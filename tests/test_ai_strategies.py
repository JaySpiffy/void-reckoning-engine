import pytest
from unittest.mock import MagicMock, Mock, patch
from src.ai.strategies.economic_strategy import EconomicStrategy
from src.ai.strategies.standard import StandardStrategy
from src.models.planet import Planet
from src.models.fleet import Fleet

@pytest.fixture
def economic_setup():
    mock_ai = Mock()
    strategy = EconomicStrategy(mock_ai)
    return strategy, mock_ai

def test_bankruptcy_halts_mustering(economic_setup):
    strategy, mock_ai = economic_setup
    # Setup
    mock_tf = Mock()
    mock_tf.state = "MUSTERING"
    mock_tf.is_raid = False
    
    mock_ai.task_forces = {"Imperium": [mock_tf]}
    
    # Execute
    strategy.handle_economic_restraint("Imperium", "BANKRUPT")
    
    # Verify
    assert mock_tf.state == "IDLE"
    assert mock_tf.target is None

def test_bankruptcy_allows_raids(economic_setup):
    strategy, mock_ai = economic_setup
    # Setup
    mock_tf = Mock()
    mock_tf.state = "MUSTERING"
    mock_tf.is_raid = True
    
    mock_ai.task_forces = {"Imperium": [mock_tf]}
    
    # Execute
    strategy.handle_economic_restraint("Imperium", "BANKRUPT")
    
    # Verify
    assert mock_tf.state == "MUSTERING"  # Should not change

@pytest.fixture
def standard_setup():
    strategy = StandardStrategy()
    mock_engine = Mock()
    mock_fleet = Mock()
    mock_fleet.id = "f1"
    mock_fleet.faction = "Imperium"
    
    # Mock Faction Manager via Engine Proxy
    mock_f_mgr = Mock()
    mock_f_mgr.requisition = 1000
    mock_f_mgr.known_planets = {"PlanetA", "PlanetB"}
    mock_f_mgr.visible_planets = {"PlanetA"}
    mock_engine.factions = {"Imperium": mock_f_mgr}
    mock_f_mgr.active_strategic_plan = None # Default to None to avoid Mock iteration issues
    
    # Mock Intel Manager
    mock_engine.intel_manager = Mock()
    mock_engine.intel_manager.get_theater_power.return_value = {"Imperium": 100, "Orks": 50}
    mock_engine.intel_manager.calculate_threat_level.return_value = 0.5
    mock_engine.intel_manager.get_cached_intel.return_value = (10, 0, 0, 0.5) # last_seen, str, def, threat
    mock_engine.intel_manager.calculate_target_score.return_value = 10.0
    mock_engine.intel_manager._is_hostile_target.return_value = True
    mock_engine.turn_counter = 12

    # Mock Planets
    p_a = Mock(spec=Planet)
    p_a.name = "PlanetA"
    p_a.owner = "Neutral"
    p_a.income_req = 10
    
    p_b = Mock(spec=Planet)
    p_b.name = "PlanetB"
    p_b.owner = "Orks"
    p_b.income_req = 20
    
    mock_engine.all_planets = [p_a, p_b]
    mock_engine.planets_by_faction = {"Imperium": []}
    
    return strategy, mock_engine, mock_fleet, p_a, p_b

def test_emergency_retreat(standard_setup):
    strategy, mock_engine, mock_fleet, p_a, p_b = standard_setup
    # Overwhelming enemy power
    mock_engine.intel_manager.get_theater_power.return_value = {"Imperium": 100, "Orks": 300}
    
    home_planet = Mock(spec=Planet)
    home_planet.name = "Terra"
    mock_engine.planets_by_faction = {"Imperium": [home_planet]}
    
    target = strategy.choose_target(mock_fleet, mock_engine)
    assert target == home_planet

@patch('src.ai.strategies.standard._ai_rng')
def test_local_expansion(mock_rng, standard_setup):
    strategy, mock_engine, mock_fleet, p_a, p_b = standard_setup
    # Setup fleet location
    mock_fleet.location.system.planets = [p_a]
    mock_fleet.location.system.connections = []
    
    # Expansion candidate
    mock_engine.game_config.get.return_value = {} # Default config
    
    # ensure is_safe returns True
    mock_engine.intel_manager.calculate_threat_level.return_value = 0.1
    
    # Select p_a as target
    mock_rng.random.return_value = 0.0 # Force expansion logic if present
    mock_rng.uniform.return_value = 5.0 # Return a valid float for weighted choice
    
    target = strategy.choose_target(mock_fleet, mock_engine)
    assert target == p_a
