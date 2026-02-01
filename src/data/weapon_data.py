import os
import json
from src.core.config import DATA_DIR


# Global DB
WEAPON_DB = {}

def load_weapon_database():
    """Internal loader. Returns dict."""
    weapon_db = {}
    from src.core.universe_data import UniverseDataManager
    # Path to weapon database
    uni_config = UniverseDataManager.get_instance().universe_config
    db_path = None
    if uni_config:
        db_path = uni_config.registry_paths.get("weapon")
    
    if not db_path or not os.path.exists(db_path):
        db_path = os.path.join(DATA_DIR, "weapon_registry.json")
    try:
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for w_name, w_data in data.items():
                stats = w_data.get("stats", {})
                
                # Legacy Parse S, AP, D

                # Parse S, AP, D (Legacy path)
                s_val = stats.get("strength", "4")
                ap_val = stats.get("ap", "0")
                d_val = stats.get("damage", "1")
                
                # Parse Range & Type (New V4 Mechanics)
                range_val = stats.get("range", "24\"")
                type_val = stats.get("type", "Rapid Fire 1")
                
                # Clean
                try:
                    s = int(s_val) if str(s_val).isdigit() else 4
                    ap = int(ap_val) if str(ap_val).replace("-","").isdigit() else 0
                    
                    d = 1
                    if 'D6' in str(d_val): d = 3.5
                    elif 'D3' in str(d_val): d = 2
                    elif str(d_val).isdigit(): d = int(d_val)
                    
                    # Range Parse "24\"" -> 24
                    r_int = 0
                    if "Melee" in str(range_val): r_int = 0
                    else:
                        r_clean = str(range_val).replace('"', '').replace('u', '').strip()
                        if r_clean.isdigit(): r_int = int(r_clean)
                        else: r_int = 24 # Default if parse fails
                    
                    # Parse Attacks from Type string (e.g. "Heavy 3", "Rapid Fire 1", "Assault 2")
                    attacks = 1
                    t_parts = str(type_val).split()
                    for p in t_parts:
                         if p.isdigit():
                              attacks = int(p)
                              break
                    
                    weapon_db[w_name.lower()] = {
                        "S": s, "AP": ap, "D": d, 
                        "Range": r_int, "Type": type_val,
                        "Attacks": attacks,
                        "Name": w_name
                    }
                except:
                    continue
    except Exception as e:
        # Only print warning if we expected to find it (i.e. we are running)
        pass 
        
    return weapon_db

def reload_weapon_db():
    """Reloads the global usage strictly."""
    new_db = load_weapon_database()
    WEAPON_DB.clear()
    WEAPON_DB.update(new_db)

# Initial Load (Best effort)
WEAPON_DB.update(load_weapon_database())


def get_weapon_stats(name):
    name_lower = name.lower()
    
    # SUFFIX STRIPPING (Fix for _S, _M, _L, _XL mismatches)
    # Unit files request "weapon_name_S", but DB has "weapon_name"
    suffixes = ["_s", "_m", "_l", "_xl"]
    base_name_lower = name_lower
    for s in suffixes:
        if base_name_lower.endswith(s):
            base_name_lower = base_name_lower[:-len(s)]
            break
            
    # [DNA DB Removal] Fallback to Legacy DB

    # 2. Check Legacy DB
    if name_lower in WEAPON_DB: return WEAPON_DB[name_lower]
    
    # Fuzzy Matching for Land/Titan Weapons
    best_match = None
    if "volcano" in name_lower: best_match = "volcano cannon"
    elif "plasma" in name_lower and "blast" in name_lower: best_match = "plasma blastgun"
    elif "plasma" in name_lower: best_match = "plasma annihilator"
    elif "gatling" in name_lower: best_match = "gatling blaster"
    elif "laser" in name_lower: best_match = "laser blaster"
    elif "missile" in name_lower: best_match = "apocalypse missile launcher"
    elif "vulcan" in name_lower: best_match = "vulcan mega-bolter"
    
    if best_match and best_match in WEAPON_DB:
        return WEAPON_DB[best_match]
        
    # Default Fallback
    return {"S": 4, "AP": 0, "D": 1, "Range": 24, "Type": "Rapid Fire 1", "Name": name}

