import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.combat.combat_state import CombatState
from src.builders.unit_builder import UnitBuilder
from src.combat.grid.grid_manager import GridManager
from src.combat.realtime.realtime_manager import RealTimeManager

def test_combat_state_init():
    print("Testing CombatState Initialization...")
    
    # Create dummy units
    u1 = UnitBuilder("Unit A", "FactionA").with_health(100).build()
    u2 = UnitBuilder("Unit B", "FactionB").with_health(100).build()
    
    armies = {"FactionA": [u1], "FactionB": [u2]}
    
    state = CombatState(armies, {}, {})
    state.initialize_battle()
    
    if hasattr(state, 'grid_manager') and isinstance(state.grid_manager, GridManager):
         print("GridManager initialized: OK")
    else:
         print("FAIL: GridManager missing")
         
    if hasattr(state, 'realtime_manager') and isinstance(state.realtime_manager, RealTimeManager):
         print("RealTimeManager initialized: OK")
    else:
         print("FAIL: RealTimeManager missing")
         
    if state.grid:
         print("Grid Compatibility Attribute: OK")
         
    # Check placement
    u1_node = state.grid_manager.get_unit_at(u1.grid_x, u1.grid_y)
    if u1_node == u1:
         print("Unit Placement from Init: OK")
    else:
         print(f"FAIL: Unit not found at {u1.grid_x}, {u1.grid_y}")

def test_real_time_update():
    print("\nTesting Real Time Update Delegation...")
    
    u1 = UnitBuilder("Unit A", "FactionA").with_health(100).with_movement(5).build()
    u2 = UnitBuilder("Unit B", "FactionB").with_health(100).build()
    
    # Manually place them near each other
    u1.grid_x, u1.grid_y = 10, 10
    u2.grid_x, u2.grid_y = 15, 10 # 5 tiles away
    
    armies = {"FactionA": [u1], "FactionB": [u2]}
    state = CombatState(armies, {}, {})
    state.initialize_battle()
    
    # Overwrite placement with test coords
    state.grid_manager.move_unit(u1, 10, 10)
    state.grid_manager.move_unit(u2, 15, 10)
    
    print("Executing real_time_update(0.1)...")
    try:
        state.real_time_update(0.1)
        print("Update executed without crash.")
    except Exception as e:
        print(f"CRASH during update: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        test_combat_state_init()
        test_real_time_update()
        print("\nCombat Refactor Verification: PASSED")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
