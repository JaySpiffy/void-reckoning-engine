import sqlite3
import os

db_path = "/app/reports/campaign_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT run_id FROM runs ORDER BY run_id DESC LIMIT 1")
row = cursor.fetchone()
if not row:
    # Fallback to events if runs table is empty/weird
    cursor.execute("SELECT run_id FROM events ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
        
    if not row:
        print("No runs found.")
        conn.close()
        exit()

run_id = row[0]
print(f"Latest Run: {run_id}")

# Get Max Turn
cursor.execute("SELECT MAX(turn) FROM events WHERE run_id = ?", (run_id,))
max_turn = cursor.fetchone()[0]
print(f"Max Turn in DB: {max_turn}")

# Check Tech Progress Error context (optional, but good to know if tech events exist)
cursor.execute("SELECT COUNT(*) FROM events WHERE run_id = ? AND event_type = 'tech_researched'", (run_id,))
tech_count = cursor.fetchone()[0]
print(f"Tech Events: {tech_count}")

# Close the connection when done
conn.close()
