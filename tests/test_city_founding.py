import pytest
from src.models.planet import Planet
from src.models.army import ArmyGroup
from src.models.unit import Unit
from src.factories.unit_factory import UnitFactory
from src.core.hex_lib import Hex

from src.core.universe_data import UniverseDataManager

class MockSystem:
    def __init__(self):
        self.name = "Test System"

class MockEngine:
    def __init__(self):
        self.turn_counter = 1
        self.factions = {}
        self.telemetry = None

@pytest.fixture(autouse=True)
def setup_universe_data():
    """Mocks UniverseDataManager to provide dummy planet classes."""
    instance = UniverseDataManager.get_instance()
    instance.game_data = {
        "planet_classes": {
            "Terran": {"req_mod": 1.0, "def_mod": 1, "slots": 5}
        }
    }
    return instance

def test_building_slots_defaults(setup_universe_data):
    system = MockSystem()
    planet = Planet("Terra", system, 3, base_req=1000)
    planet.planet_class = "Terran"
    planet.building_slots = 5 # Used to calculate hex map size
    
    # Trigger lazy generation
    provinces = planet.provinces
    
    capital = next(n for n in provinces if n.type == "Capital")
    prov_cap = next(n for n in provinces if n.type == "ProvinceCapital")
    lz = next(n for n in provinces if n.type == "LandingZone")
    
    assert capital.building_slots == 7
    assert prov_cap.building_slots == 5
    assert lz.building_slots == 3

def test_can_found_city(setup_universe_data):
    system = MockSystem()
    planet = Planet("Terra", system, 3)
    planet.planet_class = "Terran"
    planet.building_slots = 5
    
    # Find a standard province
    province = next(n for n in planet.provinces if n.type == "Province")
    assert province.can_found_city() is True
    
    # Check Wasteland/LZ
    lz = next(n for n in planet.provinces if n.type == "LandingZone")
    assert lz.can_found_city() is False
    
    # Check Capital
    capital = next(n for n in planet.provinces if n.type == "Capital")
    assert capital.can_found_city() is False

def test_found_city_mechanic(setup_universe_data):
    engine = MockEngine()
    system = MockSystem()
    planet = Planet("Terra", system, 3)
    planet.planet_class = "Terran"
    planet.building_slots = 5
    
    province = next(n for n in planet.provinces if n.type == "Province")
    
    # Create an army
    # We need to ensure UnitFactory doesn't crash too. 
    # UnitFactory.create_pdf is relatively self-contained.
    units = [UnitFactory.create_pdf("Regular", "Player") for _ in range(20)]
    army = ArmyGroup("Expeditionary_Force", "Player", units, province)
    
    # Found City
    success, msg = army.found_city(engine)
    
    assert success is True
    assert province.terrain_type == "City"
    assert province.type == "ProvinceCapital"
    assert province.building_slots == 5
    
    # Consumption check: max(10, 50% of 20) = 10. Left: 10
    assert len(army.units) == 10
    assert army.is_destroyed is False

def test_found_city_settler_trait(setup_universe_data):
    engine = MockEngine()
    system = MockSystem()
    planet = Planet("Terra", system, 3)
    planet.planet_class = "Terran"
    
    province = next(n for n in planet.provinces if n.type == "Province")
    
    # Create army with a "Settler"
    units = [UnitFactory.create_pdf("Regular", "Player") for _ in range(20)]
    units[0].traits.append("Settler")
    
    army = ArmyGroup("Colonist_Force", "Player", units, province)
    
    # Found City
    success, msg = army.found_city(engine)
    
    assert success is True
    # Consumption check (Settler trait): max(5, 25% of 20) = 5. Left: 15
    assert len(army.units) == 15

def test_planet_stat_refresh_after_founding(setup_universe_data):
    engine = MockEngine()
    system = MockSystem()
    planet = Planet("Terra", system, 3)
    planet.planet_class = "Terran"
    planet.owner = "Player"
    
    # Initial stats
    planet.recalc_stats()
    initial_queue = planet.max_queue_size
    initial_army_slots = planet.army_slots
    
    # Find two standard provinces
    provinces = [n for n in planet.provinces if n.type == "Province"]
    p1 = provinces[0]
    p2 = provinces[1]
    
    # Found first city
    army1 = ArmyGroup("Ex-1", "Player", [UnitFactory.create_pdf("Regular", "Player") for _ in range(20)], p1)
    army1.found_city(engine)
    
    # Found second city (army_slots += 0.5 + 0.5 = 1.0)
    army2 = ArmyGroup("Ex-2", "Player", [UnitFactory.create_pdf("Regular", "Player") for _ in range(20)], p2)
    army2.found_city(engine)
    
    # Final check
    assert planet.max_queue_size == initial_queue + 4 # 2 per ProvinceCapital
    assert planet.army_slots == initial_army_slots + 1 # 0.5 + 0.5 = 1.0
