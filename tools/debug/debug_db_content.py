
import sqlite3
import os

db_path = "reports/campaign_data.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- Runs Table ---")
cursor.execute("SELECT * FROM runs")
for r in cursor.fetchall():
    print(dict(r))

print("\n--- Factions Table Count ---")
cursor.execute("SELECT count(*) FROM factions")
print(cursor.fetchone()[0])

print("\n--- Events Table Count ---")
cursor.execute("SELECT count(*) FROM events")
print(cursor.fetchone()[0])

conn.close()
