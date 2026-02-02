
import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.combat.real_time.morale_manager import MoraleManager

class MockUnit:
    def __init__(self, name="Test Unit"):
        self.name = name
        self.morale_current = 100
        self.morale_max = 100
        self.morale_state = "Steady"
        self.time_since_last_damage = 0.0
        self.recent_damage_taken = 0.0
        self.max_hp = 100
        self.grid_x = 0
        self.grid_y = 0
        self.faction = "FactionA"
        self.abilities = {}
        self.is_pinned = False
        self.is_suppressed = False
        
    def is_alive(self):
        return True

def test_morale_hysteresis():
    print("Running Morale Hysteresis Test...")
    
    unit = MockUnit()
    grid = MagicMock()
    grid.query_units_in_range.return_value = []
    dt = 0.2
    
    # 1. Break the unit
    unit.morale_current = -1.0
    MoraleManager.update_unit_morale(unit, dt, [unit], grid)
    print(f"State after breaking (Morale -1): {unit.morale_state}")
    assert unit.morale_state == "Routing"
    
    # 2. Morale recovers slightly (e.g. to 5.0), but still below threshold (50)
    # In the old code, this would have caused a flip to "Shaken"
    unit.morale_current = 5.0
    MoraleManager.update_unit_morale(unit, dt, [unit], grid)
    print(f"State after minor recovery (Morale 5): {unit.morale_state}")
    assert unit.morale_state == "Routing", f"FAILED: Unit should still be Routing at 5.0 Morale, but is {unit.morale_state}"
    
    # 3. Morale recovers to 51.0 (above rally threshold)
    unit.morale_current = 51.0
    MoraleManager.update_unit_morale(unit, dt, [unit], grid)
    print(f"State after recovery to 51: {unit.morale_state}")
    assert unit.morale_state == "Shaken", f"FAILED: Unit should have rallied to Shaken at 51.0 Morale, but is {unit.morale_state}"
    
    # 4. Morale recovers more to 60.0 (above steady threshold 40)
    unit.morale_current = 60.0
    MoraleManager.update_unit_morale(unit, dt, [unit], grid)
    print(f"State after recovery to 60: {unit.morale_state}")
    assert unit.morale_state == "Steady", f"FAILED: Unit should have rallied to Steady at 60.0 Morale, but is {unit.morale_state}"
    
    # 5. Drop morale to 25.0 (below shaken threshold 30)
    unit.morale_current = 25.0
    MoraleManager.update_unit_morale(unit, dt, [unit], grid)
    print(f"State after drop to 25: {unit.morale_state}")
    assert unit.morale_state == "Shaken", f"FAILED: Unit should be Shaken at 25.0 Morale, but is {unit.morale_state}"

    # 6. Drop morale to 0.0
    unit.morale_current = 0.0
    MoraleManager.update_unit_morale(unit, dt, [unit], grid)
    print(f"State after drop to 0: {unit.morale_state}")
    assert unit.morale_state == "Routing"

    print("Test Passed Successfully!")

if __name__ == "__main__":
    try:
        test_morale_hysteresis()
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"AN ERROR OCCURRED: {e}")
        sys.exit(1)
