
import json
import os
from pathlib import Path

BASE_DIR = Path(r"c:\Users\whitt\OneDrive\Desktop\New folder (4)")
UNIVERSE_DIR = BASE_DIR / "universes" / "eternal_crusade"
TECH_DIR = UNIVERSE_DIR / "technology"
INFRA_DIR = UNIVERSE_DIR / "infrastructure"

def load_json(path):
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def generate_unlock_map():
    print("Generating Tech Unlock Map...")
    techs = load_json(TECH_DIR / "technology_registry.json")
    buildings = load_json(INFRA_DIR / "building_registry.json")
    
    # 1. Map Tech -> Buildings (Explicit in 'unlocks_buildings' field of tech)
    # 2. Map Tech -> Units (Requires parsing unit files or inferred from Tech description/unlocks_ships)
    
    unlock_map = {}
    
    for t_id, t_data in techs.items():
        unlocked_b = t_data.get('unlocks_buildings', [])
        unlocked_u = t_data.get('unlocks_ships', []) 
        
        # Also check Building Registry for reverse link
        # (Building says "Prerequisites: [Tech_ID]")
        for b_id, b_data in buildings.items():
            if t_id in b_data.get('prerequisites', []):
                if b_id not in unlocked_b:
                    unlocked_b.append(b_id)
                    
        desc = t_data.get('description', '')
        # Simple extraction from description if "Unlocks X"
        # Not perfect but helpful metadata
        
        entry = {
            "name": t_data['name'],
            "faction": t_data['faction'],
            "unlocks": {
                "buildings": sorted(list(set(unlocked_b))),
                "units": sorted(list(set(unlocked_u))),
                "mechanics": [e['description'] for e in t_data.get('effects', []) if 'unlock' in e['type'].lower() or 'unlock' in e['description'].lower()]
            }
        }
        
        if entry['unlocks']['buildings'] or entry['unlocks']['units'] or entry['unlocks']['mechanics']:
            unlock_map[t_id] = entry
            
    save_json(TECH_DIR / "tech_unlock_map.json", unlock_map)
    print(f"Generated unlock map for {len(unlock_map)} technologies.")

if __name__ == "__main__":
    generate_unlock_map()
