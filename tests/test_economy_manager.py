import pytest
from unittest.mock import MagicMock, patch
from src.managers.campaign_manager import CampaignEngine
from src.managers.economy_manager import EconomyManager

@pytest.fixture
def engine():
    config = {
        "simulation": {"seed": 12345, "ai_update_interval": 1},
        "mechanics": {
            "enable_diplomacy": False,
            "ai_economy": {
                "modes": [
                    # [FIX] Use condition_type to match implementation
                    {"name": "WAR", "threshold": 0.5, "condition_type": "losing", "budget": {"recruitment": 0.6, "construction": 0.2, "research": 0.2}}
                ]
            }
        }
    }
    # Use real CampaignEngine but mock out heavy components
    engine = CampaignEngine(game_config=config, universe_name="eternal_crusade")
    engine.resource_handler = MagicMock()
    engine.budget_allocator = MagicMock()
    engine.insolvency_handler = MagicMock()
    engine.tech_manager = MagicMock()
    engine.construction_service = MagicMock()
    engine.telemetry = MagicMock()
    engine.telemetry.faction_stats_cache = {}
    engine.telemetry.metrics = MagicMock()
    return engine

@pytest.fixture
def economy_mgr(engine):
    # Patch the components that EconomyManager initializes in its __init__
    with patch('src.managers.economy_manager.ResourceHandler', return_value=engine.resource_handler), \
         patch('src.managers.economy_manager.BudgetAllocator', return_value=engine.budget_allocator), \
         patch('src.managers.economy_manager.InsolvencyHandler', return_value=engine.insolvency_handler), \
         patch('src.managers.economy_manager.RecruitmentService'), \
         patch('src.managers.economy_manager.ConstructionService', return_value=engine.construction_service):
        mgr = EconomyManager(engine)
        return mgr

def test_economy_manager_initialization(economy_mgr):
    assert economy_mgr is not None

def test_process_economy_flow(economy_mgr, engine):
    from src.models.faction import Faction
    engine.faction_manager.factions = {"Zealot_Legions": Faction("Zealot_Legions"), "Scavenger_Clans": Faction("Scavenger_Clans")}
    
    # We need to simulate the cache being populated or returning something
    economy_mgr.faction_econ_cache = {
        "Zealot_Legions": {"income": 100, "total_upkeep": 50},
        "Scavenger_Clans": {"income": 50, "total_upkeep": 100}
    }
    
    with patch.object(economy_mgr, 'process_faction_economy') as mock_process:
        economy_mgr.process_economy()
        assert mock_process.call_count == 2

def test_process_faction_economy_healthy(economy_mgr, engine):
    f_name = "Zealot_Legions"
    from src.models.faction import Faction
    f_obj = Faction(f_name)
    f_obj.requisition = 1000
    engine.faction_manager.register_faction(f_obj)
    
    cached_econ = {
        "income": 1000,
        "total_upkeep": 500
    }
    
    economy_mgr.process_faction_economy(f_name, cached_econ)
    # Budget execution should be called
    economy_mgr.budget_allocator.execute_budget.assert_called_once()

def test_process_faction_economy_insolvent(economy_mgr, engine):
    f_name = "Scavenger_Clans"
    from src.models.faction import Faction
    f_obj = Faction(f_name)
    f_obj.requisition = -100 # Insolvent
    engine.faction_manager.register_faction(f_obj)
    
    cached_econ = {
        "income": 100,
        "total_upkeep": 500
    }
    
    economy_mgr.process_faction_economy(f_name, cached_econ)
    # handle_insolvency should be called
    economy_mgr.insolvency_handler.handle_insolvency.assert_called_once()

def test_hydrate_cached_econ_war(economy_mgr):
    from src.models.faction import Faction
    mock_faction = Faction("Zealot_Legions")
    mock_faction.requisition = 5000
    
    cached_any = {
        "income": 1000, 
        "total_upkeep": 5000, # margin 0.2 < threshold 0.5
        "income_by_category": {},
        "research_income": 100,
        "military_upkeep": 300,
        "infrastructure_upkeep": 200
    }
    
    result = economy_mgr._hydrate_cached_econ("Zealot_Legions", cached_any, mock_faction)
    assert result["active_mode"]["name"] == "WAR"
    assert result["income"] == 1000

def test_telemetry_recording(economy_mgr, engine):
    f_name = "Zealot_Legions"
    from src.models.faction import Faction
    f_obj = Faction(f_name)
    f_obj.unlocked_techs = {"Tech1"}
    engine.faction_manager.register_faction(f_obj)
    engine.tech_manager.calculate_tech_tree_depth.return_value = 5
    
    engine.telemetry.faction_stats_cache = {}
    engine.telemetry.metrics.get_live_metrics.return_value = {}
    
    economy_mgr.process_faction_economy(f_name, cached_econ={"income": 100, "total_upkeep": 50})
    assert f_name in engine.telemetry.faction_stats_cache
    assert engine.telemetry.faction_stats_cache[f_name]["tech_depth"] == 5

def test_performance_metric_sync(economy_mgr):
    economy_mgr.insolvency_handler.perf_metrics = {
        "insolvency_time": 0.5,
        "disbanded_count": 1
    }
    economy_mgr.perf_metrics["insolvency_time"] = 0.0
    economy_mgr.perf_metrics["disbanded_count"] = 0
    
    with patch.object(economy_mgr.resource_handler, 'precalculate_economics', return_value={}):
        economy_mgr.process_economy()
        
    assert economy_mgr.perf_metrics["insolvency_time"] == 0.5
    assert economy_mgr.perf_metrics["disbanded_count"] == 1
