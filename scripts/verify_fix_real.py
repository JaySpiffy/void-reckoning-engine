
import sys
import os
import src.data.weapon_data as wd

def verify_fix():
    print("--- Verifying Real Weapon Data Fix ---")
    
    from src.core.universe_data import UniverseDataManager
    
    # 1. Initialize Universe (Simulate Engine Start)
    print("Initializing Universe: eternal_crusade")
    udm = UniverseDataManager.get_instance()
    udm.load_universe_data("eternal_crusade")
    
    # 2. Verify DB populated
    print(f"DB Size: {len(wd.WEAPON_DNA_DB)}")
    
    # Helper to check content
    def check(query_name, description):
        print(f"\nQuery: '{query_name}' ({description})")
        stats = wd.get_weapon_stats(query_name)
        print(f"Stats: {stats}")
        
        is_fallback = (stats.get("S") == 4 and stats.get("AP") == 0 and stats.get("D") == 1 and stats.get("Type") == "Rapid Fire 1")
        
        if is_fallback:
            print("FAILURE: Still getting Fallback Stats!")
        else:
            print("SUCCESS: Found valid stats!")
            print(f"Synthesized S/AP/D: {stats.get('S')}/{stats.get('AP')}/{stats.get('D')}")

    # Cases
    check("Solar_Hegemony_base_melee_weapon_3_M", "Solar Weapon with Suffix (The Culprit)")
    check("solar_hegemony_base_melee_weapon_3", "Lowercase Base Name")
    check("Scavenger_Clans_base_projectile_weapon_0_M", "Scavenger Weapon with Suffix")

if __name__ == "__main__":
    verify_fix()
