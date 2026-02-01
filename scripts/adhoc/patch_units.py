
import json
import os
import sys

sys.path.append(os.getcwd())

from src.core.universe_data import UniverseDataManager
from src.factories.design_factory import ShipDesignFactory
from src.data.weapon_data import load_weapon_database, WEAPON_DB

def patch_units():
    print("Initializing...")
    manager = UniverseDataManager.get_instance()
    manager.load_universe_data("eternal_crusade")
    
    # Ensure WEAPON_DB is loaded
    if not WEAPON_DB:
        WEAPON_DB.update(load_weapon_database())
        
    registry = manager.get_faction_registry()
    
    # Dummy factories for init
    factory = ShipDesignFactory({}, {}) 
    
    targets = list(registry.keys())
    print(f"Targeting Factions: {targets}")
    
    for faction in targets:
        print(f"\nPatching {faction}...")
        fdata = registry.get(faction)
        if not fdata:
            print(f"  Warning: Faction {faction} not found in registry.")
            continue
            
        arsenal_ids = fdata.get("arsenal", [])
        
        # Hydrate Arsenal manually
        hydrated_arsenal = {}
        
        # 1. Load from Registry IDs
        for w_id in arsenal_ids:
             if isinstance(w_id, str):
                 db_entry = WEAPON_DB.get(w_id.lower())
                 if db_entry:
                     w_data = db_entry.copy()
                     w_data["id"] = w_id
                     # Scale stats using synthesis logic
                     if "stats" in db_entry and "atom_energy" in db_entry["stats"]:
                          from src.core.weapon_synthesizer import synthesize_weapon_stats
                          syn_stats = synthesize_weapon_stats(db_entry["stats"])
                          w_data["stats"] = syn_stats
                          w_data["stats"]["power"] = syn_stats["D"] * syn_stats["Attacks"]
                          w_data["stats"]["range"] = syn_stats["Range"]
                     
                     # Fallback for missing stats
                     if "stats" not in w_data or "range" not in w_data["stats"]:
                          w_data["stats"] = w_data.get("stats", {})
                          w_data["stats"].update({"power": 10, "range": 24, "S": 3, "AP": 0, "D": 1, "Range": 24, "Attacks": 1})
                     
                     # [SCALING LOGIC] Generate S/M/L/XL Variants
                     # Only keep the size variants, discard the generic if we want strict typing?
                     # Let's keep generic for fallback but rely on variants.
                     base_stats = w_data["stats"]
                     base_power = base_stats["power"]
                     base_range = base_stats["range"]
                     
                     sizes = {
                         "_S": {"pow": 0.5, "rng": 0.8},
                         "_M": {"pow": 1.0, "rng": 1.0},
                         "_L": {"pow": 2.5, "rng": 1.25},
                         "_XL": {"pow": 5.0, "rng": 1.5} 
                     }
                     
                     for suffix, mult in sizes.items():
                         variant = w_data.copy()
                         variant["id"] = f"{w_id}{suffix}"
                         variant["name"] = f"{w_data.get('name', w_id)} ({suffix.strip('_')})"
                         variant["stats"] = base_stats.copy()
                         variant["stats"]["power"] = int(base_power * mult["pow"])
                         variant["stats"]["range"] = int(base_range * mult["rng"])
                         if "D" in variant["stats"]: variant["stats"]["D"] = int(variant["stats"]["D"] * mult["pow"])
                         
                         hydrated_arsenal[variant["id"]] = variant
                         
                     # Also keep original? Yes, for safety.
                     hydrated_arsenal[w_id] = w_data
        
        # 2. Auto-Discover from WEAPON_DB if empty or incomplete
        if len(hydrated_arsenal) < 2:
            print("  Arsenal empty/small. Auto-discovering from WEAPON_DB...")
            prefix = f"{faction.lower()}_base_"
            for w_key, w_entry in WEAPON_DB.items():
                if w_key.startswith(prefix):
                     # Hydrate
                     w_data = w_entry.copy()
                     w_id = w_entry.get("id", w_key)
                     w_data["id"] = w_id
                     
                     if "stats" in w_entry and "atom_energy" in w_entry["stats"]:
                          from src.core.weapon_synthesizer import synthesize_weapon_stats
                          syn_stats = synthesize_weapon_stats(w_entry["stats"])
                          w_data["stats"] = syn_stats
                          w_data["stats"]["power"] = syn_stats["D"] * syn_stats["Attacks"]
                          w_data["stats"]["range"] = syn_stats["Range"]

                     # Fallback for missing stats
                     if "stats" not in w_data or "range" not in w_data["stats"]:
                          w_data["stats"] = w_data.get("stats", {})
                          w_data["stats"].update({"power": 10, "range": 24, "S": 3, "AP": 0, "D": 1, "Range": 24, "Attacks": 1})
                     
                     # [SCALING LOGIC] Auto-Discovery Sizes
                     base_stats = w_data["stats"]
                     base_power = base_stats["power"]
                     base_range = base_stats["range"]
                     
                     sizes = {
                         "_S": {"pow": 0.5, "rng": 0.8},
                         "_M": {"pow": 1.0, "rng": 1.0},
                         "_L": {"pow": 2.5, "rng": 1.25},
                         "_XL": {"pow": 5.0, "rng": 1.5} 
                     }
                     
                     for suffix, mult in sizes.items():
                         variant = w_data.copy()
                         variant["id"] = f"{w_id}{suffix}"
                         variant["name"] = f"{w_data.get('name', w_id)} ({suffix.strip('_')})"
                         variant["stats"] = base_stats.copy()
                         variant["stats"]["power"] = int(base_power * mult["pow"])
                         variant["stats"]["range"] = int(base_range * mult["rng"])
                         if "D" in variant["stats"]: variant["stats"]["D"] = int(variant["stats"]["D"] * mult["pow"])
                         hydrated_arsenal[variant["id"]] = variant

                     hydrated_arsenal[w_id] = w_data
        
        print(f"  Hydrated Arsenal Size: {len(hydrated_arsenal)}")
        if not hydrated_arsenal:
            print("  Skipping (No Arsenal)")
            continue

        # Iterate unit files
        unit_files = fdata.get("unit_files", [])
        for u_file in unit_files:
            # We care about space AND ground now
            if "heroes" in u_file: continue
            
            full_path = os.path.join(manager.universe_config.universe_root, u_file)
            print(f"  Checking path: {full_path}")
            if not os.path.exists(full_path):
                print(f"  File not found: {u_file}")
                continue
                
            print(f"  Processing {u_file}...")
            with open(full_path, 'r', encoding='utf-8') as f:
                units = json.load(f)
                
            modified = False
            modified = False
            for u in units:
                # if u.get("domain") != "space": continue # Allow ground now
                
                comps = u.get("components", []) 
                u_class = u.get("unit_class", "infantry")
                
                # Create a dummy hull dict with hardpoints
                hardpoints = {}
                # Space Ships
                if u_class == "fighter": hardpoints = {"weapon_small": 1}
                elif u_class == "bomber": hardpoints = {"weapon_small": 1} 
                elif u_class == "corvette": hardpoints = {"weapon_small": 2, "weapon_medium": 1}
                elif u_class == "frigate": hardpoints = {"weapon_medium": 2, "weapon_small": 2}
                elif u_class == "destroyer": hardpoints = {"weapon_medium": 4}
                elif u_class == "cruiser" or u_class == "light_cruiser": hardpoints = {"weapon_medium": 6, "weapon_heavy": 2}
                elif u_class == "heavy_cruiser" or u_class == "battlecruiser": hardpoints = {"weapon_heavy": 6, "weapon_medium": 4}
                elif u_class == "battleship": hardpoints = {"weapon_heavy": 8, "weapon_medium": 8}
                
                # Ground Units (New)
                elif u_class in ["infantry", "skirmisher", "light_infantry"]: hardpoints = {"weapon_small": 1}
                elif u_class in ["assault_infantry", "elite_infantry"]: hardpoints = {"weapon_small": 2}
                elif u_class in ["light_vehicle", "apc", "vehicle"]: hardpoints = {"weapon_medium": 1}
                elif u_class in ["tank", "battle_tank", "anti_tank"]: hardpoints = {"weapon_medium": 2}
                elif u_class in ["heavy_vehicle", "superheavy_tank", "titan_walker"]: hardpoints = {"weapon_heavy": 2, "weapon_medium": 2}
                
                else: hardpoints = {"weapon_medium": 2}
                
                design = {"components": [], "base_stats": u["base_stats"]}
                
                doctrine = "Balanced" 
                if "elemental_dna" in u:
                     doctrine = factory._determine_doctrine(u["elemental_dna"])

                # Inline fitting logic
                for hp_type, count in hardpoints.items():
                    if "weapon" in hp_type:
                        primary_count = int(count * 0.6)
                        if primary_count == 0 and count > 0: primary_count = 1
                        
                        # --- STRICT SIZING LOGIC ---
                        # Filter arsenal to ONLY include matching suffix
                        required_suffix = ""
                        if "small" in hp_type: required_suffix = "_S"
                        elif "medium" in hp_type: required_suffix = "_M"
                        elif "heavy" in hp_type: required_suffix = "_L" # XL?
                        
                        # Battleships get XL in heavy slots?
                        if u_class in ["battleship", "titan"] and "heavy" in hp_type:
                             required_suffix = "_XL"
                        
                        sized_arsenal = {k: v for k, v in hydrated_arsenal.items() if k.endswith(required_suffix)}
                        
                        # If empty (fallback), try next size down?
                        if not sized_arsenal:
                            if required_suffix == "_XL": 
                                 sized_arsenal = {k: v for k, v in hydrated_arsenal.items() if k.endswith("_L")}
                            elif required_suffix == "_L":
                                 sized_arsenal = {k: v for k, v in hydrated_arsenal.items() if k.endswith("_M")}
                            
                            # Final fallback to base
                            if not sized_arsenal:
                                 sized_arsenal = hydrated_arsenal 

                        # Role-based Weapon Preference (applied on top of Sized Arsenal)
                        role_arsenal = sized_arsenal.copy()
                        u_class_lower = u_class.lower()
                        preferred_tags = []
                        if "bomber" in u_class_lower or "siege" in u_class_lower:
                             preferred_tags = ["missile", "plasma", "torpedo"]
                        elif "interceptor" in u_class_lower or "fighter" in u_class_lower:
                             preferred_tags = ["laser", "projectile", "autocannon"]
                        elif "battleship" in u_class_lower:
                             preferred_tags = ["beam", "lance", "macro", "plasma"]
                        
                        if preferred_tags:
                             subset = {k: v for k, v in role_arsenal.items() if any(t in k.lower() for t in preferred_tags)}
                             if subset:
                                 role_arsenal = subset
                        
                        # Select Weapons
                        w_primary = factory._select_best_weapon(hp_type, role_arsenal, doctrine, "Standard", "Primary")
                        if not w_primary:
                             w_primary = factory._select_best_weapon(hp_type, sized_arsenal, doctrine, "Standard", "Primary")

                        exclude = [w_primary["id"]] if w_primary else []
                        w_secondary = factory._select_best_weapon(hp_type, role_arsenal, doctrine, "Standard", "Secondary", exclude_ids=exclude)
                        if not w_secondary: w_secondary = w_primary
                        
                        for i in range(count):
                            w = w_primary if i < primary_count else w_secondary
                            if w:
                                design["components"].append({"slot": hp_type, "component": w["id"]})
                                design["base_stats"]["damage"] += w["stats"].get("power", 10)
                                w_range = w["stats"].get("range", 0)
                                current_range = design["base_stats"].get("range", 0)
                                if w_range > current_range:
                                    design["base_stats"]["range"] = w_range
                
                if design["components"]:
                     u["components"] = design["components"]
                     u["base_stats"] = design["base_stats"] 
                     modified = True

            if modified:
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(units, f, indent=2)
                print(f"    -> Saved {len(units)} units.")

if __name__ == "__main__":
    patch_units()
