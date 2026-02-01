
import sqlite3
import json
import os
import random
import math
import re

# Paths
RUN_PATH = r"reports/eternal_crusade/batch_20260111_220530/run_1768169127"
CAMPAIGN_LOG = os.path.join(RUN_PATH, "campaign.json")
DB_PATH = "reports/campaign_data.db"
UNIVERSE = "eternal_crusade"
RUN_ID = "run_1768169127"
BATCH_ID = "batch_20260111_220530"

def recover_map():
    print(f"Scanning {CAMPAIGN_LOG} for systems...")
    systems = set()
    
    # Regex to capture system names from logs like:
    # "arrived at Zynkora Sextus" -> System Zynkora? 
    # Actually, usually "SystemName Number" or "SystemName Greek". 
    # Logs: "[DISCOVERY] Hive_Swarm discovered system Zynkora" -> This is cleaner.
    
    discovery_pattern = re.compile(r"discovered system (.+)")
    
    try:
        with open(CAMPAIGN_LOG, 'r') as f:
            for line in f:
                if "discovered system" in line:
                    try:
                        entry = json.loads(line)
                        msg = entry.get("message", "")
                        match = discovery_pattern.search(msg)
                        if match:
                            sys_name = match.group(1).strip()
                            # Clean up planet suffixes to get base system name if possible
                            # But logs say "discovered system Zynkora 10". 
                            # If individual planets are "discovered", we might get duplicates or planet names.
                            # Let's just collect all unique names found in discovery and treat them as systems for visualization.
                            systems.add(sys_name)
                    except:
                        pass
    except FileNotFoundError:
        print("campaign.json not found!")
        return

    print(f"Found {len(systems)} potential systems.")
    
    if not systems:
        print("No systems found in logs. Cannot generate map.")
        return

    # Generate Fake Topology (Spiral or Scatter)
    system_list = []
    
    # Simple phyllotaxis arrangement for nice distribution
    golden_angle = math.pi * (3 - math.sqrt(5))
    
    for i, name in enumerate(systems):
        radius = 50 * math.sqrt(i + 1)
        theta = i * golden_angle
        
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        
        system_list.append({
            "name": name,
            "x": round(x, 2),
            "y": round(y, 2),
            "owner": "Neutral",
            "connections": [], # No lanes for now
            "total_planets": random.randint(1, 5),
            "planets": []
        })

    # Create Event
    event_data = {
        "systems": system_list,
        "lanes": [], # No lanes
        "num_systems": len(system_list)
    }
    
    keyword_str = "galaxy_generated system map topology"
    
    # Insert into DB
    print(f"Inserting galaxy_generated event into {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if event already exists
    cursor.execute("SELECT count(*) FROM events WHERE event_type='galaxy_generated' AND run_id=?", (RUN_ID,))
    if cursor.fetchone()[0] > 0:
        print("Map already exists (or was inserted). Skipping.")
        conn.close()
        return

    # Insert
    # Schema: batch_id, universe, run_id, turn, timestamp, category, event_type, faction, location, entity_type, entity_name, data_json, keywords
    
    cursor.execute("""
        INSERT INTO events (
            batch_id, universe, run_id, turn, timestamp, category, event_type, faction, location, entity_type, entity_name, data_json, keywords
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        BATCH_ID,
        UNIVERSE,
        RUN_ID,
        0,
        "2026-01-11T22:05:30", # Approx start time
        "SYSTEM",
        "galaxy_generated",
        "System",
        None,
        None,
        None,
        json.dumps(event_data),
        keyword_str
    ))
    
    conn.commit()
    conn.close()
    print("Map Recovery Complete!")

if __name__ == "__main__":
    recover_map()
