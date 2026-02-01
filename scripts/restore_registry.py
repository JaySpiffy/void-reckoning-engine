
import json
import os

def register_reinforcements():
    base_path = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\factions"
    registry_path = os.path.join(base_path, "faction_registry.json")
    
    with open(registry_path, "r", encoding='utf-8') as f:
        registry = json.load(f)
        
    for faction in registry.keys():
        f_lower = faction.lower()
        
        if "unit_files" not in registry[faction]:
            registry[faction]["unit_files"] = []
            
        current_files = registry[faction]["unit_files"]
        
        # Scan for ALL unit files in units/ directory starting with faction name
        # This includes *_roster.json, *_specialists.json, *_variants.json, *_space_units.json, *_ground_reinforcements.json
        
        files_to_add = []
        units_dir = os.path.join(base_path, "..", "units")
        try:
             all_files = os.listdir(units_dir)
             for f_name in all_files:
                 if f_name.lower().startswith(f_lower) and f_name.endswith(".json"):
                     rel_path = f"units/{f_name}"
                     files_to_add.append(rel_path)
        except Exception as e:
            print(f"Error scanning units dir: {e}")
            
        # Add to registry (avoid duplicates)
        for f_path in files_to_add:
            if f_path not in current_files:
                current_files.append(f_path)
                print(f"  Added {f_path} for {faction}")
            
    with open(registry_path, "w", encoding='utf-8') as f:
        json.dump(registry, f, indent=2)

if __name__ == "__main__":
    register_reinforcements()
