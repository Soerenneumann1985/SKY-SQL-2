# SKY SQL

[![CI](https://github.com/soerenneumann1985/sky-sql-2/actions/workflows/ci.yml/badge.svg)](https://github.com/soerenneumann1985/sky-sql-2/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%E2%80%93%203.13-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A web app (with a CLI alternative and a JSON API) for exploring a US
flight-delay dataset stored in SQLite. Look up a specific flight, list all
flights on a given date, or find the most delayed flights for an airline or an
origin airport — and export any result set to CSV.

## Features

- **Flight by ID** — look up a single flight's details.
- **Flights by date** — list all flights on a given day.
- **Delayed flights by airline** — the 10 most-delayed flights (≥ 20 min) for a given airline, with airline autocomplete.
- **Delayed flights by origin airport** — the 10 most-delayed flights (≥ 20 min) departing from a given IATA airport code, with airport autocomplete.
- **CSV export** — download any result set as a `.csv` file.
- **JSON API** — every search is also available as JSON.
- **Modern UI** — responsive layout, automatic dark mode, accessible markup (skip link, ARIA labels, keyboard focus styles).

## Project structure

```
SKY-SQL-2/
├── src/sky_sql/
│   ├── __main__.py       # `sky-sql` command (web / cli)
│   ├── web.py            # Flask app factory, routes, CSV export, JSON API
│   ├── cli.py            # Interactive command-line menu
│   ├── repository.py     # Typed database access layer (SQLAlchemy)
│   ├── templates/        # Jinja templates
│   └── static/style.css
├── tests/                # pytest suite (runs against a small fixture DB)
├── data/flights.sqlite3  # Flight dataset (SQLite)
├── .github/workflows/    # CI: ruff + pytest on Python 3.10–3.13
└── pyproject.toml        # Packaging, dependencies, ruff & pytest config
```

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows

pip install -e ".[dev]"
```

Or with [uv](https://docs.astral.sh/uv/): `uv venv && uv pip install -e ".[dev]"`.

## Usage

### Web app

```bash
sky-sql web               # or: python -m sky_sql web
sky-sql web --port 8000 --debug
```

Then open **http://127.0.0.1:5000**.

### CLI

```bash
sky-sql cli
```

```
Menu:
1. Show flight by ID
2. Show flights by date
3. Delayed flights by airline
4. Delayed flights by origin airport
5. Exit
```

Pick an option, follow the prompts, and choose `y` to export the results to CSV.

### JSON API

| Endpoint                                  | Description                      |
| ----------------------------------------- | -------------------------------- |
| `GET /api/search/flight?id=280`           | Single flight by ID              |
| `GET /api/search/date?date=2015-01-01`    | All flights on a date            |
| `GET /api/search/airline?airline=Virgin`  | Top delayed flights for airline  |
| `GET /api/search/airport?airport=LAX`     | Top delayed flights from airport |
| `GET /api/airlines`                       | List of airline names            |
| `GET /healthz`                            | Health check                     |

```json
{"count": 1, "results": [{"flight_id": 280, "airline": "...", "origin": "LAX", "destination": "JFK", "delay": 42}]}
```

Invalid parameters return HTTP 400 with `{"error": "..."}`.

### Configuration

| Environment variable   | Default                          | Purpose                          |
| ---------------------- | -------------------------------- | -------------------------------- |
| `SKY_SQL_DATABASE_URL` | `sqlite:///<repo>/data/flights.sqlite3` | SQLAlchemy URL of the dataset |
| `SECRET_KEY`           | random per process               | Flask session / flash signing    |

## Development

```bash
pytest                     # run the test suite
pytest --cov=sky_sql       # with coverage
ruff check . && ruff format .
pre-commit install         # optional: lint on every commit
```

## Data

The dataset (`data/flights.sqlite3`) contains three tables:

- `flights` — one row per flight (date, origin/destination airport, airline, departure delay in minutes, ...).
- `airlines` — airline ID to airline name lookup.
- `airports` — IATA code, name and city of each airport.

## Tech stack

- Python 3.10+
- [Flask](https://flask.palletsprojects.com/) for the web app
- [SQLAlchemy 2](https://www.sqlalchemy.org/) for database access
- SQLite as the data store
- [pytest](https://pytest.org/) and [Ruff](https://docs.astral.sh/ruff/) for testing and linting
