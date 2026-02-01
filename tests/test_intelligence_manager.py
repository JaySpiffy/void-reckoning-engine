import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from src.managers.campaign_manager import CampaignEngine
from src.managers.intelligence_manager import IntelligenceManager

@pytest.fixture
def engine():
    config = {"simulation": {"seed": 12345}}
    # Use real CampaignEngine
    engine = CampaignEngine(game_config=config, universe_name="eternal_crusade")
    engine.logger = MagicMock()
    # [FIX] Add missing attributes
    engine.ai_manager = MagicMock()
    engine.galaxy_state = MagicMock()
    # Mock TechManager analyze_tech_tree
    engine.tech_manager = MagicMock()
    engine.tech_manager.analyze_tech_tree.return_value = {"OrkUnitTech": 1.5}
    
    # [FIX] Manual storage for factions and fleets
    from src.models.faction import Faction
    engine._test_factions = {
        "Zealot_Legions": Faction("Zealot_Legions"),
        "Scavenger_Clans": Faction("Scavenger_Clans")
    }
    engine._test_fleets = []
    
    # [FIX] Mock get_faction to return from our local dict
    # This is what attempt_blueprint_theft calls
    engine.get_faction = MagicMock(side_effect=lambda name: engine._test_factions.get(name))
    
    # Also mock get_all_factions for completeness
    engine.get_all_factions = MagicMock(return_value=list(engine._test_factions.values()))
    
    return engine

@pytest.fixture
def intel_mgr(engine):
    # [FIX] Use PropertyMock to patch read-only fleets and factions properties
    # We patch them on the INSTANCE types to ensure they are used
    with patch("src.managers.campaign_manager.CampaignEngine.factions", new_callable=PropertyMock) as mock_f, \
         patch("src.managers.campaign_manager.CampaignEngine.fleets", new_callable=PropertyMock) as mock_fleets:
        mock_f.return_value = engine._test_factions
        mock_fleets.return_value = engine._test_fleets
        yield IntelligenceManager(engine)

def test_intelligence_manager_initialization(intel_mgr):
    assert intel_mgr is not None
    assert intel_mgr._visibility_cache == {}

def test_clear_all_caches(intel_mgr):
    intel_mgr._visibility_cache["test"] = "data"
    intel_mgr.clear_visibility_cache()
    assert intel_mgr._visibility_cache == {}

@patch("src.utils.blueprint_registry.BlueprintRegistry")
def test_attempt_blueprint_theft_success(mock_blueprint_registry, intel_mgr, engine):
    f_name = "Zealot_Legions"
    target_f = "Scavenger_Clans"
    location = MagicMock()
    location.name = "GorkCity"
    location.is_sieged = False
    location.defense_level = 0
    
    f_obj = engine.get_faction(f_name)
    target_f_obj = engine.get_faction(target_f)
    
    assert f_obj is not None
    assert target_f_obj is not None
    
    f_obj.visible_planets = {"GorkCity"}
    f_obj.intel_points = 500
    # [FIX] Target must have unlocked_techs
    target_f_obj.unlocked_techs = ["OrkUnitTech"]
    
    mock_registry_inst = mock_blueprint_registry.get_instance.return_value
    # Mock get_blueprint to return a valid bp
    mock_registry_inst.get_blueprint.return_value = {
        "id": "OrkUnitTech",
        "name": "Ork Unit",
        "universal_stats": {"damage": 10.0},
        "default_traits": []
    }
    
    with patch("random.random", return_value=0.01), \
         patch("random.choices", return_value=["OrkUnitTech"]):
        # [PHASE 32] Direct check before call
        assert engine.get_faction("Scavenger_Clans") is not None
        
        success = intel_mgr.attempt_blueprint_theft(f_name, target_f, location, engine)
        assert success is True
        assert f_obj.intel_points == 300
        
        mock_registry_inst.register_blueprint.assert_called_once()
        kwargs = mock_registry_inst.register_blueprint.call_args[1]
        assert kwargs["faction_owner"] == f_name
        
        args = mock_registry_inst.register_blueprint.call_args[0]
        registered_bp = args[0]
        assert registered_bp["universal_stats"]["damage"] == 9.0

@patch("src.utils.blueprint_registry.BlueprintRegistry")
def test_attempt_blueprint_theft_failure(mock_blueprint_registry, intel_mgr, engine):
    f_name = "Zealot_Legions"
    target_f = "Scavenger_Clans"
    location = MagicMock()
    location.name = "GorkCity"
    location.is_sieged = False
    location.defense_level = 0
    
    f_obj = engine.get_faction(f_name)
    f_obj.visible_planets = {"GorkCity"}
    
    engine.diplomacy = MagicMock()
    engine.faction_reporter = MagicMock()
    
    with patch("random.random", return_value=0.99):
        success = intel_mgr.attempt_blueprint_theft(f_name, target_f, location, engine)
        # Should fail due to high random roll
        assert success is False

def test_intelligence_decay(intel_mgr, engine):
    f_name = "Zealot_Legions"
    planet_name = "Terra"
    f_obj = engine.get_faction(f_name)
    f_obj.intelligence_memory = {planet_name: {"last_seen_turn": 1, "threat": 2.0, "last_owner": "Scavenger_Clans"}}
    
    engine.turn_counter = 10
    _, _, _, threat, _ = intel_mgr.get_cached_intel(f_name, planet_name, 10)
    assert threat == 1.0

def test_calculate_target_score(intel_mgr, engine):
    planet_name = "Goal"
    planet = MagicMock()
    planet.name = planet_name
    planet.owner = "Scavenger_Clans"
    planet.income_req = 100
    planet.provinces = []
    planet.system.connections = [1, 2, 3]
    planet.system.x = 100
    planet.system.y = 100
    engine.get_planet = MagicMock(return_value=planet)
    engine.galaxy_state.planets = {planet_name: planet}
    with patch.object(intel_mgr, 'get_cached_intel', return_value=(1, 1000, 100, 1.0, "Scavenger_Clans")):
        score = intel_mgr.calculate_target_score(planet_name, "Zealot_Legions", 0, 0, (), (), None, "EXPANSION", 1)
        assert score > 0
        
def test_attempt_weapon_theft(intel_mgr):
    my_arsenal = {}
    target_arsenal = {"weapon_ork_choppa": {"id": "weapon_ork_choppa", "name": "Choppa", "stats": {"power": 50}}}
    with patch("random.random", return_value=0.01), \
         patch("random.choice", return_value=target_arsenal["weapon_ork_choppa"]):
        success = intel_mgr.attempt_weapon_theft("Zealot_Legions", "Scavenger_Clans", my_arsenal, target_arsenal)
        assert success is True
        assert any("stolen_weapon_ork_choppa" in k for k in my_arsenal.keys())
