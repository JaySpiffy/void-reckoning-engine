
import os
import sys
import shutil
import sqlite3
import json
import re
import math
import random

sys.path.append(os.getcwd())

from src.reporting.indexer import ReportIndexer

import glob

# Configuration
DB_PATH = "reports/campaign_data.db"
UNIVERSE = "eternal_crusade"

def get_latest_run():
    # reports/eternal_crusade/batch_*/run_*
    base_dir = os.path.join("reports", UNIVERSE)
    if not os.path.exists(base_dir): return None, None, None
    
    batch_dirs = sorted(glob.glob(os.path.join(base_dir, "batch_*")), reverse=True)
    if not batch_dirs: return None, None, None
    
    latest_batch = batch_dirs[0]
    batch_id = os.path.basename(latest_batch)
    
    run_dirs = sorted(glob.glob(os.path.join(latest_batch, "run_*")), reverse=True)
    if not run_dirs: return None, None, None
    
    latest_run = run_dirs[0]
    run_id = os.path.basename(latest_run)
    
    return batch_id, run_id, latest_run

BATCH_ID, RUN_ID, RUN_PATH = get_latest_run()
if not RUN_ID:
    print("No runs found!")
    sys.exit(1)

print(f"Targeting Latest Run: {RUN_ID} (Batch: {BATCH_ID})")

def recover_map(db_path):
    print(f"  > [MAP RECOVERY] Scanning campaign.json...")
    log_path = os.path.join(RUN_PATH, "campaign.json")
    systems = set()
    discovery_pattern = re.compile(r"discovered system (.+)")
    
    try:
        with open(log_path, 'r') as f:
            for line in f:
                if "discovered system" in line:
                    try:
                        entry = json.loads(line)
                        msg = entry.get("message", "")
                        match = discovery_pattern.search(msg)
                        if match:
                            systems.add(match.group(1).strip())
                    except:
                        pass
    except FileNotFoundError:
        print("    ! campaign.json not found")
        return

    print(f"    - Found {len(systems)} systems")
    if not systems: return

    # Generate Topology
    system_list = []
    golden_angle = math.pi * (3 - math.sqrt(5))
    for i, name in enumerate(systems):
        radius = 50 * math.sqrt(i + 1)
        theta = i * golden_angle
        system_list.append({
            "name": name,
            "x": round(radius * math.cos(theta), 2),
            "y": round(radius * math.sin(theta), 2),
            "owner": "Neutral",
            "connections": [],
            "total_planets": random.randint(1, 5),
            "planets": []
        })

    event_data = {"systems": system_list, "lanes": [], "num_systems": len(system_list)}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (
            batch_id, universe, run_id, turn, timestamp, category, event_type, 
            faction, location, entity_type, entity_name, data_json, keywords
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        BATCH_ID, UNIVERSE, RUN_ID, 0, "2026-01-11T22:05:30", "SYSTEM", "galaxy_generated",
        "System", None, None, None, json.dumps(event_data), "galaxy_generated system map topology"
    ))
    conn.commit()
    conn.close()
    print("  > [MAP RECOVERY] Success!")

def rebuild():
    # 1. Delete Corrupted DB
    if os.path.exists(DB_PATH):
        print(f"Deleting corrupted database: {DB_PATH}")
        try:
            os.remove(DB_PATH)
        except PermissionError:
            print("ERROR: Cannot delete database. It is being used by another process (Docker?).")
            print("Please run 'docker-compose down' first.")
            return

    # 2. Initialize Fresh DB (Schema)
    print("Initializing fresh database...")
    indexer = ReportIndexer(db_path=DB_PATH)
    
    # 3. Index the Run (Standard Data)
    print(f"Indexing run: {RUN_PATH}...")
    if os.path.exists(RUN_PATH):
        indexer.index_run(os.path.abspath(RUN_PATH), universe=UNIVERSE)
    else:
        print(f"Run path not found: {RUN_PATH}")
        return

    # 4. Recover Map (Custom)
    recover_map(DB_PATH)
    
    # 5. Recover Logs (Custom via Indexer)
    print(f"Re-indexing text logs...")
    log_path = os.path.join(RUN_PATH, "campaign.json")
    if os.path.exists(log_path):
        indexer._index_text_log(BATCH_ID, RUN_ID, log_path, universe=UNIVERSE)
        indexer.conn.commit()
    
    print("\nDatabase Rebuild Complete!")
    print("You can now restart the dashboard.")

if __name__ == "__main__":
    rebuild()
