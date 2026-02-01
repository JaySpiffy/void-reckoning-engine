
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

import src.core.config as config
from src.managers.tech_manager import TechManager

def inspect_universe(u_name):
    print(f"\n--- Inspecting Universe: {u_name} ---")
    try:
        config.set_active_universe(u_name)
        print(f"ACTIVE_UNIVERSE: {config.ACTIVE_UNIVERSE}")
        print(f"TECH_DIR: {config.TECH_DIR}")
        
        tm = TechManager()
        factions = list(tm.faction_tech_trees.keys())
        print(f"Factions found: {factions}")
        
        for faction in factions:
            tree = tm.faction_tech_trees[faction]
            print(f"  {faction:25}: Techs={len(tree['techs'])}, Units={len(tree['units'])}")
    except Exception as e:
        print(f"ERROR inspecting {u_name}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_universe("warhammer40k")
    inspect_universe("star_trek")
    inspect_universe("star_wars")
