import pytest
from unittest.mock import MagicMock
from src.managers.combat.invasion_manager import InvasionManager
from src.models.planet import Planet
from src.models.hex_node import HexNode
from src.models.faction import Faction
from src.core.universe_data import UniverseDataManager

# Mock UniverseDataManager before importing models that use it
mock_udm = MagicMock()
mock_udm.get_planet_classes.return_value = {"Terran": {"req_mod": 1.0, "def_mod": 1, "slots": 5}}
mock_udm.get_building_database.return_value = {
    "Major_Spaceport": {"cost": 1000, "effects": {"description": "Naval Slots +1"}},
    "Barracks": {"cost": 400, "effects": {"description": "Army Slots +1"}}
}
UniverseDataManager.get_instance = MagicMock(return_value=mock_udm)

class MockContext:
    def __init__(self):
        self.logger = MagicMock()
        self.telemetry = MagicMock()
        self.turn_counter = 1
        self.factions = {
            "FactionA": Faction("FactionA"),
            "FactionB": Faction("FactionB")
        }
        self.planets = {}
        self.diplomacy = None

    def get_faction(self, name):
        return self.factions.get(name)

    def get_planet(self, name):
        return self.planets.get(name)

    def update_planet_ownership(self, planet, owner):
        planet.owner = owner

def setup_mock_planet():
    planet = Planet("TestPlanet", None, 1)
    planet.owner = "FactionA"
    
    # Mock Provinces
    cap = HexNode("TestPlanet_Cap", 0, 0, "TestPlanet")
    cap.type = "Capital"
    cap.owner = "FactionA"
    cap.buildings = ["Major_Spaceport"]
    
    city = HexNode("TestPlanet_City", 1, 0, "TestPlanet")
    city.type = "ProvinceCapital"
    city.owner = "FactionA"
    city.buildings = ["Barracks"]
    
    waste = HexNode("TestPlanet_Waste", 2, 0, "TestPlanet")
    waste.type = "LandingZone"
    waste.owner = "FactionA"
    
    planet.provinces = [cap, city, waste]
    return planet, cap, city, waste

def test_partial_conquest_logic():
    ctx = MockContext()
    manager = InvasionManager(ctx)
    planet, cap, city, waste = setup_mock_planet()
    ctx.planets[planet.name] = planet
    
    # Capture city only
    manager.handle_conquest(city, "FactionB", decision="occupy")
    
    assert city.owner == "FactionB"
    assert planet.owner == "FactionA" # Should NOT flip because Capital is still FactionA
    assert cap.owner == "FactionA"

def test_full_conquest_logic():
    ctx = MockContext()
    manager = InvasionManager(ctx)
    planet, cap, city, waste = setup_mock_planet()
    ctx.planets[planet.name] = planet
    
    # Capture both
    manager.handle_conquest(city, "FactionB")
    manager.handle_conquest(cap, "FactionB")
    
    assert city.owner == "FactionB"
    assert cap.owner == "FactionB"
    assert planet.owner == "FactionB" # Should flip!

def test_raze_mechanic():
    ctx = MockContext()
    manager = InvasionManager(ctx)
    planet, cap, city, waste = setup_mock_planet()
    ctx.planets[planet.name] = planet
    
    faction_b = ctx.get_faction("FactionB")
    initial_req = faction_b.requisition
    
    # Raze the city
    manager.handle_conquest(city, "FactionB", decision="raze")
    
    assert city.owner == "FactionB"
    assert city.terrain_type == "Ruins"
    assert city.type == "Wasteland"
    assert len(city.buildings) == 0
    assert faction_b.requisition > initial_req # Loot gained
    
    # Check if planet flips if Capital is also taken (even if city is Ruins)
    manager.handle_conquest(cap, "FactionB")
    assert planet.owner == "FactionB"

def test_planet_stat_reduction_from_ruins():
    planet, cap, city, waste = setup_mock_planet()
    planet.owner = "FactionB"
    cap.owner = "FactionB"
    city.owner = "FactionB"
    
    # Before raze
    planet.recalc_stats()
    base_queue = planet.max_queue_size
    
    # Raze city
    city.terrain_type = "Ruins"
    
    # After raze
    planet.recalc_stats()
    assert planet.max_queue_size < base_queue # Queue size should drop because Ruins don't contribute
