from sqlalchemy import create_engine, text
import json


import os
print("Arbeitsverzeichnis:", os.getcwd())
print("Existiert die DB-Datei?", os.path.exists("data/flights.sqlite3"))


QUERY_FLIGHT_BY_ID = ("SELECT flights.*, airlines.airline as AIRLINE, flights.ID as FLIGHT_ID, "
                      "flights.DEPARTURE_DELAY as DELAY "
                      "FROM flights "
                      "JOIN airlines ON flights.AIRLINE = airlines.id "
                      "WHERE flights.ID = :id")


QUERY_ALL_AIRLINES = """
SELECT ID, AIRLINE
FROM airlines
ORDER BY AIRLINE ASC
"""

# Define the database URL
DATABASE_URL = "sqlite:///data/flights.sqlite3"

# Create the engine
engine = create_engine(DATABASE_URL)


def execute_query(query, params):
    """
    Execute an SQL query with the params provided in a dictionary,
    and returns a list of records (dictionary-like objects).
    If an exception was raised, print the error, and return an empty list.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.mappings().all()
            return rows
            
    except Exception as e:
        print("Query error:", e)
        return []


def get_flight_by_id(flight_id):
    """
    Searches for flight details using flight ID.
    If the flight was found, returns a list with a single record.
    """
    params = {'id': flight_id}
    return execute_query(QUERY_FLIGHT_BY_ID, params)


def get_flights_by_date(day, month, year):
    query = (
        "SELECT flights.ID, flights.ID as FLIGHT_ID, "
        "flights.ORIGIN_AIRPORT, flights.DESTINATION_AIRPORT, "
        "airlines.airline as AIRLINE, flights.DEPARTURE_DELAY as DELAY "
        "FROM flights "
        "JOIN airlines ON flights.AIRLINE = airlines.id "
        "WHERE flights.DAY = :day AND flights.MONTH = :month AND flights.YEAR = :year"
    )
    params = {"day": str(day), "month": str(month), "year": str(year)}
    print("Eingabe params:", params)          # <-- neu
    rows = execute_query(query, params)
    print("Anzahl Ergebnisse:", len(rows))   # <-- neu
    return rows



def get_all_airlines():
    return execute_query(QUERY_ALL_AIRLINES, {})



def get_delayed_flights_by_airline(airline_name):
    query = """
    SELECT flights.ID AS FLIGHT_ID,
            airlines.AIRLINE,
            flights.ORIGIN_AIRPORT,
            flights.DEPARTURE_DELAY as DELAY,
            flights.DESTINATION_AIRPORT
    FROM flights 
    JOIN airlines ON flights.AIRLINE = airlines.ID
    WHERE airlines.AIRLINE LIKE :airline
        AND flights.DEPARTURE_DELAY IS NOT NULL
        AND flights.DEPARTURE_DELAY >= 20
        ORDER BY flights.DEPARTURE_DELAY DESC LIMIT 10
        """
    params = {'airline': f"%{airline_name}%"}
    return execute_query(query, params)

def get_delayed_flights_by_airport(origin_airport):
    query = """
    SELECT flights.ID AS FLIGHT_ID,
        airlines.AIRLINE,
        flights.ORIGIN_AIRPORT,
        flights.DESTINATION_AIRPORT,
        flights.DEPARTURE_DELAY as DELAY
    FROM flights 
    JOIN airlines ON flights.AIRLINE = airlines.ID
    WHERE flights.ORIGIN_AIRPORT = :origin
        AND flights.DEPARTURE_DELAY IS NOT NULL
        AND flights.DEPARTURE_DELAY >= 20
    ORDER BY flights.DEPARTURE_DELAY DESC LIMIT 10
    """
    params = {"origin": origin_airport}
    return execute_query(query, params)


if __name__ == "__main__":
    results = get_delayed_flights_by_airline("Virgin")

    if results:
        for row in results:
            print(json.dumps(dict(row), indent=4))
    else:
        print("No delayed flights found for this airline")









    