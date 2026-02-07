import pytest
from unittest.mock import MagicMock, Mock, patch
from src.managers.ai_manager import StrategicAI
from src.models.planet import Planet
from src.models.fleet import Fleet
from src.core.interfaces import IEngine
from unittest.mock import mock_open as unittest_mock_open

def patch_open(*args, **kwargs):
    m = MagicMock()
    m.__enter__.return_value = MagicMock()
    return m

@pytest.fixture
def mock_engine():
    engine = MagicMock(spec=IEngine)
    engine.turn_counter = 1
    engine.factions = {}
    engine.planets_by_faction = {}
    engine.all_planets = []
    engine.fleets = []
    engine.telemetry = MagicMock()
    engine.logger = MagicMock()
    engine.diplomacy = MagicMock()
    engine.tech_manager = MagicMock()
    engine.intelligence_manager = MagicMock()
    engine.economy_manager = MagicMock()
    return engine

@pytest.fixture
def ai_manager(mock_engine):
    with patch("src.ai.strategies.standard._ai_rng", MagicMock()):
        # Pre-initialize sub-systems if needed, or let StrategicAI do it
        # But we want to mock components that StrategicAI creates
        ai = StrategicAI(mock_engine)
        
        # Mock sub-components that are initialized in __init__
        ai.tf_manager = MagicMock()
        ai.planner = MagicMock()
        ai.learning_engine = MagicMock()
        ai.personality_manager = MagicMock()
        ai.intelligence_coordinator = MagicMock()
        ai.tech_doctrine_manager = MagicMock()
        ai.target_scoring = MagicMock()
        
        # Mocking complex sub-systems initialized in __init__
        ai.proactive_diplomacy = MagicMock()
        ai.coalition_builder = MagicMock()
        ai.posture_manager = MagicMock()
        ai.economic_engine = MagicMock() # Added EconomicEngine mock
        
        return ai

def test_cache_management(ai_manager, mock_engine):
    """Test that turn cache builds and invalidates correctly."""
    mock_fleet = MagicMock(spec=Fleet)
    mock_fleet.faction = "Imperium"
    mock_fleet.is_destroyed = False
    mock_fleet.location = MagicMock()
    mock_fleet.location.name = "Terra"
    mock_fleet.destination = None
    mock_engine.fleets = [mock_fleet]
    
    ai_manager.build_turn_cache()
    assert len(ai_manager.turn_cache["fleets_by_loc"]) > 0
    assert ai_manager._last_cache_turn == mock_engine.turn_counter
    
    ai_manager.invalidate_turn_cache()
    assert len(ai_manager.turn_cache) == 0
    assert ai_manager._last_cache_turn == -1

def test_classify_defense_zones(ai_manager, mock_engine):
    """Test defense zone classification logic."""
    p1 = MagicMock(spec=Planet)
    p1.name = "Capital"
    p1.provinces = [MagicMock(type="Capital")]
    p1.owner = "Imperium"
    p1.system = MagicMock()
    p1.system.connections = []
    
    p2 = MagicMock(spec=Planet)
    p2.name = "Core"
    p2.provinces = []
    p2.owner = "Imperium"
    p2.system = MagicMock()
    p2.system.connections = []
    
    mock_engine.planets_by_faction = {"Imperium": [p1, p2]}
    
    zones = ai_manager.classify_defense_zones("Imperium")
    assert zones["Capital"] == "CAPITAL"
    assert zones["Core"] == "CORE"

def test_calculate_expansion_target_score(ai_manager):
    """Test delegation of expansion scoring."""
    ai_manager.calculate_expansion_target_score("Mars", "Imperium", 0, 0, "Expansionist", "STABLE", 10)
    ai_manager.target_scoring.calculate_expansion_target_score.assert_called_once()

def test_predict_enemy_threats(ai_manager, mock_engine):
    """Test threat prediction logic with visibility checks."""
    faction = "Imperium"
    f_mgr = MagicMock()
    f_mgr.visible_planets = {"Frontier"}
    mock_engine.factions = {faction: f_mgr}
    
    enemy_fleet = MagicMock(spec=Fleet)
    enemy_fleet.faction = "Orks"
    enemy_fleet.is_destroyed = False
    enemy_fleet.location = MagicMock()
    enemy_fleet.location.name = "Frontier" # Visible
    enemy_fleet.destination = MagicMock()
    enemy_fleet.destination.owner = faction
    enemy_fleet.route = [1, 2, 3] # ETA 3
    enemy_fleet.power = 500
    
    mock_engine.fleets = [enemy_fleet]
    ai_manager.build_turn_cache(force=True)
    
    threats = ai_manager.predict_enemy_threats(faction)
    assert len(threats) == 1
    assert threats[0]["eta"] == 3
    assert threats[0]["strength"] == 500

def test_share_intelligence(ai_manager, mock_engine):
    """Test intelligence sharing between allies."""
    f1_name, f2_name = "Imperium", "Eldar"
    f1_mgr = MagicMock()
    f1_mgr.known_planets = {"Terra", "Mars"}
    f1_mgr.intelligence_memory = {
        "OrkWorld": {"last_seen_turn": 1, "strength": 1000}
    }
    
    f2_mgr = MagicMock()
    f2_mgr.known_planets = {"Terra"}
    f2_mgr.intelligence_memory = {}
    
    mock_engine.factions = {f1_name: f1_mgr, f2_name: f2_mgr}
    mock_engine.turn_counter = 1
    
    # Setup alliance
    ai_manager.intelligence_coordinator.get_diplomatic_stance.return_value = "ALLIED"
    
    ai_manager.share_intelligence_with_allies(f1_name)
    
    # Eldar should now know about Mars and OrkWorld
    assert "Mars" in f2_mgr.known_planets
    assert "OrkWorld" in f2_mgr.intelligence_memory

@patch("src.factories.hull_mutation_factory.HullMutationFactory")
@patch("src.factories.weapon_factory.ProceduralWeaponFactory")
@patch("os.path.exists", return_value=True)
@patch("builtins.open", unittest_mock_open(read_data='{"base_hull": {"name": "Base"}}'))
@patch("json.load")
def test_innovation_cycle_hull(mock_json, mock_exists, mock_weapon, mock_hull, ai_manager, mock_engine):
    """Test that innovation cycle can trigger a hull mutation."""
    faction = "Imperium"
    f_obj = MagicMock()
    # Mocking as a real dict to avoid MagicMock auto-creation
    f_obj.custom_hulls = {}
    mock_engine.factions = {faction: f_obj}
    
    ai_manager.personality_manager.get_faction_dna.return_value = "dna_data"
    
    # Mock hull mutation
    mock_mutator = mock_hull.return_value
    mock_mutated_hull = {"id": "mutated_hull_1", "name": "Super Battleship"}
    mock_mutator.mutate_hull.return_value = mock_mutated_hull
    
    # Mock hull data loading
    mock_json.return_value = {"base_hull": {"name": "Base"}}
    
    with patch("random.random", return_value=0.1): # Trigger hull mutation
        ai_manager.process_innovation_cycle(faction)
    
    assert f_obj.custom_hulls["mutated_hull_1"] == mock_mutated_hull
    ai_manager.learning_engine.update_performance_metrics.assert_called_with(faction)

def test_process_turn_orchestration(ai_manager, mock_engine):
    """Test that process_turn calls expected sub-phases via StrategyOrchestrator."""
    from src.ai.management import StrategyOrchestrator
    orchestrator = StrategyOrchestrator(ai_manager)
    ai_manager.orchestrator = orchestrator # Put the real orchestrator in for this test
    
    mock_engine.factions = {"Imperium": MagicMock()}
    mock_engine.turn_counter = 25 # Trigger innovation
    
    # Mock the specialists to verify orchestrator calls them
    ai_manager.production_planner = MagicMock()
    ai_manager.expansion_logic = MagicMock()
    
    # We want to test that orchestrator calls the specialists
    ai_manager.process_turn()
    
    # Verify orchestrated calls
    ai_manager.production_planner.process_innovation_cycle.assert_called()
    ai_manager.intelligence_coordinator.process_espionage_decisions.assert_called()
    ai_manager.proactive_diplomacy.process_turn.assert_called()
    ai_manager.coalition_builder.process_turn.assert_called()
