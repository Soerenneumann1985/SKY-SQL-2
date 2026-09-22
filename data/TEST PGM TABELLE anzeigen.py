from sqlalchemy import create_engine, text

DATABASE_URL = "sqlite:///flights.sqlite3"
engine = create_engine(DATABASE_URL)

def show_columns(table_name):
    query = f"PRAGMA table_info({table_name});"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
        for row in rows:
            row_dict = dict(row._mapping)
            print(row_dict)


def count_query(query, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        print(result.scalar())


def show_rows(query, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        rows = result.fetchall()
        print(f"{len(rows)} Zeile(n):")
        for row in rows:
            print(dict(row._mapping))


if __name__ == "__main__":
    query = (
        "SELECT COUNT(*) FROM flights "
        "JOIN airlines ON flights.AIRLINE = airlines.id "
        "WHERE flights.DAY = :day AND flights.MONTH = :month AND flights.YEAR = :year"
    )
    params = {"day": "16", "month": "3", "year": "2015"}
    count_query(query, params)

