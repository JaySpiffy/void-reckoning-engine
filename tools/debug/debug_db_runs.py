
import sqlite3
import os

db_path = "reports/campaign_data.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- Runs Table ---")
try:
    cursor.execute("SELECT * FROM runs")
    runs = cursor.fetchall()
    if not runs:
        print("No runs found in 'runs' table.")
    for run in runs:
        print(dict(run))
except Exception as e:
    print(f"Error querying runs: {e}")

print("\n--- Events Table (Unique Run IDs) ---")
try:
    cursor.execute("SELECT DISTINCT run_id, universe, batch_id FROM events")
    events = cursor.fetchall()
    if not events:
        print("No events found.")
    for e in events:
        print(dict(e))
except Exception as e:
    print(f"Error querying events: {e}")

conn.close()
