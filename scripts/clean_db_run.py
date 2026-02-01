
import sqlite3
import os

DB_PATH = "reports/campaign_data.db"

def clean_run(run_id):
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Check if run exists
    cursor = conn.cursor()
    cursor.execute("SELECT batch_id FROM runs WHERE run_id = ?", (run_id,))
    row = cursor.fetchone()
    
    if row:
        print(f"Deleting run {run_id} from database...")
        # Manually cascade delete
        cursor.execute("DELETE FROM resource_transactions WHERE run_id = ?", (run_id,))
        cursor.execute("DELETE FROM factions WHERE run_id = ?", (run_id,))
        cursor.execute("DELETE FROM events WHERE run_id = ?", (run_id,))
        cursor.execute("DELETE FROM battle_performance WHERE run_id = ?", (run_id,))
        cursor.execute("DELETE FROM battles WHERE run_id = ?", (run_id,))
        
        # Finally delete run
        cursor.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
        conn.commit()
        print("Run and all related data deleted successfully.")
    else:
        print(f"Run {run_id} not found in database.")

    conn.close()

if __name__ == "__main__":
    # Configuration
    RUN_ID = "run_1768696819"
    clean_run(RUN_ID)
