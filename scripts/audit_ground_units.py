
import json
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

RAW_GROUND_CLASSES = [
    "light_infantry", "assault_infantry", "skirmisher",
    "light_vehicle", "apc", "anti_tank",
    "battle_tank", "heavy_vehicle", "superheavy_tank"
]

def audit_rosters():
    base_path = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\units"
    factions_dir = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\factions"
    
    # Get factions
    registry_path = os.path.join(factions_dir, "faction_registry.json")
    with open(registry_path, "r", encoding='utf-8') as f:
        registry = json.load(f)
        
    audit_results = {}
    
    print(f"{'Faction':<20} | {' | '.join([c[:3] for c in RAW_GROUND_CLASSES])}")
    print("-" * 60)
    
    for faction in registry.keys():
        # Load all roster files for this faction
        roster_files = [f for f in os.listdir(base_path) if f.startswith(faction.lower()) and f.endswith(".json")]
        
        found_classes = set()
        
        for r_file in roster_files:
            try:
                with open(os.path.join(base_path, r_file), "r", encoding='utf-8') as f:
                    units = json.load(f)
                    for u in units:
                        # Check domain (explicit or inferred)
                        domain = u.get("domain", "ground")
                        u_class = u.get("unit_class")
                        
                        if domain == "ground" and u_class in RAW_GROUND_CLASSES:
                            found_classes.add(u_class)
            except Exception as e:
                print(f"Error reading {r_file}: {e}")
                
        audit_results[faction] = found_classes
        
        # Print row
        row = [faction[:19]]
        for c in RAW_GROUND_CLASSES:
            row.append(" X " if c in found_classes else " . ")
        print(f"{row[0]:<20} | {' | '.join(row[1:])}")

if __name__ == "__main__":
    audit_rosters()
