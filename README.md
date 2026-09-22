# SKY SQL

A command-line tool for exploring a US flight-delay dataset stored in SQLite.
Look up a specific flight, list all flights on a given date, or find the most
delayed flights for an airline or an origin airport — and optionally export
the results to CSV.

## Features

- **Flight by ID** — look up a single flight's details.
- **Flights by date** — list all flights on a given day.
- **Delayed flights by airline** — the 10 most-delayed flights (≥ 20 min) for a given airline.
- **Delayed flights by origin airport** — the 10 most-delayed flights (≥ 20 min) departing from a given IATA airport code.
- **CSV export** — save any result set to a `.csv` file.

## Project structure

```
SKY-SQL-2/
├── src/
│   ├── main.py           # CLI entry point and menu
│   └── flights_data.py   # Database access layer (SQLAlchemy)
├── data/
│   └── flights.sqlite3   # Flight dataset (SQLite)
├── requirements.txt
└── README.md
```

## Setup

Requires Python 3.9+.

```bash
python -m venv .venv
.venv\Scripts\activate      # on Windows
source .venv/bin/activate   # on macOS/Linux

pip install -r requirements.txt
```

## Usage

Run from the project root:

```bash
python src/main.py
```

You'll get a menu:

```
Menu:
1. Show flight by ID
2. Show flights by date
3. Delayed flights by airline
4. Delayed flights by origin airport
5. Exit
```

Pick an option, follow the prompts, and choose `y` when asked whether to
export the results to CSV.

## Data

The dataset (`data/flights.sqlite3`) contains two tables:

- `flights` — one row per flight (date, origin/destination airport, airline, departure delay in minutes, ...).
- `airlines` — airline ID to airline name lookup.

## Tech stack

- Python
- [SQLAlchemy](https://www.sqlalchemy.org/) for database access
- SQLite as the data store
