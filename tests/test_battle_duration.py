
import json
import os
import sys
import time

# Add project root to path
sys.path.append(os.getcwd())

from src.combat.tactical_engine import resolve_real_time_combat
from src.factories.unit_factory import UnitFactory
from src.utils.unit_parser import load_all_units

def test_battle_timeout():
    print("\n>>> Testing Battle Timeout Logic (Max 5s) <<<")
    
    # 1. Load Data
    total_loaded = load_all_units()
    factions = sorted(list(total_loaded.keys()))
    f1_name = factions[0]
    f2_name = factions[1]
    
    # 2. Build Small but Tough Armies
    def build_test_army(bps, count, faction):
        army = []
        for i in range(count):
            bp = bps[i % len(bps)]
            unit = UnitFactory.create_from_blueprint(bp, faction)
            unit.name = f"{bp.name} #{i+1}"
            unit.base_hp = 1000000 
            unit.current_hp = 1000000
            army.append(unit)
        return army

    army1 = build_test_army(total_loaded[f1_name], 50, f1_name)
    army2 = build_test_army(total_loaded[f2_name], 50, f2_name)
    
    armies_dict = {f1_name: army1, f2_name: army2}
    
    # 3. Resolve with short timeout
    print("Starting combat with max_time=5.0s...")
    start_time = time.time()
    
    winner, survivors, sim_time, stats = resolve_real_time_combat(
        armies_dict,
        silent=False,
        max_time=5.0,
        dt=0.1,
        combat_domain="space"
    )
    
    end_time = time.time()
    real_elapsed = end_time - start_time
    
    print(f"\n--- Results ---")
    print(f"Winner: {winner}")
    print(f"Simulated Time: {sim_time}s")
    print(f"Real Wall-Clock Time: {real_elapsed:.2f}s")
    
    if sim_time >= 5.0:
        print("SUCCESS: Battle timed out as expected.")
    else:
        print(f"FAILURE: Battle ended early ({sim_time}s) or logic skipped timeout.")

if __name__ == "__main__":
    test_battle_timeout()
