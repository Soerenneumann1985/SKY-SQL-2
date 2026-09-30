from __future__ import annotations

import pytest

from sky_sql.repository import CSV_HEADER, Flight, flights_to_csv_rows, is_valid_iata_code


def test_flight_by_id(repo):
    assert repo.get_flight_by_id(1) == [Flight(1, "Virgin America", "LAX", "SFO", 45)]


def test_flight_by_id_missing(repo):
    assert repo.get_flight_by_id(999) == []


def test_null_delay_becomes_zero(repo):
    (flight,) = repo.get_flight_by_id(3)
    assert flight.delay == 0
    assert not flight.is_delayed


def test_flights_by_date(repo):
    assert [f.flight_id for f in repo.get_flights_by_date(1, 1, 2015)] == [1, 2]
    assert repo.get_flights_by_date(1, 1, 2016) == []


def test_delayed_by_airline_filters_and_sorts(repo):
    flights = repo.get_delayed_flights_by_airline("virgin")
    assert [f.flight_id for f in flights] == [4, 1]


def test_delayed_by_airport_is_case_insensitive(repo):
    assert [f.flight_id for f in repo.get_delayed_flights_by_airport("lax")] == [1]


def test_lookup_lists(repo):
    assert repo.get_all_airlines() == ["Delta Air Lines Inc.", "Virgin America"]
    assert [a.code for a in repo.get_all_airports()] == ["LAX", "SFO"]


@pytest.mark.parametrize(
    ("code", "valid"),
    [("LAX", True), ("lax", True), ("LA", False), ("LAXX", False), ("L4X", False), ("ÄÖÜ", False)],
)
def test_is_valid_iata_code(code, valid):
    assert is_valid_iata_code(code) is valid


def test_csv_rows():
    rows = flights_to_csv_rows([Flight(1, "X", "A", "B", 5)])
    assert rows == [CSV_HEADER, (1, "X", "A", "B", 5)]
