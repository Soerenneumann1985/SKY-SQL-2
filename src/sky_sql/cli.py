"""Interactive command-line interface."""

from __future__ import annotations

import csv
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TypeVar

from sqlalchemy.exc import SQLAlchemyError

from sky_sql.repository import Flight, FlightRepository, flights_to_csv_rows, is_valid_iata_code

T = TypeVar("T")


def prompt_until_valid(message: str, parse: Callable[[str], T | None]) -> T:
    """Keep asking until `parse` returns a value (it returns None or raises on bad input)."""
    while True:
        raw = input(message).strip()
        try:
            value = parse(raw)
        except ValueError as exc:
            print(f"Try again... ({exc})")
            continue
        if value is not None:
            return value
        print("Try again...")


def flight_by_id(repo: FlightRepository) -> list[Flight]:
    flight_id = prompt_until_valid("Enter flight ID: ", int)
    return repo.get_flight_by_id(flight_id)


def flights_by_date(repo: FlightRepository) -> list[Flight]:
    day = prompt_until_valid(
        "Enter date in DD/MM/YYYY format: ", lambda s: datetime.strptime(s, "%d/%m/%Y").date()
    )
    return repo.get_flights_by_date(day.day, day.month, day.year)


def delayed_flights_by_airline(repo: FlightRepository) -> list[Flight]:
    airline = prompt_until_valid("Enter airline name: ", lambda s: s or None)
    return repo.get_delayed_flights_by_airline(airline)


def delayed_flights_by_airport(repo: FlightRepository) -> list[Flight]:
    airport = prompt_until_valid(
        "Enter origin airport IATA code: ",
        lambda s: s.upper() if is_valid_iata_code(s) else None,
    )
    return repo.get_delayed_flights_by_airport(airport)


def print_results(flights: list[Flight]) -> None:
    print(f"Got {len(flights)} results.")
    for f in flights:
        line = f"{f.flight_id}. {f.origin} -> {f.destination} by {f.airline}"
        if f.is_delayed:
            line += f", Delay: {f.delay} Minutes"
        print(line)


def offer_csv_export(flights: list[Flight]) -> None:
    if not flights:
        return
    choice = input("Would you like to export this data to a CSV file? (y/n): ").strip().lower()
    if choice != "y":
        return
    filename = input("Enter filename (e.g. delayed_flights.csv): ").strip() or "flights.csv"
    path = Path(filename)
    with path.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(flights_to_csv_rows(flights))
    print(f"Data successfully exported to {path}")


MENU: dict[int, tuple[str, Callable[[FlightRepository], list[Flight]] | None]] = {
    1: ("Show flight by ID", flight_by_id),
    2: ("Show flights by date", flights_by_date),
    3: ("Delayed flights by airline", delayed_flights_by_airline),
    4: ("Delayed flights by origin airport", delayed_flights_by_airport),
    5: ("Exit", None),
}


def choose_action() -> Callable[[FlightRepository], list[Flight]] | None:
    print("\nMenu:")
    for key, (label, _) in MENU.items():
        print(f"{key}. {label}")
    choice = prompt_until_valid("> ", lambda s: int(s) if int(s) in MENU else None)
    return MENU[choice][1]


def main(repo: FlightRepository | None = None) -> int:
    repo = repo or FlightRepository.from_url()
    try:
        while (action := choose_action()) is not None:
            try:
                flights = action(repo)
            except SQLAlchemyError as exc:
                print(f"Database error: {exc}", file=sys.stderr)
                continue
            print_results(flights)
            offer_csv_export(flights)
    except (KeyboardInterrupt, EOFError):
        print()
    return 0
