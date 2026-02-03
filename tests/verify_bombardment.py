
import pytest
from unittest.mock import MagicMock
from src.combat.combat_phases import OrbitalSupportPhase
from src.models.unit import Unit

class MockFleet:
    def __init__(self, faction, location):
        self.faction = faction
        self.location = location
        self.is_destroyed = False

class MockPlanet:
    def __init__(self, name):
        self.name = name

class MockManager:
    def __init__(self):
        self.armies_dict = {}
        self.location = None
        self.context = None # Campaign ref

def test_orbital_bombardment_triggers():
    """
    Verify that an orbiting fleet provides support to ground troops.
    """
    # Setup
    planet = MockPlanet("TestPlanet")
    
    manager = MockManager()
    manager.location = planet
    manager.location.parent_planet = planet # Ensure logic sees it as ground
    
    # Setup Armies
    # Faction A has troops and fleet
    # Faction B has troops only
    # Pass 'hp' to trigger HealthComponent creation
    unit_a = Unit("Marine Squad", "FactionA", unit_type="Infantry", hp=100)
    unit_b = Unit("Rebel Scum", "FactionB", unit_type="Infantry", hp=1000)
    
    # Manually add MoraleComponent since Unit init might skip it
    from src.combat.components.morale_component import MoraleComponent
    unit_b.add_component(MoraleComponent(max_morale=100, base_leadership=7))
    
    manager.armies_dict = {
        "FactionA": [unit_a],
        "FactionB": [unit_b]
    }
    
    # Setup Campaign Context
    mock_campaign = MagicMock()
    fleet_a = MockFleet("FactionA", planet)
    mock_campaign.get_all_fleets.return_value = [fleet_a]
    manager.context = mock_campaign
    
    # Execute Phase
    phase = OrbitalSupportPhase()
    context = {"manager": manager}
    
    print(f"\n[Before] Target HP: {unit_b.current_hp}")
    phase.execute(context)
    print(f"[After] Target HP: {unit_b.current_hp}")
    
    # Assertions
    # 1. Damage should be dealt (Base 100)
    assert unit_b.current_hp < 1000, "Orbital bombardment failed to deal damage"
    
    # 2. Morale should be impacted
    assert unit_b.morale_current < unit_b.morale_max, "Orbital bombardment failed to damage morale"

def test_no_orbital_support_if_no_fleet():
    """
    Verify that NO bombardment occurs if fleet is not present.
    """
    planet = MockPlanet("LonelyPlanet")
    manager = MockManager()
    manager.location = planet
    manager.location.parent_planet = planet
    
    unit_a = Unit("Marine Squad", "FactionA", unit_type="Infantry", hp=100)
    unit_b = Unit("Alien Bug", "FactionB", unit_type="Infantry", hp=1000)
    
    manager.armies_dict = {"FactionA": [unit_a], "FactionB": [unit_b]}
    
    mock_campaign = MagicMock()
    mock_campaign.get_all_fleets.return_value = [] # No fleets
    manager.context = mock_campaign
    
    phase = OrbitalSupportPhase()
    phase.execute({"manager": manager})
    
    assert unit_b.current_hp == 1000, "Damage dealt despite no fleet in orbit!"

if __name__ == "__main__":
    pytest.main([__file__])
