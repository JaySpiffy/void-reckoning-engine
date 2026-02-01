import pytest
from unittest.mock import MagicMock
from src.managers.faction_manager import FactionManager
from src.models.faction import Faction

class TestFactionManager:
    @pytest.fixture
    def manager(self):
        return FactionManager(logger=MagicMock())

    @pytest.fixture
    def mock_factions(self):
        f1 = MagicMock(spec=Faction)
        f1.name = "Imperium"
        f1.is_alive = True
        
        f2 = MagicMock(spec=Faction)
        f2.name = "Chaos"
        f2.is_alive = True
        
        f3 = MagicMock(spec=Faction)
        f3.name = "Eldar_Dead"
        f3.is_alive = False
        
        return [f1, f2, f3]

    def test_initialization(self, manager):
        assert manager.factions == {}

    def test_register_faction(self, manager, mock_factions):
        for f in mock_factions:
            manager.register_faction(f)
        
        assert len(manager.factions) == 3
        assert "Imperium" in manager.factions
        assert manager.factions["Imperium"] == mock_factions[0]

    def test_get_faction(self, manager, mock_factions):
        manager.register_faction(mock_factions[0])
        f = manager.get_faction("Imperium")
        assert f == mock_factions[0]
        
        assert manager.get_faction("NonExistent") is None

    def test_get_living_factions(self, manager, mock_factions):
        for f in mock_factions:
            manager.register_faction(f)
            
        living = manager.get_living_factions()
        assert len(living) == 2
        assert mock_factions[0] in living
        assert mock_factions[1] in living
        assert mock_factions[2] not in living

    def test_clear(self, manager, mock_factions):
        manager.register_faction(mock_factions[0])
        assert len(manager.factions) == 1
        
        manager.clear()
        assert len(manager.factions) == 0
