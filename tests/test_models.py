from src.core.constants import PLANET_CLASSES, BUILDING_DATABASE
import pytest
from unittest.mock import MagicMock, patch
from src.models.planet import Planet
from src.models.faction import Faction
from src.models.unit import Unit

# --- Fixtures ---

@pytest.fixture
def faction(eternal_crusade_universe):
    f = Faction("Imperium")
    f.requisition = 1000
    f.unlocked_techs = ["BolterDirill"]
    return f

@pytest.fixture
def mock_universe_data():
    with patch("src.models.planet.UniverseDataManager") as mock_udm:
        instance = mock_udm.get_instance.return_value
        # Mock planet classes
        instance.get_planet_classes.return_value = {
            "Terran": {"req_mod": 1.0, "def_mod": 1, "slots": 5},
            "Desert": {"req_mod": 0.8, "def_mod": 0, "slots": 4},
            "Hive":   {"req_mod": 2.0, "def_mod": 2, "slots": 8}
        }
        # Mock building database so generate_resources doesn't crash on building generation/lookup
        instance.get_building_database.return_value = {}
        yield instance

@pytest.fixture
def planet(mock_universe_data):
    # Needs system mock?
    sys = MagicMock()
    # Force planet class to allow deterministic assert
    with patch("random.choice", return_value="Terran"):
        p = Planet("TestWorld", sys, 3, base_req=500)
    return p

# --- Tests ---

def test_faction_economy(faction):
    """
    Test basic faction economy methods.
    """
    assert faction.can_afford(500)
    assert not faction.can_afford(1500)
    
    faction.deduct_cost(200)
    assert faction.requisition == 800
    
    # Test tracking
    assert faction.stats["turn_req_expense"] == 200

def test_faction_tech(faction):
    """
    Test tech unlocking check.
    """
    assert faction.has_tech("BolterDirill")
    assert not faction.has_tech("PlasmaTech")

def test_planet_initialization(planet):
    """
    Test that planet stats are derived from class.
    """
    # Verify planet class derived inputs
    assert planet.planet_class == "Terran"
    
    # Base 500 * 1.0 = 500
    assert planet.income_req == 500
    assert planet.building_slots == 5
    assert planet.defense_level == 1

def test_planet_garrison_spawn(planet):
    """
    Test garrison generation.
    """
    planet.defense_level = 2
    garrison = planet.spawn_garrison("Imperium", max_count=10)
    
    assert len(garrison) > 0
    assert len(garrison) <= 10
    assert all(isinstance(u, Unit) for u in garrison)
    assert all(u.faction == "Imperium" for u in garrison)

def test_planet_income_calculation(planet):
    """
    Test income generation including modifiers (siege).
    """
    base_income = planet.income_req
    
    # Normal
    res = planet.generate_resources()
    assert res["req"] == base_income
    
    # Sieged
    planet.is_sieged = True
    res_sieged = planet.generate_resources()
    assert res_sieged["req"] == int(base_income * 0.5)
