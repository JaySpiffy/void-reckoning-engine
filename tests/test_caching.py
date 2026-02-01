import pytest
from unittest.mock import MagicMock
from src.models.fleet import Fleet
from src.models.unit import Unit
from src.models.army import ArmyGroup

# --- Fixtures ---

@pytest.fixture
def mock_unit():
    u = MagicMock(spec=Unit)
    u.abilities = {"Tags": ["Infantry"]} # Default size
    return u

@pytest.fixture
def mock_army_group(mock_unit):
    ag = MagicMock(spec=ArmyGroup)
    ag.units = [mock_unit]
    return ag

@pytest.fixture
def fleet():
    f = Fleet("TestFleet", "Imperium", MagicMock())
    return f

# --- Tests ---

def test_fleet_capacity_invalidation(fleet, mock_army_group):
    """
    Test that modifying fleet cargo invalidates the used capacity cache.
    """
    # 1. Embark ArmyGroup (simulated)
    fleet.cargo_armies.append(mock_army_group)
    fleet.invalidate_caches()
    
    # Check capacity (1 unit, default size = 1)
    assert fleet.used_capacity == 1
    assert fleet._used_capacity_dirty == False
    
    # 2. Modify composition (Add another army group)
    fleet.cargo_armies.append(mock_army_group)
    fleet.invalidate_caches()
    
    # 3. Verify Recalculation
    assert fleet._used_capacity_dirty == True # Set by invalidate
    assert fleet.used_capacity == 2

def test_transport_capacity_update(fleet):
    """Verify transport capacity updates when ships are added."""
    # Add a ship with transport capacity
    ship_template = MagicMock(spec=Unit)
    ship_template.name = "TransportShip"
    ship_template.is_ship.return_value = True
    ship_template.transport_capacity = 10
    ship_template.cost = 100
    ship_template.ma = 3
    ship_template.md = 3
    ship_template.defense = 3
    ship_template.current_hp = 100
    ship_template.armor = 10
    ship_template.attack = 2
    ship_template.damage = 1
    ship_template.authentic_weapons = []
    ship_template.rank = 0
    ship_template.shield_max = 0
    ship_template.traits = []
    ship_template.abilities = {}
    
    fleet.add_unit(ship_template)
    
    assert fleet.transport_capacity == 10

def test_economy_manager_cache_clearing():
    """Verify EconomyManager clears its specific caches."""
    from src.managers.economy_manager import EconomyManager
    
    engine = MagicMock()
    engine.game_config = {"simulation": {}, "mechanics": {}}
    
    em = EconomyManager(engine)
    em.faction_econ_cache = {"Imperium": {"data": 1}}
    
    em.clear_caches()
    assert len(em.faction_econ_cache) == 0
