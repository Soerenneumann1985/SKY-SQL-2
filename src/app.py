import csv
import io
import os
from datetime import datetime

from flask import Flask, Response, flash, redirect, render_template, request, url_for

import flights_data

IATA_LENGTH = 3

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/flight")
def flight_by_id():
    flight_id = request.args.get("id", "").strip()
    results = None
    if flight_id:
        try:
            results = flights_data.get_flight_by_id(int(flight_id))
            if not results:
                flash(f"Keine Flugdaten für ID {flight_id} gefunden.")
        except ValueError:
            flash("Bitte eine gültige numerische Flug-ID eingeben.")
    return render_template("flight_by_id.html", results=results, flight_id=flight_id)


DATASET_YEAR = 2015


@app.route("/by-date")
def flights_by_date():
    date_str = request.args.get("date", "").strip()
    display_date = date_str or f"{DATASET_YEAR}-01-01"
    results = None
    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            results = flights_data.get_flights_by_date(date.day, date.month, date.year)
            if not results:
                flash(f"Keine Flüge am {date_str} gefunden.")
        except ValueError:
            flash("Bitte ein gültiges Datum eingeben.")
    return render_template(
        "flights_by_date.html", results=results, date=display_date, dataset_year=DATASET_YEAR
    )


@app.route("/delayed/airline")
def delayed_by_airline():
    airline = request.args.get("airline", "").strip()
    results = None
    if airline:
        results = flights_data.get_delayed_flights_by_airline(airline)
        if not results:
            flash(f"Keine verspäteten Flüge für „{airline}“ gefunden.")
    return render_template("delayed_by_airline.html", results=results, airline=airline)


@app.route("/delayed/airport")
def delayed_by_airport():
    airport = request.args.get("airport", "").strip().upper()
    results = None
    if airport:
        if airport.isalpha() and len(airport) == IATA_LENGTH:
            results = flights_data.get_delayed_flights_by_airport(airport)
            if not results:
                flash(f"Keine verspäteten Flüge ab „{airport}“ gefunden.")
        else:
            flash("Bitte einen gültigen 3-stelligen IATA-Flughafencode eingeben.")
    return render_template("delayed_by_airport.html", results=results, airport=airport)


def _fetch_export_results(kind):
    if kind == "flight":
        return flights_data.get_flight_by_id(int(request.args["id"]))
    if kind == "date":
        date = datetime.strptime(request.args["date"], "%Y-%m-%d")
        return flights_data.get_flights_by_date(date.day, date.month, date.year)
    if kind == "airline":
        return flights_data.get_delayed_flights_by_airline(request.args["airline"])
    if kind == "airport":
        return flights_data.get_delayed_flights_by_airport(request.args["airport"].upper())
    return None


@app.route("/export")
def export_csv():
    kind = request.args.get("kind")
    try:
        results = _fetch_export_results(kind)
    except (KeyError, ValueError):
        results = None

    if results is None:
        flash("Ungültige Export-Anfrage.")
        return redirect(url_for("index"))

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["FLIGHT_ID", "AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT", "DELAY"])
    for row in results:
        writer.writerow([
            row["FLIGHT_ID"],
            row["AIRLINE"],
            row["ORIGIN_AIRPORT"],
            row["DESTINATION_AIRPORT"],
            row["DELAY"] or 0,
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={kind}_export.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True)
