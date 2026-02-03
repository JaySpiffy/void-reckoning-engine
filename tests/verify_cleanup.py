import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.utils.blueprint_registry import BlueprintRegistry
from src.core.config import set_active_universe

def verify_cleanup():
    universe_name = "void_reckoning"
    set_active_universe(universe_name)
    
    registry = BlueprintRegistry.get_instance()
    # universe_path needs to be the absolute path to void_reckoning
    universe_path = os.path.join(os.getcwd(), "universes", universe_name)
    registry.load_blueprints(universe_path=universe_path)
    
    blueprints = registry.list_blueprints()
    print(f"Total blueprints loaded: {len(blueprints)}")
    
    # Test cases
    test_ids = [
        "templars_of_the_flux_fighter_standard", # Procedural Ship
        "algorithmic_hierarchy_micro_swarm_standard", # Procedural Land
        "algorithmic_hierarchy_prime_calculator", # Hand-crafted Hero
        "algorithmic_hierarchy_silicon_god" # Hand-crafted Capital
    ]
    
    for b_id in test_ids:
        bp = registry.get_blueprint(b_id)
        if bp:
            print(f"[PASS] Found blueprint: {b_id} ({bp.get('name')})")
        else:
            print(f"[FAIL] Missing blueprint: {b_id}")

    # Check for some legacy file paths to ensure they are gone
    legacy_file = os.path.join(universe_path, "units", "algorithmic_hierarchy_roster.json")
    if not os.path.exists(legacy_file):
        print(f"[PASS] Legacy file removed: {os.path.basename(legacy_file)}")
    else:
        print(f"[FAIL] Legacy file still exists: {legacy_file}")

if __name__ == "__main__":
    verify_cleanup()
