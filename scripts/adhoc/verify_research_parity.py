import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

import src.core.config as config
from src.core.universe_data import UniverseDataManager
from src.core.constants import get_building_database, categorize_building

def verify_parity():
    print("--- Starting Research Parity Verification ---")
    
    # Setup Universe
    universe_name = "eternal_crusade"
    udm = UniverseDataManager.get_instance()
    udm.load_universe_data(universe_name)
    config.set_active_universe(universe_name)
    
    db = get_building_database()
    
    targets = {
        "Iron_Vanguard": ["Iron_Vanguard_Design Bureau", "Iron_Vanguard_Research Sanctum"],
        "Scavenger_Clans": ["Scavenger_Clans_Tinkerer's Shed", "Scavenger_Clans_Grot Lab"],
        "Ancient_Guardians": ["Ancient_Guardians_Archive of Ages", "Ancient_Guardians_Hall of Prophecy"]
    }
    
    all_passed = True
    for faction, b_ids in targets.items():
        print(f"\nVerifying {faction}:")
        for b_id in b_ids:
            if b_id not in db:
                print(f"  [FAIL] Building {b_id} not found in registry!")
                all_passed = False
                continue
                
            b_data = db[b_id]
            cat = categorize_building(b_id, b_data)
            tier = b_data.get("tier")
            
            if cat == "Research":
                print(f"  [PASS] {b_id}: Category=Research, Tier={tier}")
            else:
                print(f"  [FAIL] {b_id}: Category={cat}, Tier={tier} (Expected Category=Research)")
                all_passed = False

    if all_passed:
        print("\n--- All Research Parity Checks Passed ---")
    else:
        print("\n--- Some Research Parity Checks Failed ---")

if __name__ == "__main__":
    verify_parity()
