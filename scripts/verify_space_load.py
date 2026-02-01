
import sys
import os
sys.path.append(os.getcwd())

from src.core.universe_data import UniverseDataManager

def verify():
    print("Loading universe...")
    dm = UniverseDataManager.get_instance()
    try:
        dm.load_universe_data("eternal_crusade")
    except Exception as e:
        print(f"Load failed: {e}")
        # Try loading via CampaignManager which initializes things
        from src.managers.campaign_manager import CampaignManager
        cm = CampaignManager("eternal_crusade")
        # cm.initialize_game() # Might be too heavy
        dm = cm.universe_data
        
    # Validating via Blueprint Registry (Lightweight)
    registry = dm.get_blueprint_registry()
    print(f"Blueprints loaded: {len(registry)}")
    space_bps = [b for b, d in registry.items() if d.get('domain') == 'space' and d.get('faction') == 'Zealot_Legions']
    print(f"Space Blueprints in Registry: {len(space_bps)}")
    
    if space_bps:
         print("SUCCESS: Space units found in registry.")
         print(f"Sample: {space_bps[0]}")
         return
    
    print("FAILURE: No space blueprints found.")
    return
    
    faction = dm.get_faction("Zealot_Legions")
    if not faction:
        print("ERROR: Faction Zealot_Legions not found.")
        return

    print(f"Faction: {faction.name}")
    print(f"Total Units: {len(faction.units)}")
    
    space_units = [u for u in faction.units if getattr(u, 'domain', '') == 'space']
    print(f"Space Units: {len(space_units)}")
    
    if len(space_units) > 0:
        print("SUCCESS: Space units loaded.")
        print("Sample unit:", space_units[0].name)
    else:
        print("FAILURE: No space units found.")

if __name__ == "__main__":
    verify()
