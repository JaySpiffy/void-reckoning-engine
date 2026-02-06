import pytest
from src.combat.combat_state import CombatState
from src.models.unit import Unit

@pytest.fixture
def create_mock_unit():
    def _create(name):
        return Unit(name, 40, 40, 10, 0, 5, {}, faction="TestFaction")
    return _create

def test_small_skirmish_scaling(create_mock_unit):
    """Test that < 20 units results in a 30x30 grid."""
    armies = {
        "FactionA": [create_mock_unit(f"A_{i}") for i in range(5)],
        "FactionB": [create_mock_unit(f"B_{i}") for i in range(5)]
    }
    # Total 10 units
    state = CombatState(armies, {}, {})
    state.initialize_battle()
    
    assert state.grid.width == 30
    assert state.grid.height == 30

def test_medium_battle_scaling(create_mock_unit):
    """Test that 20-59 units results in a 50x50 grid."""
    armies = {
        "FactionA": [create_mock_unit(f"A_{i}") for i in range(15)],
        "FactionB": [create_mock_unit(f"B_{i}") for i in range(15)]
    }
    # Total 30 units
    state = CombatState(armies, {}, {})
    state.initialize_battle()
    
    assert state.grid.width == 50
    assert state.grid.height == 50

def test_massive_battle_scaling(create_mock_unit):
    """Test that >= 150 units results in a 100x100 grid."""
    armies = {
        "FactionA": [create_mock_unit(f"A_{i}") for i in range(80)],
        "FactionB": [create_mock_unit(f"B_{i}") for i in range(80)]
    }
    # Total 160 units
    state = CombatState(armies, {}, {})
    state.initialize_battle()
    
    assert state.grid.width == 100
    assert state.grid.height == 100

def test_unit_placement_bounds(create_mock_unit):
    """Verify units are placed within the grid bounds."""
    armies = {
        "FactionA": [create_mock_unit(f"A_BOUNDS_{i}") for i in range(5)],
        "FactionB": [create_mock_unit(f"B_BOUNDS_{i}") for i in range(5)]
    }
    state = CombatState(armies, {}, {})
    state.initialize_battle()
    
    for u in armies["FactionA"]:
        x, y = u.grid_x, u.grid_y
        assert x is not None
        assert y is not None
        assert 0 <= x < 30
        assert 0 <= y < 30
        # Verify relative placement logic roughly
        assert x >= int(30 * 0.35)
        assert x <= int(30 * 0.45) + 5
