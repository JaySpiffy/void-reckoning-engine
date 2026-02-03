
import pytest
from unittest.mock import MagicMock
from src.services.recruitment_service import RecruitmentService

class MockBlueprint:
    def __init__(self, name, unit_class, cost, tier=1):
        self.name = name
        self.unit_class = unit_class
        self.cost = cost
        self.tier = tier
        self.abilities = {"Tags": []}
    
    def is_ship(self):
        return False

@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.tech_manager.calculate_tech_tree_depth.return_value = {"tier_breakdown": {1: 1, 2: 1, 3: 1, 4: 1}}
    return engine

def test_army_blueprint_unlocks(mock_engine):
    service = RecruitmentService(mock_engine)
    
    faction_mgr = MagicMock()
    faction_mgr.unlocked_techs = set()
    
    # Create blueprints
    basic_inf = MockBlueprint("Guardians", "line_infantry", 100)
    assault_marines = MockBlueprint("Assault Marines", "assault_marines", 1000, tier=2)
    titan = MockBlueprint("Warlord", "war_titan", 10000, tier=4)
    
    mock_engine.army_blueprints = {"Aurelian_Hegemony": [basic_inf, assault_marines, titan]}
    mock_engine.get_faction.return_value = faction_mgr
    
    # Test 1: Only basic infantry available initially (Tier 1 has no unlock_tech)
    available = service._get_available_army_blueprints("Aurelian_Hegemony", faction_mgr)
    available_names = [bp.name for bp in available]
    
    assert "Guardians" in available_names
    assert "Assault Marines" not in available_names
    assert "Warlord" not in available_names
    
    # Test 2: Unlock Elite Infantry
    faction_mgr.unlocked_techs.add("Tech_Unlock_Elite_Infantry")
    available = service._get_available_army_blueprints("Aurelian_Hegemony", faction_mgr)
    available_names = [bp.name for bp in available]
    
    assert "Guardians" in available_names
    assert "Assault Marines" in available_names
    assert "Warlord" not in available_names
    
    # Test 3: Unlock Titan Engine
    faction_mgr.unlocked_techs.add("Tech_Unlock_Titan_Engine")
    available = service._get_available_army_blueprints("Aurelian_Hegemony", faction_mgr)
    available_names = [bp.name for bp in available]
    
    assert "Warlord" in available_names
