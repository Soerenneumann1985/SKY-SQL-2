from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from sky_sql.repository import FlightRepository
from sky_sql.web import create_app

SCHEMA = """
CREATE TABLE airlines (ID INTEGER PRIMARY KEY, AIRLINE TEXT);
CREATE TABLE airports (
    IATA_CODE TEXT PRIMARY KEY, AIRPORT TEXT, CITY TEXT, STATE TEXT,
    COUNTRY TEXT, LATITUDE TEXT, LONGITUDE TEXT
);
CREATE TABLE flights (
    ID INTEGER PRIMARY KEY AUTOINCREMENT, YEAR TEXT, MONTH TEXT, DAY NUMERIC,
    AIRLINE INTEGER, ORIGIN_AIRPORT TEXT, DESTINATION_AIRPORT TEXT, DEPARTURE_DELAY INTEGER
);
"""

AIRLINES = [(1, "Virgin America"), (2, "Delta Air Lines Inc.")]
AIRPORTS = [
    ("LAX", "Los Angeles International Airport", "Los Angeles", "CA", "USA", "0", "0"),
    ("SFO", "San Francisco International Airport", "San Francisco", "CA", "USA", "0", "0"),
]
FLIGHTS = [
    # ID, YEAR, MONTH, DAY, AIRLINE, ORIGIN, DEST, DELAY
    (1, "2015", "1", 1, 1, "LAX", "SFO", 45),
    (2, "2015", "1", 1, 2, "SFO", "LAX", -3),
    (3, "2015", "1", 2, 1, "LAX", "JFK", None),
    (4, "2015", "1", 2, 1, "SFO", "JFK", 120),
    (5, "2015", "1", 3, 2, "LAX", "ATL", 19),
]


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "flights.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO airlines VALUES (?, ?)", AIRLINES)
        conn.executemany("INSERT INTO airports VALUES (?, ?, ?, ?, ?, ?, ?)", AIRPORTS)
        conn.executemany("INSERT INTO flights VALUES (?, ?, ?, ?, ?, ?, ?, ?)", FLIGHTS)
    return path


@pytest.fixture
def repo(db_path: Path) -> FlightRepository:
    return FlightRepository.from_url(f"sqlite:///{db_path}")


@pytest.fixture
def client(repo: FlightRepository):
    app = create_app(repository=repo, config={"TESTING": True})
    return app.test_client()
