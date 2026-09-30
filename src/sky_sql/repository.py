"""Database access layer for the flight dataset."""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import astuple, dataclass, fields
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, text

# The dataset ships with the repository in <project root>/data/flights.sqlite3.
# It can be overridden with the SKY_SQL_DATABASE_URL environment variable.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data' / 'flights.sqlite3'}"

DATASET_YEAR = 2015
MIN_DELAY_MINUTES = 20
DELAYED_LIMIT = 10

# Every query returns the same projection, so results can be mapped onto `Flight`.
_SELECT_FLIGHT = """
SELECT flights.ID                              AS flight_id,
       airlines.AIRLINE                        AS airline,
       flights.ORIGIN_AIRPORT                  AS origin,
       flights.DESTINATION_AIRPORT             AS destination,
       COALESCE(flights.DEPARTURE_DELAY, 0)    AS delay
FROM flights
JOIN airlines ON flights.AIRLINE = airlines.ID
"""

_DELAYED_FILTER = f"""
  AND flights.DEPARTURE_DELAY >= {MIN_DELAY_MINUTES}
ORDER BY flights.DEPARTURE_DELAY DESC
LIMIT {DELAYED_LIMIT}
"""

QUERY_FLIGHT_BY_ID = _SELECT_FLIGHT + "WHERE flights.ID = :id"

QUERY_FLIGHTS_BY_DATE = (
    _SELECT_FLIGHT
    + "WHERE flights.DAY = :day AND flights.MONTH = :month AND flights.YEAR = :year "
    + "ORDER BY flights.ID"
)

QUERY_DELAYED_BY_AIRLINE = _SELECT_FLIGHT + "WHERE airlines.AIRLINE LIKE :airline" + _DELAYED_FILTER

QUERY_DELAYED_BY_AIRPORT = (
    _SELECT_FLIGHT + "WHERE flights.ORIGIN_AIRPORT = :origin" + _DELAYED_FILTER
)

QUERY_ALL_AIRLINES = "SELECT AIRLINE FROM airlines ORDER BY AIRLINE"

QUERY_ALL_AIRPORTS = "SELECT IATA_CODE, AIRPORT, CITY FROM airports ORDER BY IATA_CODE"


@dataclass(frozen=True, slots=True)
class Flight:
    """A single flight as shown in the UI, the CLI and CSV exports."""

    flight_id: int
    airline: str
    origin: str
    destination: str
    delay: int

    @property
    def is_delayed(self) -> bool:
        return self.delay > 0

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Flight:
        return cls(
            flight_id=int(row["flight_id"]),
            airline=row["airline"],
            origin=row["origin"],
            destination=row["destination"],
            delay=int(row["delay"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}

    def to_row(self) -> tuple[Any, ...]:
        return astuple(self)


CSV_HEADER = ("FLIGHT_ID", "AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT", "DELAY")


@dataclass(frozen=True, slots=True)
class Airport:
    code: str
    name: str
    city: str


def database_url_from_env() -> str:
    return os.environ.get("SKY_SQL_DATABASE_URL", DEFAULT_DATABASE_URL)


class FlightRepository:
    """Read-only queries against the flight database.

    Database errors are not swallowed; they propagate as
    ``sqlalchemy.exc.SQLAlchemyError`` so callers can report them properly.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @classmethod
    def from_url(cls, url: str | None = None) -> FlightRepository:
        return cls(create_engine(url or database_url_from_env()))

    def _fetch(self, query: str, params: Mapping[str, Any] | None = None) -> list[Any]:
        with self._engine.connect() as conn:
            return list(conn.execute(text(query), dict(params or {})).mappings())

    def _fetch_flights(self, query: str, params: Mapping[str, Any]) -> list[Flight]:
        return [Flight.from_row(row) for row in self._fetch(query, params)]

    def get_flight_by_id(self, flight_id: int) -> list[Flight]:
        return self._fetch_flights(QUERY_FLIGHT_BY_ID, {"id": flight_id})

    def get_flights_by_date(self, day: int, month: int, year: int) -> list[Flight]:
        # YEAR and MONTH are stored as TEXT in the dataset, so compare as strings.
        params = {"day": str(day), "month": str(month), "year": str(year)}
        return self._fetch_flights(QUERY_FLIGHTS_BY_DATE, params)

    def get_delayed_flights_by_airline(self, airline_name: str) -> list[Flight]:
        return self._fetch_flights(QUERY_DELAYED_BY_AIRLINE, {"airline": f"%{airline_name}%"})

    def get_delayed_flights_by_airport(self, origin_airport: str) -> list[Flight]:
        return self._fetch_flights(QUERY_DELAYED_BY_AIRPORT, {"origin": origin_airport.upper()})

    def get_all_airlines(self) -> list[str]:
        return [row["AIRLINE"] for row in self._fetch(QUERY_ALL_AIRLINES)]

    def get_all_airports(self) -> list[Airport]:
        return [
            Airport(code=row["IATA_CODE"], name=row["AIRPORT"], city=row["CITY"])
            for row in self._fetch(QUERY_ALL_AIRPORTS)
        ]


def is_valid_iata_code(code: str) -> bool:
    return len(code) == 3 and code.isascii() and code.isalpha()


def flights_to_csv_rows(flights: Iterable[Flight]) -> list[tuple[Any, ...]]:
    return [CSV_HEADER, *(flight.to_row() for flight in flights)]
