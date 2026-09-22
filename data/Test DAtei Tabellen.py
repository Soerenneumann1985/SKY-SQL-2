import sqlite3

db_path = r"C:\Users\soere\PycharmProjects\SKY SQL 2\data\flights.sqlite3"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

print("Tabellen in der Datenbank:")
for t in tables:
    print("-", t[0])

conn.close()


import sqlite3

db_path = "flights.sqlite3"

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT * FROM flights WHERE ID = 280")
row = cur.fetchone()

print("Ergebnis für ID 280:", row)

conn.close()
