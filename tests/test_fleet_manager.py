import pytest
from unittest.mock import MagicMock
from src.managers.fleet_manager import FleetManager

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def fleet_mgr(mock_engine):
    return FleetManager(mock_engine)

@pytest.fixture
def mock_fleet():
    fleet = MagicMock()
    fleet.faction = "Imperium"
    fleet.is_destroyed = False
    return fleet

def test_add_fleet(fleet_mgr, mock_fleet):
    """Verify fleet is added to master list and faction index."""
    fleet_mgr.add_fleet(mock_fleet)
    
    assert mock_fleet in fleet_mgr.fleets
    assert mock_fleet in fleet_mgr.fleets_by_faction["Imperium"]
    # Verify engine injection
    assert mock_fleet.engine == fleet_mgr.engine

def test_remove_fleet(fleet_mgr, mock_fleet):
    """Verify fleet is removed correctly."""
    fleet_mgr.add_fleet(mock_fleet)
    fleet_mgr.remove_fleet(mock_fleet)
    
    assert mock_fleet not in fleet_mgr.fleets
    assert mock_fleet not in fleet_mgr.fleets_by_faction["Imperium"]

def test_get_fleets_by_faction_filtering(fleet_mgr):
    """Verify get_fleets_by_faction filters destroyed fleets."""
    f1 = MagicMock()
    f1.faction = "Eldar"
    f1.is_destroyed = False
    
    f2 = MagicMock()
    f2.faction = "Eldar"
    f2.is_destroyed = True # Should be filtered
    
    f3 = MagicMock()
    f3.faction = "Orks" # Wrong faction
    f3.is_destroyed = False
    
    fleet_mgr.add_fleet(f1)
    fleet_mgr.add_fleet(f2)
    fleet_mgr.add_fleet(f3)
    
    eldar_fleets = fleet_mgr.get_fleets_by_faction("Eldar")
    
    assert f1 in eldar_fleets
    assert f2 not in eldar_fleets
    assert f3 not in eldar_fleets
    assert len(eldar_fleets) == 1

def test_duplicate_add_prevention(fleet_mgr, mock_fleet):
    """Verify adding same fleet twice doesn't duplicate entries."""
    fleet_mgr.add_fleet(mock_fleet)
    fleet_mgr.add_fleet(mock_fleet)
    
    assert len(fleet_mgr.fleets) == 1
    assert len(fleet_mgr.fleets_by_faction["Imperium"]) == 1
