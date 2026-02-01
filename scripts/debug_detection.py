import sqlite3
import os

DB_PATH = "reports/db/index.db"

def test_detection():
    print(f"Testing detection on: {os.path.abspath(DB_PATH)}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Check Runs Table
        print("Checking 'runs' table...")
        try:
            cursor.execute("SELECT universe, run_id FROM runs ORDER BY started_at DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                print(f"FAILED: Found in runs (unexpected): {row}")
            else:
                print("OK: Runs table empty as expected.")
        except Exception as e:
            print(f"Error checking runs: {e}")

        # 2. Check Events Table Fallback
        print("Checking 'events' table fallback...")
        try:
            cursor.execute("PRAGMA table_info(events)")
            columns = [c[1] for c in cursor.fetchall()]
            print(f"Events columns: {columns}")
            
            cursor.execute("SELECT universe, run_id FROM events ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                print(f"SUCCESS: Found in events: {row}")
            else:
                print("FAILED: No events found.")
                
            # Double check count
            cursor.execute("SELECT count(*) FROM events")
            print(f"Total events: {cursor.fetchone()[0]}")
            
        except Exception as e:
            print(f"Error checking events: {e}")
            
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    test_detection()
