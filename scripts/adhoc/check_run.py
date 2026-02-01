
import sqlite3
import os

db_path = '/app/reports/campaign_data.db'
run_id = 'run_1768247475'
universe = 'eternal_crusade'

# 1. Check DB State
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        # Check Runs Table
        cursor = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,))
        run_row = cursor.fetchone()
        print(f"DB Metadata for {run_id}: {run_row}")
        
        # Check Events Table
        cursor = conn.execute("SELECT count(*) FROM events WHERE run_id=?", (run_id,))
        event_count = cursor.fetchone()[0]
        print(f"DB Event Count for {run_id}: {event_count}")
        
    except Exception as e:
        print(f"DB Error: {e}")
else:
    print("DB file not found.")

# 2. Find File System Location
base_dir = f"/app/reports/{universe}"
found_path = None

if os.path.exists(base_dir):
    batches = sorted(os.listdir(base_dir), reverse=True)
    for b in batches:
        b_path = os.path.join(base_dir, b)
        if not os.path.isdir(b_path): continue
        
        possible_run = os.path.join(b_path, run_id)
        if os.path.exists(possible_run):
            print(f"Found Run Directory: {possible_run}")
            found_path = possible_run
            
            # Check contents
            files = os.listdir(possible_run)
            print(f"Files in run dir: {files}")
            
            # Check campaign.json properties
            c_path = os.path.join(possible_run, 'campaign.json')
            if os.path.exists(c_path):
                print(f"campaign.json size: {os.path.getsize(c_path)} bytes")
            break

if not found_path:
    print(f"Run directory for {run_id} NOT found in {base_dir}")
