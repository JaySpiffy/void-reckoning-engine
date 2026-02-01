
import os
import json
import sys

sys.path.append(os.getcwd())

from src.data.weapon_data import load_weapon_database, WEAPON_DB

def verify_migration():
    print("--- Verifying Weapon Migration ---")
    
    # 1. Check File Content
    registry_path = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\factions\weapon_registry.json"
    with open(registry_path, 'r') as f:
        data = json.load(f)
        
    first_key = list(data.keys())[0]
    first_entry = data[first_key]
    
    print(f"Checking {first_key} in JSON...")
    stats = first_entry.get("stats", {})
    
    if "S" in stats and "AP" in stats and "D" in stats:
        print(f"  [PASS] Manual stats found in JSON: S={stats['S']}, AP={stats['AP']}, D={stats['D']}")
    else:
        print("  [FAIL] Manual stats NOT found in JSON!")
        return

    # 2. Check Loader Logic
    print("\nChecking WeaponLoader logic...")
    db = load_weapon_database()
    
    # helper for insensitive lookup
    key_lower = first_key.lower()
    
    if key_lower in db:
        loaded_wpn = db[key_lower]
        print(f"  Loaded: {loaded_wpn}")
        
        # Check for dna_source flag from synthesizer
        if loaded_wpn.get("dna_source"):
            print("  [FAIL] Weapon has 'dna_source' flag! It was synthesized despite manual stats.")
        else:
            print("  [PASS] Weapon loaded without 'dna_source' flag. Manual priority worked.")
            
        # Verify values match
        if loaded_wpn["S"] == stats["S"] and loaded_wpn["D"] == stats["D"]:
             print("  [PASS] Loaded values match JSON values.")
        else:
             print(f"  [FAIL] Value mismatch! Loaded S={loaded_wpn['S']}, Expected S={stats['S']}")
            
    else:
        print(f"  [FAIL] Weapon {key_lower} not found in DB!")

if __name__ == "__main__":
    verify_migration()
