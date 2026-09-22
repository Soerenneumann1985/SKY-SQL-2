# SKY SQL

A web app (with a CLI alternative) for exploring a US flight-delay dataset
stored in SQLite. Look up a specific flight, list all flights on a given
date, or find the most delayed flights for an airline or an origin airport —
and export any result set to CSV.

## Features

- **Flight by ID** — look up a single flight's details.
- **Flights by date** — list all flights on a given day.
- **Delayed flights by airline** — the 10 most-delayed flights (≥ 20 min) for a given airline.
- **Delayed flights by origin airport** — the 10 most-delayed flights (≥ 20 min) departing from a given IATA airport code.
- **CSV export** — download any result set as a `.csv` file.

## Project structure

```
SKY-SQL-2/
├── src/
│   ├── app.py             # Flask web app (routes, forms, CSV export)
│   ├── main.py             # CLI entry point and menu
│   ├── flights_data.py     # Database access layer (SQLAlchemy)
│   ├── templates/          # Jinja templates for the web app
│   └── static/
│       └── style.css
├── data/
│   └── flights.sqlite3     # Flight dataset (SQLite)
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

### Web app

Run from the project root:

```bash
python src/app.py
```

Then open **http://127.0.0.1:5000** in your browser. From the start page you
can search flights by ID, by date, by airline, or by origin airport, and
export any result table to CSV via the "CSV exportieren" button.

### CLI

Alternatively, run the original command-line version:

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
- [Flask](https://flask.palletsprojects.com/) for the web app
- [SQLAlchemy](https://www.sqlalchemy.org/) for database access
- SQLite as the data store
