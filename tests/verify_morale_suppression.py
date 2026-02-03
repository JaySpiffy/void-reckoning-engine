
import pytest
from unittest.mock import MagicMock, patch
from src.combat.combat_phases import MoralePhase, CombatPhase
from src.models.unit import Unit
from src.combat.components.morale_component import MoraleComponent

def test_suppression_accumulates():
    """Verify suppression can be applied to a unit."""
    # Ensure correct init with base_leadership
    unit = Unit("Guardsmen", "Imperium", unit_type="Infantry", hp=100)
    unit.add_component(MoraleComponent(max_morale=100, base_leadership=7))
    
    # Simulate taking damage/suppression
    unit.morale_comp.apply_suppression(25)
    
    assert unit.current_suppression == 25, "Suppression failed to accumulate"
    assert not unit.morale_comp.is_broken, "Unit should not be broken yet"

def test_morale_check_failure_routing():
    """Verify that failing a morale check causes routing."""
    # Setup unit with low leadership and high suppression
    unit = Unit("Cowardly Conscripts", "Rebels", unit_type="Infantry", hp=100)
    unit.add_component(MoraleComponent(max_morale=100, base_leadership=4)) # Low LD
    
    # High suppression to trigger check condition
    unit.current_suppression = 50 
    
    # Setup Context
    manager = MagicMock()
    manager.mechanics_engine = None 
    
    context = {
        "manager": manager,
        "active_units": [(unit, "Rebels")],
        "round_num": 1,
        "grid": None
    }
    
    stream_mock = MagicMock()
    stream_mock.randint.return_value = 12
    
    # Use unittest.mock.patch correctly
    with patch("src.combat.combat_phases.get_stream") as mock_get_stream:
        mock_get_stream.return_value = stream_mock
        
        phase = MoralePhase()
        phase.execute(context)
        
        assert unit.is_routing, "Unit failed to route after failed morale check"

if __name__ == "__main__":
    pytest.main([__file__])
