import pytest
from unittest.mock import MagicMock
from src.managers.combat.retreat_handler import RetreatHandler

@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.get_all_fleets.return_value = []
    ctx.logger = MagicMock()
    return ctx

@pytest.fixture
def retreat_handler(mock_context):
    return RetreatHandler(mock_context)

def test_handle_retreats_no_retreat(retreat_handler, mock_context):
    """Test case where no units have retreated."""
    battle = MagicMock()
    battle.participating_fleets = {"F1"}
    battle.participating_armies = set()
    battle.state.armies_dict = {}
    
    planet = MagicMock()
    
    # Fleet is at location and engaged (implied by not destination)
    f1 = MagicMock()
    f1.id = "F1"
    f1.location = planet
    f1.is_destroyed = False
    f1.destination = None
    
    mock_context.get_all_fleets.return_value = [f1]
    
    retreat_handler.handle_retreats(battle, planet)
    
    # Verify no removal from battle
    assert "F1" in battle.participating_fleets

def test_handle_retreats_moved_fleet(retreat_handler, mock_context):
    """Test fleet that moved away."""
    battle = MagicMock()
    battle.participating_fleets = {"F1"}
    battle.participating_armies = set()
    battle.state.armies_dict = {}
    battle.state.grid = MagicMock()
    
    planet = MagicMock()
    other_planet = MagicMock()
    
    # Fleet moved to other_planet
    f1 = MagicMock()
    f1.id = "F1"
    f1.location = other_planet
    f1.is_destroyed = False
    
    mock_context.get_all_fleets.return_value = [f1]
    
    retreat_handler.handle_retreats(battle, planet)
    
    # Verify removal
    assert "F1" not in battle.participating_fleets

def test_handle_retreats_disengaged_fleet(retreat_handler, mock_context):
    """Test fleet that is at location but disengaged and moving (Retreating phase)."""
    battle = MagicMock()
    battle.participating_fleets = {"F1"}
    
    planet = MagicMock()
    
    f1 = MagicMock()
    f1.id = "F1"
    f1.location = planet
    f1.is_destroyed = False
    f1.is_engaged = False
    f1.destination = "SomeDest" # Moving
    
    mock_context.get_all_fleets.return_value = [f1]
    
    retreat_handler.handle_retreats(battle, planet)
    
    # Verify removal
    # Wait, the logic is: if (not is_engaged and destination is not None) -> Retreated
    # Wait, in the code: if (not fleet.is_engaged and fleet.destination is not None): retreating_fleet_ids.append(fid)
    # Ah, I need to ensure my Mock behaves correctly.
    
    # However, removal from `battle.participating_fleets` acts on the set reference.
    # The Mock set methods should work if it's a real set or we check calls.
    # Here I used a regular set.
    
    assert "F1" not in battle.participating_fleets

def test_cleanup_units_from_grid(retreat_handler, mock_context):
    """Test that retreated units are removed from grid/state."""
    battle = MagicMock()
    battle.participating_fleets = {"F1"}
    battle.participating_armies = set()
    battle.state.grid = MagicMock()
    
    # Setup armies dict with a unit belonging to F1
    u1 = MagicMock()
    u1._fleet_id = "F1"
    u2 = MagicMock()
    u2._fleet_id = "F2" # Staying
    
    battle.state.armies_dict = {"Imperium": [u1, u2]}
    
    planet = MagicMock()
    other_planet = MagicMock()
    
    # F1 moved away
    f1 = MagicMock()
    f1.id = "F1"
    f1.location = other_planet 
    mock_context.get_all_fleets.return_value = [f1]
    
    retreat_handler.handle_retreats(battle, planet)
    
    # u1 should be removed from armies_dict
    assert len(battle.state.armies_dict["Imperium"]) == 1
    assert battle.state.armies_dict["Imperium"][0] == u2
    
    # u1 should be removed from grid
    battle.state.grid.remove_unit.assert_called_with(u1)
