
import sqlite3
import json

DB_PATH = "reports/campaign_data.db"
RUN_ID = "run_1768172839"
UNIVERSE = "eternal_crusade"

def check():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Checking DB: {DB_PATH}")
    print(f"Target Run: {RUN_ID}")
    
    # Check 1: Does the event exist?
    cursor.execute("SELECT count(*) FROM events WHERE run_id=? AND event_type='galaxy_generated'", (RUN_ID,))
    count = cursor.fetchone()[0]
    print(f"Galaxy Map Events found: {count}")
    
    if count > 0:
        cursor.execute("SELECT universe, data_json FROM events WHERE run_id=? AND event_type='galaxy_generated'", (RUN_ID,))
        row = cursor.fetchone()
        print(f"  > Universe in DB: {row[0]}")
        try:
            data = json.loads(row[1])
            print(f"  > Systems in JSON: {len(data.get('systems', []))}")
        except:
            print("  > JSON Parse Error")
            
    conn.close()

if __name__ == "__main__":
    check()
