
import sys
import os
import json

# Mock the environment to load the local files
import src.data.weapon_data as wd

def test_lookup():
    print("--- Testing Weapon Lookup ---")
    
    # 1. Mock the DNA DB Load (simulate what happens in production)
    # We found that the code iterates and tries v['name'], which triggers KeyError if missing
    # And then catches it.
    
    # Let's inspect the actual loaded DB state if possible, or simulate it.
    # wd.load_weapon_dna_db() has already run on import if specific files exist.
    # But we want to test specific scenarios.
    
    # Mock Data matching the file we viewed
    mock_dna_data = {
        "Solar_Hegemony_base_melee_weapon_3": {
            "atom_mass": 17.3387
            # NO NAME FIELD
        }
    }
    
    # Simulate the load logic from weapon_data.py lines 103-116
    WEAPON_DNA_DB = {}
    WEAPON_DNA_DB.update(mock_dna_data)
    
    try:
        for k, v in mock_dna_data.items():
            WEAPON_DNA_DB[v["name"].lower()] = v
    except Exception as e:
        print(f"Expected Error during secondary indexing: {e}")
        
    print(f"DB Keys: {list(WEAPON_DNA_DB.keys())}")
    
    # 2. Test Lookup
    test_cases = [
        "Solar_Hegemony_base_melee_weapon_3", # Exact Match (Mixed Case)
        "solar_hegemony_base_melee_weapon_3", # Lower Case
        "solar_hegemony_base_melee_weapon_3_M", # With Suffix (What Unit asks for)
        "Solar_Hegemony_base_melee_weapon_0_M" # Missing Weapon
    ]
    
    # Patch the module's DB
    wd.WEAPON_DNA_DB = WEAPON_DNA_DB
    
    for inputs in test_cases:
        print(f"\nQuery: '{inputs}'")
        stats = wd.get_weapon_stats(inputs)
        print(f"Result S/AP/D: {stats.get('S')}/{stats.get('AP')}/{stats.get('D')}")
        print(f"Is Fallback? {'Yes' if stats.get('S')==4 and stats.get('D')==1 else 'No'}")

if __name__ == "__main__":
    test_lookup()
