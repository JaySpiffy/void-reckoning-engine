
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.core.universe_data import UniverseDataManager

def check_arsenals():
    print("Loading Universe Data...")
    manager = UniverseDataManager.get_instance()
    manager.load_universe_data("eternal_crusade")
    
    registry = manager.get_faction_registry()
    print(f"Registry Path: {manager.universe_config.registry_paths.get('faction')}")
    print(f"Faction Registry Keys: {list(registry.keys())}")
    
    factions = ["Iron_Vanguard", "Ancient_Guardians"]
    
    for fname in factions:
        print(f"\nChecking Faction: {fname}")
        # Iterate registry to find match
        fdata = None
        if fname in registry:
             fdata = registry[fname]
        else:
             # Try case insensitive
             for k, v in registry.items():
                 if k.lower() == fname.lower():
                     fdata = v
                     break
        
        if not fdata:
             print(f"  [ERROR] No data found for {fname}")
             continue
             
        arsenal = fdata.get("arsenal", [])
        print(f"  Arsenal Size: {len(arsenal)}")
        if arsenal:
            print("  First 5 items:")
            for item in arsenal[:5]:
                print(f"    - {item}")
        else:
            print("  [WARNING] Arsenal is EMPTY!")

if __name__ == "__main__":
    check_arsenals()
