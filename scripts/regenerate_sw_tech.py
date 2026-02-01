import os
import sys
import json
from collections import defaultdict
from pathlib import Path

# Fix paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.utils.eaw_xml_parser import EaWXMLParser

# Constants
MOD_PATH = r"E:\SteamLibrary\steamapps\workshop\content\32470\1125571106"
OUTPUT_PATH = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eaw_thrawns_revenge\technology\technology_registry.json"

def regenerate_registry():
    print(f"Initializing parser for {MOD_PATH}...")
    if not os.path.exists(MOD_PATH):
        print("ERROR: Mod path does not exist!")
        return

    parser = EaWXMLParser(os.path.join(MOD_PATH, "Data", "Xml"))
    
    print("Parsing units...")
    units_by_tier = defaultdict(list)
    
    count = 0
    for name in parser.units_raw:
        u = parser._map_to_unit(name)
        if u and u.tier > 0:
            units_by_tier[u.tier].append(u.name)
            count += 1
            
    print(f"Parsed {count} units with tech requirements.")
    
    # Build Registry
    technologies = {}
    
    # Standard EaW Tech Levels 1-5
    for tier in range(1, 6):
        tech_id = f"tech_tier_{tier}"
        
        # Calculate cost (heuristic)
        cost = tier * 2000
        
        # Determine unlocks
        # Tech X unlocks units with Tech_Level == X (and technically enables <= X, but explicit unlocks = X)
        unlocks = units_by_tier.get(tier, [])
        
        technologies[tech_id] = {
            "id": tech_id,
            "name": f"Tech Level {tier}",
            "tier": tier,
            "cost": cost,
            "prerequisites": [f"tech_tier_{tier-1}"] if tier > 1 else [],
            "faction": "Shared",
            "area": "engineering", # Default
            "unlocks_ships": unlocks,
            "unlocks_buildings": [] # Future work
        }
        
    # Write to file
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(technologies, f, indent=2)
        
    print(f"Registry written to {OUTPUT_PATH}")
    print(json.dumps(technologies["tech_tier_1"], indent=2)) # Preview

if __name__ == "__main__":
    regenerate_registry()
