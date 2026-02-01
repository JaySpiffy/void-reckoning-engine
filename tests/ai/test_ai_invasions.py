
import pytest
from unittest.mock import MagicMock, call
from src.managers.ai_manager import StrategicAI
from src.core.interfaces import IEngine

def test_ai_triggers_invasion_on_siege():
    """
    Verifies that StrategicAI._process_sieges calls battle_manager.land_armies
    when a fleet is orbiting a sieged planet with cargo armies.
    """
    # Setup Mocks
    engine = MagicMock(spec=IEngine)
    engine.fleets = []
    engine.factions = {}
    engine.turn_counter = 10
    
    # Mock Managers
    engine.battle_manager = MagicMock()
    engine.tech_manager = MagicMock() # Needed for TechDoctrineManager
    engine.logger = MagicMock()
    
    # Mock Faction
    f_mgr = MagicMock()
    engine.factions["Imperium"] = f_mgr
    
    # Mock Planet (Sieged)
    planet = MagicMock()
    planet.name = "Cadia"
    planet.owner = "Chaos" # Enemy
    planet.is_sieged = True
    
    # Mock Fleet (Orbiting, with Cargo)
    fleet = MagicMock()
    fleet.name = "Battlefleet Gothic"
    fleet.faction = "Imperium"
    fleet.location = planet
    fleet.is_destroyed = False
    fleet.cargo_armies = ["Regiment A"] # Has cargo
    
    # Set Engine State
    engine.fleets = [fleet]
    
    # Initialize AI
    ai = StrategicAI(engine)
    
    # Execute Check
    ai._process_sieges("Imperium")
    
    # Assertion: Invasion Triggered
    engine.battle_manager.land_armies.assert_called_once_with(fleet, planet)
    engine.logger.campaign.assert_called_with("[STRATEGY] Imperium launching invasion of Cadia from Battlefleet Gothic!")
    
def test_ai_skips_unsieged_planet():
    """
    Verifies that invasion is NOT triggered if planet is not sieged.
    """
    engine = MagicMock(spec=IEngine)
    engine.fleets = []
    engine.factions = {}
    engine.battle_manager = MagicMock()
    engine.tech_manager = MagicMock()
    
    f_mgr = MagicMock()
    engine.factions["Imperium"] = f_mgr
    
    planet = MagicMock()
    planet.name = "Cadia"
    planet.owner = "Chaos"
    planet.is_sieged = False # NOT sieged
    
    fleet = MagicMock()
    fleet.faction = "Imperium"
    fleet.location = planet
    fleet.is_destroyed = False
    fleet.cargo_armies = ["Regiment A"]
    
    engine.fleets = [fleet]
    
    ai = StrategicAI(engine)
    ai._process_sieges("Imperium")
    
    # Assertion: No Invasion
    engine.battle_manager.land_armies.assert_not_called()

def test_ai_skips_empty_fleet():
    """
    Verifies that invasion is NOT triggered if fleet has no cargo.
    """
    engine = MagicMock(spec=IEngine)
    engine.fleets = []
    engine.factions = {}
    engine.battle_manager = MagicMock()
    engine.tech_manager = MagicMock()
    
    f_mgr = MagicMock()
    engine.factions["Imperium"] = f_mgr
    
    planet = MagicMock()
    planet.name = "Cadia"
    planet.owner = "Chaos"
    planet.is_sieged = True
    
    fleet = MagicMock()
    fleet.faction = "Imperium"
    fleet.location = planet
    fleet.is_destroyed = False
    fleet.cargo_armies = [] # Empty cargo
    
    engine.fleets = [fleet]
    
    ai = StrategicAI(engine)
    ai._process_sieges("Imperium")
    
    # Assertion: No Invasion
    engine.battle_manager.land_armies.assert_not_called()
    
if __name__ == "__main__":
    test_ai_triggers_invasion_on_siege()
    test_ai_skips_unsieged_planet()
    test_ai_skips_empty_fleet()
    print("AI Invasion Logic Verified!")
