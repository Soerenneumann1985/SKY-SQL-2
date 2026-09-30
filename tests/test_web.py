from __future__ import annotations

import csv
import io

import pytest
from sqlalchemy.exc import OperationalError


@pytest.mark.parametrize(
    "path", ["/", "/flight", "/by-date", "/delayed/airline", "/delayed/airport"]
)
def test_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "SKY SQL" in response.text


def test_flight_search(client):
    response = client.get("/flight?id=1")
    assert "Virgin America" in response.text
    assert "+45 min" in response.text


def test_flight_search_invalid_id(client):
    response = client.get("/flight?id=abc")
    assert "gültige numerische Flug-ID" in response.text


def test_flight_search_not_found(client):
    assert "Keine Flugdaten für ID 999" in client.get("/flight?id=999").text


def test_date_search(client):
    response = client.get("/by-date?date=2015-01-01")
    assert "2 Ergebnisse" in response.text


def test_date_search_invalid(client):
    assert "gültiges Datum" in client.get("/by-date?date=nope").text


def test_airline_page_offers_autocomplete(client):
    assert '<option value="Virgin America">' in client.get("/delayed/airline").text


def test_airport_search_invalid_code(client):
    assert "IATA-Flughafencode eingeben" in client.get("/delayed/airport?airport=LA1").text


def test_active_nav_link(client):
    assert 'aria-current="page"' in client.get("/by-date").text


def test_csv_export(client):
    response = client.get("/export?kind=airline&airline=Virgin")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert 'filename="airline_export.csv"' in response.headers["Content-Disposition"]
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == ["FLIGHT_ID", "AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT", "DELAY"]
    assert [row[0] for row in rows[1:]] == ["4", "1"]


@pytest.mark.parametrize("query", ["kind=bogus", "kind=flight&id=x", "kind=date"])
def test_csv_export_invalid_redirects(client, query):
    response = client.get(f"/export?{query}")
    assert response.status_code == 302


def test_api_search(client):
    data = client.get("/api/search/airport?airport=sfo").get_json()
    assert data == {
        "count": 1,
        "results": [
            {
                "flight_id": 4,
                "airline": "Virgin America",
                "origin": "SFO",
                "destination": "JFK",
                "delay": 120,
            },
        ],
    }


def test_api_search_bad_request(client):
    response = client.get("/api/search/flight?id=zero")
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_api_unknown_search(client):
    assert client.get("/api/search/nope").status_code == 404


def test_api_airlines(client):
    assert client.get("/api/airlines").get_json() == ["Delta Air Lines Inc.", "Virgin America"]


def test_healthz(client):
    assert client.get("/healthz").get_json() == {"status": "ok"}


def test_database_error_page(client, repo, monkeypatch):
    def boom(*_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("disk on fire"))

    monkeypatch.setattr(repo, "get_flight_by_id", boom)
    response = client.get("/flight?id=1")
    assert response.status_code == 503
    assert "Datenbank ist nicht erreichbar" in response.text
