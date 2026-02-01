
import sqlite3
import os

db_path = '/app/reports/campaign_data.db'
run_id = 'run_1768247475'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT count(*) FROM events WHERE run_id=? AND event_type='galaxy_generated'", (run_id,))
        count = cursor.fetchone()[0]
        print(f"Galaxy Generated Events for {run_id}: {count}")
        
    except Exception as e:
        print(f"DB Error: {e}")
