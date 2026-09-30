"""Flask web app: search forms, CSV export and a small JSON API."""

from __future__ import annotations

import csv
import io
import logging
import os
import secrets
from collections.abc import Callable
from datetime import date, datetime
from functools import cache
from typing import Any

from flask import (
    Flask,
    Response,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError

from sky_sql.repository import (
    DATASET_YEAR,
    DELAYED_LIMIT,
    MIN_DELAY_MINUTES,
    Flight,
    FlightRepository,
    flights_to_csv_rows,
    is_valid_iata_code,
)

log = logging.getLogger(__name__)


class InvalidQuery(ValueError):
    """Raised when search parameters are missing or malformed."""


# --------------------------------------------------------------------------
# Search definitions — shared by the HTML pages, the CSV export and the API.
# Each search validates its own query parameters and runs the matching query.
# --------------------------------------------------------------------------


def _search_flight(repo: FlightRepository, args: dict[str, str]) -> list[Flight]:
    try:
        flight_id = int(args.get("id", ""))
    except ValueError:
        raise InvalidQuery("Bitte eine gültige numerische Flug-ID eingeben.") from None
    if flight_id < 1:
        raise InvalidQuery("Bitte eine gültige numerische Flug-ID eingeben.")
    return repo.get_flight_by_id(flight_id)


def _search_date(repo: FlightRepository, args: dict[str, str]) -> list[Flight]:
    try:
        day = datetime.strptime(args.get("date", ""), "%Y-%m-%d").date()
    except ValueError:
        raise InvalidQuery("Bitte ein gültiges Datum eingeben.") from None
    return repo.get_flights_by_date(day.day, day.month, day.year)


def _search_airline(repo: FlightRepository, args: dict[str, str]) -> list[Flight]:
    airline = args.get("airline", "")
    if not airline:
        raise InvalidQuery("Bitte einen Airline-Namen eingeben.")
    return repo.get_delayed_flights_by_airline(airline)


def _search_airport(repo: FlightRepository, args: dict[str, str]) -> list[Flight]:
    airport = args.get("airport", "").upper()
    if not is_valid_iata_code(airport):
        raise InvalidQuery("Bitte einen gültigen 3-stelligen IATA-Flughafencode eingeben.")
    return repo.get_delayed_flights_by_airport(airport)


SEARCHES: dict[str, Callable[[FlightRepository, dict[str, str]], list[Flight]]] = {
    "flight": _search_flight,
    "date": _search_date,
    "airline": _search_airline,
    "airport": _search_airport,
}


def _clean_args() -> dict[str, str]:
    return {key: value.strip() for key, value in request.args.items()}


def _repo() -> FlightRepository:
    return current_app.extensions["sky_sql.repository"]


def _run_search(kind: str, args: dict[str, str]) -> list[Flight]:
    return SEARCHES[kind](_repo(), args)


def _search_page(template: str, kind: str, param: str, empty_message: str, **context: Any) -> str:
    """Render a search page; run the search only when its parameter is given."""
    args = _clean_args()
    results: list[Flight] | None = None
    if args.get(param):
        try:
            results = _run_search(kind, args)
        except InvalidQuery as exc:
            flash(str(exc), "error")
        else:
            if not results:
                flash(empty_message.format(value=args[param]), "info")
    return render_template(
        template,
        results=results,
        kind=kind,
        query=args.get(param, ""),
        export_params={param: args.get(param, "")},
        **context,
    )


def _csv_response(flights: list[Flight], filename: str) -> Response:
    buffer = io.StringIO()
    csv.writer(buffer).writerows(flights_to_csv_rows(flights))
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def create_app(
    repository: FlightRepository | None = None, config: dict[str, Any] | None = None
) -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    app.json.sort_keys = False  # keep Flight field order in API responses
    if config:
        app.config.update(config)

    app.extensions["sky_sql.repository"] = repository or FlightRepository.from_url()

    @cache
    def airlines() -> list[str]:
        return _repo().get_all_airlines()

    @cache
    def airports() -> list[Any]:
        return _repo().get_all_airports()

    @app.context_processor
    def inject_globals() -> dict[str, Any]:
        return {
            "dataset_year": DATASET_YEAR,
            "min_delay": MIN_DELAY_MINUTES,
            "delayed_limit": DELAYED_LIMIT,
        }

    # ---------------------------------------------------------------- pages

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/flight")
    def flight_by_id() -> str:
        return _search_page(
            "flight_by_id.html", "flight", "id", "Keine Flugdaten für ID {value} gefunden."
        )

    @app.get("/by-date")
    def flights_by_date() -> str:
        return _search_page(
            "flights_by_date.html",
            "date",
            "date",
            "Keine Flüge am {value} gefunden.",
            default_date=date(DATASET_YEAR, 1, 1).isoformat(),
        )

    @app.get("/delayed/airline")
    def delayed_by_airline() -> str:
        return _search_page(
            "delayed_by_airline.html",
            "airline",
            "airline",
            "Keine verspäteten Flüge für „{value}“ gefunden.",
            airlines=airlines(),
        )

    @app.get("/delayed/airport")
    def delayed_by_airport() -> str:
        return _search_page(
            "delayed_by_airport.html",
            "airport",
            "airport",
            "Keine verspäteten Flüge ab „{value}“ gefunden.",
            airports=airports(),
        )

    @app.get("/export")
    def export_csv() -> Response:
        kind = request.args.get("kind", "")
        if kind not in SEARCHES:
            flash("Ungültige Export-Anfrage.", "error")
            return redirect(url_for("index"))
        try:
            flights = _run_search(kind, _clean_args())
        except InvalidQuery as exc:
            flash(str(exc), "error")
            return redirect(url_for("index"))
        return _csv_response(flights, f"{kind}_export.csv")

    # ------------------------------------------------------------------ API

    @app.get("/api/search/<kind>")
    def api_search(kind: str) -> Response:
        if kind not in SEARCHES:
            abort(404)
        try:
            flights = _run_search(kind, _clean_args())
        except InvalidQuery as exc:
            return jsonify(error=str(exc)), 400
        return jsonify(count=len(flights), results=[f.to_dict() for f in flights])

    @app.get("/api/airlines")
    def api_airlines() -> Response:
        return jsonify(airlines())

    @app.get("/healthz")
    def healthz() -> Response:
        return jsonify(status="ok")

    # --------------------------------------------------------------- errors

    @app.errorhandler(SQLAlchemyError)
    def database_error(exc: SQLAlchemyError) -> tuple[Any, int]:
        log.exception("Database error", exc_info=exc)
        if request.path.startswith("/api/"):
            return jsonify(error="Datenbankfehler"), 503
        return render_template("error.html", message="Die Datenbank ist nicht erreichbar."), 503

    @app.errorhandler(404)
    def not_found(_exc: Exception) -> tuple[Any, int]:
        if request.path.startswith("/api/"):
            return jsonify(error="Nicht gefunden"), 404
        return render_template("error.html", message="Diese Seite gibt es nicht."), 404

    return app


def run(host: str = "127.0.0.1", port: int = 5000, debug: bool = False) -> None:
    create_app().run(host=host, port=port, debug=debug)
