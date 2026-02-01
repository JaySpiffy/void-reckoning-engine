import os
import sys
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))
import json
from src.core.universe_data import UniverseDataManager
from src.managers.tech_manager import TechManager
from src.models.faction import Faction

def inspect_tech():
    # Setup Universe
    udm = UniverseDataManager.get_instance()
    udm.load_universe_data("eternal_crusade")
    
    # TechManager loads tech trees in __init__
    # We need to make sure config pointing to the right place
    import src.core.config as cfg
    cfg.TECH_DIR = os.path.join("universes", "eternal_crusade", "technology")
    
    tm = TechManager(game_config={"tech_cost_multiplier": 1.0})
    # Tech trees are loaded in __init__ via load_tech_trees()
    
    factions = ["Iron_Vanguard", "Cyber_Synod", "Ancient_Guardians"]
    
    for f_name in factions:
        print(f"\n--- Faction: {f_name} ---")
        f_tree = tm.faction_tech_trees.get(f_name.lower())
        if not f_tree:
            print(f"  [ERROR] No tech tree found for {f_name.lower()}")
            continue
            
        techs = f_tree.get("techs", {})
        prereqs = f_tree.get("prerequisites", {})
        
        print(f"  Total Techs: {len(techs)}")
        print(f"  Total Prereqs: {len(prereqs)}")
        
        # Check specific tech
        target = f"Tech_{f_name}_Heavy Armor"
        if target in techs:
            p = prereqs.get(target, [])
            print(f"  {target} prerequisites: {p}")
        else:
            # Maybe it has a different ID?
            print(f"  {target} NOT FOUND in techs.")
            print(f"  Sample Tech IDs: {list(techs.keys())[:5]}")

        # Check Available Research for a new faction
        f_obj = Faction(f_name)
        # f_obj.unlocked_techs = ["Headquarters", "None"]
        available = tm.get_available_research(f_obj)
        print(f"  Available Research (Starting): {[a['id'] for a in available]}")
        
        # Mock unlock Tier 1
        f_obj.unlocked_techs.append(f"Tech_{f_name}_Basic Doctrine")
        f_obj.unlocked_techs.append(f"Tech_{f_name}_Logistics") # I know it often has Space
        available_t2 = tm.get_available_research(f_obj)
        print(f"  Available Research (After Tier 1 Unlock): {[a['id'] for a in available_t2]}")

if __name__ == "__main__":
    inspect_tech()
