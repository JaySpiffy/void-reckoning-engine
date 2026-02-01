
import sqlite3
import os
import sys
import json
import glob

# Configuration
DB_PATH = "reports/campaign_data.db"
UNIVERSE = "eternal_crusade"
DEFAULT_RUN_ID = "run_1768172839"

REQUIRED_TABLES = [
    "events",
    "factions",
    "battles",
    "resource_transactions",
    "battle_performance"
]

REQUIRED_COLUMNS = {
    "events": ["universe", "run_id", "event_type", "data_json", "timestamp", "turn"],
    "factions": ["universe", "run_id", "name", "data_json", "turn"],
    "battles": ["universe", "run_id", "location", "data_json"],
    "resource_transactions": ["universe", "run_id", "faction", "total_amount"],
    "battle_performance": ["universe", "run_id", "battle_id"] 
}

def get_latest_run():
    base_dir = os.path.join("reports", UNIVERSE)
    if not os.path.exists(base_dir): return None
    
    batch_dirs = sorted(glob.glob(os.path.join(base_dir, "batch_*")), reverse=True)
    if not batch_dirs: return None
    
    run_dirs = sorted(glob.glob(os.path.join(batch_dirs[0], "run_*")), reverse=True)
    if not run_dirs: return None
    
    return os.path.basename(run_dirs[0])

def diagnose():
    print(f"Diagnosing DB: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("ERROR: Database file not found!")
        return

    # Auto-detect run ID if possible, else default
    latest_run = get_latest_run()
    target_run = latest_run if latest_run else DEFAULT_RUN_ID
    print(f"Target Universe: {UNIVERSE}")
    print(f"Target Run ID: {target_run}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        return

    print("\n--- Table Existence & Schema Check ---")
    missing_tables = []
    
    for table in REQUIRED_TABLES:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            status = "[OK]"
            # Check columns
            cursor.execute(f"PRAGMA table_info({table})")
            existing_cols = {info[1] for info in cursor.fetchall()}
            required_cols = REQUIRED_COLUMNS.get(table, [])
            missing_cols = [c for c in required_cols if c not in existing_cols]
            
            if missing_cols:
                status = "[WARN]"
                print(f"{status} Table '{table}' exists but MISSING columns: {missing_cols}")
            else:
                print(f"{status} Table '{table}' exists and has required schema.")
                
            # Count records
            try:
                # Some tables might not have run_id/universe if schema differed, but assuming standard
                if "run_id" in existing_cols:
                    cursor.execute(f"SELECT count(*) FROM {table} WHERE universe=? AND run_id=?", (UNIVERSE, target_run))
                    count = cursor.fetchone()[0]
                    print(f"     Records for {UNIVERSE}/{target_run}: {count}")
                    if count == 0:
                         print(f"     [WARN] Dataset empty for this run!")
                else:
                    cursor.execute(f"SELECT count(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"     Total Records (No run_id col): {count}")
            except Exception as e:
                print(f"     Error counting records: {e}")

        else:
            print(f"[FAIL] Table '{table}' MISSING!")
            missing_tables.append(table)

    print("\n--- Data Provider Query Simulation ---")
    
    # 1. Galaxy Map
    print("\n1. Galaxy Topology (get_galaxy_snapshot)")
    print("   Query: SELECT date(timestamp), data_json FROM events WHERE ... event_type = 'galaxy_generated' ...")
    cursor.execute(
        "SELECT date(timestamp), data_json FROM events WHERE universe = ? AND run_id = ? AND event_type = 'galaxy_generated' ORDER BY turn DESC LIMIT 1",
        (UNIVERSE, target_run)
    )
    row = cursor.fetchone()
    if row:
        print("   [OK] Result found.")
        try:
            data = json.loads(row[1])
            sys_count = len(data.get('systems', []))
            print(f"   System Count: {sys_count}")
        except Exception as e:
            print(f"   [FAIL] JSON Parse Error: {e}")
    else:
        print("   [FAIL] No galaxy_generated event found.")

    # 2. Factions
    print("\n2. Faction List (get_factions)")
    cursor.execute(
        "SELECT data_json FROM factions WHERE universe = ? AND run_id = ? ORDER BY turn DESC",
         (UNIVERSE, target_run)
    )
    rows = cursor.fetchall()
    print(f"   [INFO] Faction records found: {len(rows)}")

    # 3. Recent Battles
    print("\n3. Recent Battles (get_recent_battles)")
    cursor.execute(
        "SELECT count(*) FROM battles WHERE universe = ? AND run_id = ?",
        (UNIVERSE, target_run)
    )
    count = cursor.fetchone()[0]
    print(f"   [INFO] Total battles: {count}")

    conn.close()
    
    if missing_tables:
        print(f"\n[SUMMARY] CRITICAL: Missing tables: {missing_tables}")
    else:
        print("\n[SUMMARY] Schema validation passed.")

if __name__ == "__main__":
    diagnose()
