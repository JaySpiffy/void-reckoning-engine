
import pytest
from src.models.unit import Unit
from src.managers.combat.suppression_manager import SuppressionManager
from src.combat.real_time.morale_manager import MoraleManager
from src.core.constants import SUPPRESSED_THRESHOLD, PINNED_THRESHOLD

def test_suppression_accumulation():
    """Verify suppression adds up and respects thresholds."""
    unit = Unit(name="Guardsman", ma=30, md=30, hp=100, armor=10, damage=10, abilities={})
    unit.suppression_resistance = 0 # 100% intake
    
    mgr = SuppressionManager()
    
    # 1. Apply Suppression (Low)
    mgr.apply_suppression(unit, 30.0)
    assert unit.current_suppression == 30.0
    assert unit.is_suppressed == True
    assert unit.is_pinned == False
    
    # 2. Apply Suppression (High -> Pinned)
    mgr.apply_suppression(unit, 50.0)
    assert unit.current_suppression == 80.0
    assert unit.is_suppressed == True
    assert unit.is_pinned == True

def test_suppression_resistance():
    """Verify resistance reduces incoming suppression."""
    unit = Unit(name="Marine", ma=40, md=40, hp=200, armor=30, damage=10, abilities={})
    unit.suppression_resistance = 100 # 50% mitigation (100 / (100+100)) = 0.5
    
    mgr = SuppressionManager()
    
    mgr.apply_suppression(unit, 50.0)
    
    # Expected: 50 * 0.5 = 25
    assert unit.current_suppression == 25.0
    assert unit.is_suppressed == True # >= 25.0

def test_suppression_morale_interaction():
    """Verify pinned units lose morale rapidly."""
    unit = Unit(name="Coward", ma=20, md=20, hp=100, armor=0, damage=5, abilities={})
    unit.morale_current = 100.0
    unit.is_pinned = True
    
    # MoraleManager update for 1 second
    dt = 1.0
    # Update signature: update_unit_morale(unit, dt, all_units, grid)
    # Mock list/grid as they aren't used for this specific check
    # Mock Grid
    class MockGrid:
        def query_units_in_range(self, x, y, radius): return []
    
    grid = MockGrid()
    MoraleManager.update_unit_morale(unit, dt, [], grid)
    
    # Pinned drain is -15.0 per sec
    assert unit.morale_current == 85.0

if __name__ == "__main__":
    test_suppression_accumulation()
    test_suppression_resistance()
    test_suppression_morale_interaction()
    print("Suppression Logic Verified!")
