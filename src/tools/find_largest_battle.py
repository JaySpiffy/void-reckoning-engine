
import os
import json
import glob
import argparse
from typing import List, Dict, Any

def find_largest_battles(run_dir: str):
    print(f"Scanning {run_dir} for combat logs...")
    
    # Recursive gob for Combat_*.json
    # glob pattern: run_dir/turn_*/battles/Combat_*.json
    pattern = os.path.join(run_dir, "turn_*", "battles", "Combat_*.json")
    files = glob.glob(pattern)
    
    print(f"Found {len(files)} combat logs. Analyzing...")
    
    battles = []
    
    for fpath in files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not data.get("rounds"):
                continue
                
            # Get initial state (Round 1 snapshots)
            # If round 1 snapshots are missing (unlikely), check subsequent rounds?
            # Usually round 1 has everything.
            
            # Snapshots might be in the first element of 'rounds'
            first_round = data["rounds"][0]
            snapshots = first_round.get("snapshots", [])
            
            total_units = len(snapshots)
            
            # Count by faction
            faction_counts = {}
            for u in snapshots:
                fac = u.get("faction", "Unknown")
                faction_counts[fac] = faction_counts.get(fac, 0) + 1
            
            # Metadata
            planet = os.path.basename(fpath).split("_")[2] # Combat_T90_PlanetName_Timestamp...
            # A bit fragile splitting by underscore if planet has underscores, but okay for now.
            # Better: use filename
            fname = os.path.basename(fpath)
            # Combat_T{Turn}_{Planet}_{Timestamp}.json
            parts = fname.split("_")
            turn = parts[1]
            planet_name = parts[2]
            
            battles.append({
                "file": fname,
                "path": fpath,
                "turn": turn,
                "planet": planet_name,
                "total_units": total_units,
                "breakdown": faction_counts
            })
            
        except Exception as e:
            print(f"Error parsing {fpath}: {e}")
            continue

    # Sort by total_units desc
    battles.sort(key=lambda x: x["total_units"], reverse=True)
    
    print("\n--- TOP 5 LARGEST BATTLES ---")
    for i, b in enumerate(battles[:5]):
        print(f"{i+1}. {b['planet']} ({b['turn']}) - {b['total_units']} Ships/Units")
        details = ", ".join([f"{k}: {v}" for k,v in b['breakdown'].items()])
        print(f"   [{details}]")
        print(f"   Log: {b['path']}")
    
    if not battles:
        print("No battles found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", help="Path to the run directory (e.g. reports/batch_.../run_001)")
    args = parser.parse_args()
    
    find_largest_battles(args.run_dir)
