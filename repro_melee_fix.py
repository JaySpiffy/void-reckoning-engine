
import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.getcwd())

from src.combat.realtime.realtime_manager import RealTimeManager

def test_repro_melee_fix():
    print("Running reproduction test for melee fix...")
    
    # Mock battle state
    battle_state = MagicMock()
    battle_state.total_sim_time = 10.0
    battle_state.last_snapshot_time = 0
    battle_state.active_factions = ["faction1", "faction2"]
    
    # Mock unit
    unit = MagicMock()
    unit.is_alive.return_value = True
    unit.is_ship.return_value = False
    unit.grid_x = 0
    unit.grid_y = 0
    unit._shooting_cooldown = 0
    unit.facing = 0
    unit.abilities = {} # Avoid issues in shield regen or elsewhere
    
    # target unit
    target = MagicMock()
    target.is_alive.return_value = True
    target.is_ship.return_value = False
    target.grid_x = 2
    target.grid_y = 2
    
    battle_state.armies_dict = {
        "faction1": [unit],
        "faction2": [target]
    }
    battle_state.grid = MagicMock()
    battle_state.grid.get_distance.return_value = 2.0
    battle_state.grid.query_units_in_range.return_value = []
    battle_state.grid.get_modifiers_at.return_value = {}
    battle_state.faction_doctrines = {}
    battle_state.victory_points = {"faction1": 0, "faction2": 0}
    
    # Mock TargetSelector
    import src.combat.tactical.target_selector as ts
    ts.TargetSelector.select_target_by_doctrine = MagicMock(return_value=(target, None))
    
    # Mock resolve_melee_phase
    import src.combat.ground_combat as gc
    original_melee = gc.resolve_melee_phase
    
    # We want to see if it catches "got multiple values for argument 'round_num'"
    def spy_melee(*args, **kwargs):
        print(f"Melee spy called with args={len(args)} and kwargs={list(kwargs.keys())}")
        return original_melee(*args, **kwargs)
    
    gc.resolve_melee_phase = spy_melee
    
    manager = RealTimeManager()
    
    try:
        manager.update(battle_state, 0.1)
        print("Success: RealTimeManager.update completed.")
    except TypeError as e:
        if "resolve_melee_phase() got multiple values for argument" in str(e):
            print(f"FAILED: Redundant round_num error still present: {e}")
            sys.exit(1)
        else:
            print(f"Caught expected mock-related TypeError (ignored): {e}")
    except Exception as e:
        print(f"Caught expected mock-related Exception (ignored): {e}")
    finally:
        gc.resolve_melee_phase = original_melee

if __name__ == "__main__":
    test_repro_melee_fix()
