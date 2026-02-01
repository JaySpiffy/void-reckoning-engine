import pytest
from unittest.mock import MagicMock, patch, call
from src.managers.turn_processor import TurnProcessor
from src.managers.campaign_manager import CampaignEngine
from src.managers.turn_processor import TurnProcessor

@pytest.fixture
def mock_engine():
    engine = MagicMock(spec=CampaignEngine)
    engine.turn_counter = 50
    engine.logger = MagicMock()
    engine.factions = {}
    engine.fleets = []
    
    # KNOWN ISSUE: TurnProcessor needs fleet_manager attribute
    # This is a production code change requiring test updates
    engine.fleet_manager = MagicMock()
    
    # Mock sub-managers
    engine.economy_manager = MagicMock()
    engine.battle_manager = MagicMock()
    engine.battle_manager.active_battles = []
    engine.intel_manager = MagicMock()
    engine.strategic_ai = MagicMock()
    engine.action_reporter = MagicMock()
    engine.construction_service = MagicMock()
    engine.storm_manager = MagicMock()
    engine.diplomacy = MagicMock()
    engine.telemetry = MagicMock()
    engine.config = MagicMock()
    engine.config.performance_log_interval = 5
    engine.config.max_fleet_size = 10
    
    # Additional engine attributes needed by TurnProcessor
    engine.report_organizer = MagicMock()
    engine.faction_reporter = MagicMock()
    engine.all_planets = []
    engine.systems = []
    engine.stats_history = []
    engine.strategies = {}
    engine.default_strategy = MagicMock()
    
    # Mock methods
    engine.get_all_factions.return_value = []
    engine.get_faction.return_value = MagicMock()
    engine.get_all_fleets.return_value = []
    engine.get_all_planets.return_value = []
    engine.prune_empty_armies = MagicMock()
    engine.clear_turn_caches = MagicMock()
    engine.rebuild_planet_indices = MagicMock()
    engine.unregister_fleet = MagicMock()
    engine.detect_narrative_turning_points = MagicMock()
    engine.log_performance_metrics = MagicMock()
    engine.check_victory_conditions = MagicMock(return_value=None)
    
    return engine

@pytest.fixture
def turn_processor(mock_engine):
    return TurnProcessor(mock_engine)

def test_process_turn_global(turn_processor, mock_engine):
    """Test global phase execution in process_turn."""
    # Setup some factions
    f1 = MagicMock()
    f1.name = "Imperium"
    f1.requisition = 1000
    f1.reset_turn_stats = MagicMock()
    
    f2 = MagicMock()
    f2.name = "Orks"
    f2.requisition = 1000
    f2.reset_turn_stats = MagicMock()
    
    mock_engine.get_all_factions.return_value = [f1, f2]
    
    # Process turn
    turn_processor.process_turn()
    
    # Verify global calls
    mock_engine.prune_empty_armies.assert_called_once()
    mock_engine.clear_turn_caches.assert_called_once()
    mock_engine.economy_manager.clear_caches.assert_called_once()
    mock_engine.rebuild_planet_indices.assert_called_once()
    f1.reset_turn_stats.assert_called()
    f2.reset_turn_stats.assert_called()

def test_process_faction_turn(turn_processor, mock_engine):
    """Test individual faction turn processing."""
    faction = MagicMock()
    faction.name = "Imperium"
    faction.requisition = 1000
    faction.reset_turn_stats = MagicMock()
    
    mock_engine.get_all_factions.return_value = [faction]
    
    # Process turn
    turn_processor.process_turn()
    
    # Verify faction-specific calls
    faction.reset_turn_stats.assert_called_once()

def test_fleet_arrival_logic(turn_processor, mock_engine):
    """Test fleet arrival and consolidation logic."""
    # Setup
    f1 = MagicMock()
    f1.name = "Imperium"
    f1.requisition = 1000
    f1.reset_turn_stats = MagicMock()
    
    f2 = MagicMock()
    f2.name = "Orks"
    f2.requisition = 1000
    f2.reset_turn_stats = MagicMock()
    
    mock_engine.get_all_factions.return_value = [f1, f2]
    
    # Process turn
    turn_processor.process_turn()
    
    # Verify fleet arrival logic - called once per faction
    assert mock_engine.fleet_manager.consolidate_fleets.call_count == 2

def test_analytics_flush(turn_processor, mock_engine):
    """Test analytics data flushing."""
    # Process turn first
    turn_processor.process_turn()
    # Verify telemetry.flush was called (not analytics_flush)
    mock_engine.telemetry.flush.assert_called()

def test_cleanup_destroyed_fleets(turn_processor, mock_engine):
    """Test cleanup of destroyed fleets."""
    # Setup - create a destroyed fleet
    destroyed_fleet = MagicMock()
    destroyed_fleet.is_destroyed = True
    destroyed_fleet.location = MagicMock()
    destroyed_fleet.units = MagicMock()
    destroyed_fleet.cargo_armies = MagicMock()
    destroyed_fleet.destination = MagicMock()
    
    # Setup faction
    f1 = MagicMock()
    f1.name = "Imperium"
    f1.is_destroyed = False
    
    mock_engine.get_all_factions.return_value = [f1]
    mock_engine.fleets = [destroyed_fleet]
    
    # Process turn
    turn_processor.process_turn()
    
    # Verify destroyed fleet cleanup
    mock_engine.unregister_fleet.assert_called_once_with(destroyed_fleet)
