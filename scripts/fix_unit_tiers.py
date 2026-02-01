
import json
import os

CLASS_TIER_MAP = {
    # Space
    "fighter": 1, "bomber": 1, "interceptor": 1,
    "corvette": 2, "frigate": 2, "destroyer": 2,
    "light_cruiser": 3, "heavy_cruiser": 3, "battlecruiser": 3, "battleship": 3,
    "carrier": 4, "dreadnought": 4,
    "titan": 5, "planet_killer": 5, "world_devastator": 5, "stellar_accelerator": 5,
    "mothership": 6,
    
    # Ground
    "light_infantry": 1, "assault_infantry": 1, "skirmisher": 1,
    "light_vehicle": 2, "apc": 2, "anti_tank": 2,
    "battle_tank": 3, "heavy_vehicle": 3, "superheavy_tank": 3,
    "command_vehicle": 4,
    "titan_walker": 5, "siege_engine": 5,
    "mobile_fortress": 6
}

def fix_tiers():
    base_dir = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\units"
    
    for filename in os.listdir(base_dir):
        if not filename.endswith(".json"): continue
        
        filepath = os.path.join(base_dir, filename)
        
        try:
            with open(filepath, "r", encoding='utf-8') as f:
                units = json.load(f)
                
            modified = False
            for u in units:
                u_class = u.get("unit_class")
                if u_class in CLASS_TIER_MAP:
                    correct_tier = CLASS_TIER_MAP[u_class]
                    if u.get("tier") != correct_tier:
                        u["tier"] = correct_tier
                        # Also update base_stats tier if present
                        if "base_stats" in u:
                            u["base_stats"]["tier"] = correct_tier
                        modified = True
                        
            if modified:
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump(units, f, indent=2)
                print(f"Fixed tiers in {filename}")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    fix_tiers()
