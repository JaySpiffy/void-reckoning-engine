
import sqlite3
import os

db_path = '/app/reports/campaign_data.db'
conn = sqlite3.connect(db_path)
run_id = 'run_1768239493'

try:
    print(f"Deleting run {run_id}...")
    conn.execute("DELETE FROM runs WHERE run_id=?", (run_id,))
    conn.execute("DELETE FROM events WHERE run_id=?", (run_id,))
    conn.commit()
    print("Deleted.")
    
    # Verify
    cursor = conn.execute("SELECT count(*) FROM events WHERE run_id=?", (run_id,))
    print(f"Events remaining: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Error: {e}")
