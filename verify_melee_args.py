
import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.getcwd())

from src.combat.ground_combat import resolve_melee_phase

def test_direct_melee_call():
    print("Testing direct resolve_melee_phase call with engine-style arguments...")
    
    # Mock arguments
    u = MagicMock()
    u.is_alive.return_value = True
    u.is_ship.return_value = False
    u.faction = "faction1"
    u.name = "Attacker"
    
    target_unit = MagicMock()
    target_unit.is_alive.return_value = True
    target_unit.is_ship.return_value = False
    target_unit.faction = "faction2"
    target_unit.name = "Defender"
    
    battle_state = MagicMock()
    battle_state.total_sim_time = 10.5
    battle_state.tracker = MagicMock()
    
    # This matches the OLD buggy call in RealTimeManager:
    # melee_context = {
    #     "manager": battle_state,
    #     "tracker": battle_state.tracker,
    #     "round_num": int(battle_state.total_sim_time)
    # }
    # resolve_melee_phase([u], [target_unit], int(battle_state.total_sim_time), **melee_context)
    
    # This matches the NEW fixed call:
    melee_context = {
        "manager": battle_state,
        "tracker": battle_state.tracker
    }
    
    try:
        print("Calling resolve_melee_phase (fixed)...")
        resolve_melee_phase([u], [target_unit], int(battle_state.total_sim_time), **melee_context)
        print("Success: resolve_melee_phase (fixed) called without TypeError.")
    except TypeError as e:
        print(f"FAILED: TypeError caught: {e}")
        sys.exit(1)

    # Now let's PROVE that the old way WOULD have failed (sanity check)
    print("\nSanity check: verifying that redundant 'round_num' WOULD still fail...")
    broken_context = {
        "manager": battle_state,
        "tracker": battle_state.tracker,
        "round_num": int(battle_state.total_sim_time)
    }
    try:
        resolve_melee_phase([u], [target_unit], int(battle_state.total_sim_time), **broken_context)
        print("Sanity check FAILED: Redundant call worked? (This shouldn't happen)")
    except TypeError as e:
        if "got multiple values for argument 'round_num'" in str(e):
            print(f"Sanity check PASSED: Redundant call failed as expected: {e}")
        else:
            print(f"Sanity check error: caught unexpected TypeError: {e}")

if __name__ == "__main__":
    test_direct_melee_call()
