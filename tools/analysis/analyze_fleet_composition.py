import re
import os
from collections import defaultdict

LOG_FILE = r'C:\Users\whitt\Desktop\New folder (4)\reports\batch_20251229_093226\run_001\full_campaign_log.txt'

def analyze():
    print(f"Reading {LOG_FILE}...")
    
    fleet_loads = defaultdict(list) # Faction -> [LoadSize, ...]
    battles = []
    
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Parse Embark for Fleet Size
            # Pattern: [EMBARK] Faction Army X boarded Faction Battlefleet Y (Load: 57/130)
            embark_match = re.search(r'boarded (.*?) Battlefleet .*? \(Load: (\d+)/(\d+)\)', line)
            if embark_match:
                faction = embark_match.group(1)
                load = int(embark_match.group(2))
                capacity = int(embark_match.group(3))
                fleet_loads[faction].append(load)
                
            # Parse Battle Start
            if "BATTLE STARTED" in line:
                battles.append(line.strip())
            
            # Parse Battle End
            end_match = re.search(r'Battle at .*? ending .*? \(Round (\d+)\)', line)
            if end_match:
                pass # rounds = int(end_match.group(1))

    print("\n--- FLEET SIZE ANALYSIS (Based on Transport Usage) ---")
    for faction, loads in sorted(fleet_loads.items()):
        if not loads: continue
        avg_load = sum(loads) / len(loads)
        max_load = max(loads)
        print(f"{faction}: Max Fleet Size Observed: {max_load} units. Avg: {avg_load:.1f}")
        
    print("\n--- COMBAT ANALYSIS ---")
    print(f"Total Battles Initiated: {len(battles)}")
    if battles:
        print("Sample Battles:")
        for b in battles[-5:]:
            print(f"  {b}")

if __name__ == "__main__":
    analyze()
