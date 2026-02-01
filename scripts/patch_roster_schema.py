import json
import os
import glob
import sys

# Define mappings for inference
# Keywords in name -> Class

RANK_KEYWORDS = {
  "space": {
      "fighter": ["fighter", "interceptor", "bomber", "initiate", "scout"],
      "corvette": ["corvette", "raider", "escort"],
      "frigate": ["frigate"],
      "destroyer": ["destroyer"],
      "cruiser": ["cruiser", "light cruiser", "heavy cruiser"],
      "battleship": ["battleship", "flagship", "dreadnought"],
      "titan": ["titan", "colossus"],
      "carrier": ["carrier", "hive ship"]
  },
  "ground": {
      "light_infantry": ["light", "scout", "ranger", "skirmisher", "cultist", "gaunt"],
      "assault_infantry": ["assault", "berserker", "warrior", "boyz"],
      "light_vehicle": ["bike", "speeder", "chariot", "buggy"],
      "battle_tank": ["tank", "predator", "lemean", "hammerhead"],
      "heavy_vehicle": ["heavy", "artillery", "basilisk"],
      "titan_walker": ["titan", "knight", "stompa", "wraithknight"],
      "command_vehicle": ["command", "hq"]
  }
}

DEFAULT_SPACE = "fighter"
DEFAULT_GROUND = "light_infantry"

def infer_class_and_domain(unit_data):
    u_type = unit_data.get("type", "infantry").lower()
    name = unit_data.get("name", "").lower()
    desc = unit_data.get("description", "").lower()
    
    # 1. Determine Domain
    domain = "ground"
    if "ship" in u_type or "fleet" in u_type:
        domain = "space"
    
    # 2. Determine Class
    assigned_class = None
    
    # Special overrides based on existing blueprints names
    if "initiate" in name and domain == "ground": assigned_class = "light_infantry"
    if "templar" in name and domain == "ground": assigned_class = "assault_infantry"
    if "chariot" in name and domain == "ground": assigned_class = "light_vehicle"
    if "penitent" in name: assigned_class = "heavy_vehicle"
    if "cherubim" in name: assigned_class = "fighter"
    if "sword" in name and domain == "space": assigned_class = "frigate"
    if "cathedral" in name: assigned_class = "cruiser"
    if "basilica" in name: assigned_class = "battleship"
    if "crusader" in name and unit_data.get("tier", 0) >= 5: assigned_class = "titan_walker" # Hero titan
    
    if not assigned_class:
        # Keyword search
        mapping = RANK_KEYWORDS[domain]
        for cls, keywords in mapping.items():
            for kw in keywords:
                if kw in name or kw in desc:
                    assigned_class = cls
                    break
            if assigned_class: break
            
    if not assigned_class:
        assigned_class = DEFAULT_SPACE if domain == "space" else DEFAULT_GROUND
        
    return assigned_class, domain

def patch_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        modified = False
        if isinstance(data, list):
            for unit in data:
                # Always update if missing
                if "unit_class" not in unit or "domain" not in unit:
                    cls, dom = infer_class_and_domain(unit)
                    unit["unit_class"] = cls
                    unit["domain"] = dom
                    modified = True
        elif isinstance(data, dict):
             # Some might be single dicts? Roster usually list. check.
             if "unit_class" not in data or "domain" not in data:
                 cls, dom = infer_class_and_domain(data)
                 data["unit_class"] = cls
                 data["domain"] = dom
                 modified = True
                 
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"Patched {os.path.basename(filepath)}")
            
    except Exception as e:
        print(f"Error patching {filepath}: {e}")

if __name__ == "__main__":
    target_dir = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\units"
    files = glob.glob(os.path.join(target_dir, "*.json"))
    print(f"Found {len(files)} files to patch.")
    
    for f in files:
        patch_file(f)
