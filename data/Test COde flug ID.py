import sqlite3

def get_all_flight_ids():
    db_path = "flights.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = "SELECT * FROM flights JOIN airlines ON flights.AIRLINE = airlines.id ORDER BY flights.ID LIMIT 20 "
    cur.execute(query)
    rows = cur.fetchall()

    conn.close()
    return rows


def main():
    db_path = "flights.db"   # <-- hier deinen Datenbankpfad eintragen

    print("Alle Flight-IDs:")
    print("----------------")

    ids = get_all_flight_ids()

    for row in ids:
        print("ID:"+str(row["ID"]))


if __name__ == "__main__":
    main()
