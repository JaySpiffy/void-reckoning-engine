import pytest
from unittest.mock import MagicMock, call, patch
from src.managers.turn_processor import TurnProcessor

# --- Fixtures ---

@pytest.fixture
def mock_engine(eternal_crusade_universe):
    engine = MagicMock()
    engine.turn_counter = 5
    engine.all_planets = []
    engine.stats_history = []
    
    # Mock helpers
    imperium = MagicMock()
    imperium.name = "Imperium"
    imperium.is_alive = True
    neutral = MagicMock()
    neutral.name = "Neutral"
    neutral.is_alive = True
    
    engine.factions = {"Imperium": imperium, "Neutral": neutral}
    engine.get_all_factions.return_value = [imperium, neutral]
    engine.fleets = []
    
    # Sub-managers
    engine.economy_manager = MagicMock()
    engine.battle_manager = MagicMock()
    engine.diplomacy = MagicMock()
    engine.intel_manager = MagicMock()
    engine.strategic_ai = MagicMock()
    engine.storm_manager = MagicMock()
    engine.faction_reporter = MagicMock()
    engine.report_organizer = MagicMock()
    engine.telemetry = MagicMock()
    engine.logger = MagicMock()
    
    # Config
    engine.config = MagicMock()
    engine.config.performance_log_interval = 100
    
    return engine

@pytest.fixture
def turn_processor(mock_engine):
    return TurnProcessor(mock_engine)

# --- Tests ---

def test_process_turn_lifecycle(turn_processor, mock_engine):
    """Verify the orchestration sequence of a full turn."""
    # Setup
    mock_engine.turn_counter = 10 
    
    turn_processor.process_faction_turns()
    
    # Verify Economy Pre-calculcation call
    mock_engine.economy_manager.resource_handler.precalculate_economics.assert_called_once()
    
    # Verify Faction Turn Processing (Imperium, not Neutral)
    mock_engine.economy_manager.process_faction_economy.assert_called_with("Imperium")

    
    # Verify Cleanup
    # Telemetry flush at turn 10 (modulo 10)
    assert mock_engine.telemetry.flush.call_count >= 1

def test_process_faction_turn_structure(turn_processor, mock_engine):
    """Verify the events within a single faction's turn."""
    f_name = "Imperium"
    
    # Setup Fleet for movement logic
    fleet = MagicMock()
    fleet.faction = f_name
    fleet.is_destroyed = False
    fleet.destination = None
    fleet.location = MagicMock()
    
    mock_engine.fleets = [fleet]
    mock_engine.default_strategy = MagicMock()
    mock_engine.strategies = {f_name: MagicMock()}
    
    # Execute
    turn_processor.process_faction_turn(f_name)
    
    # 1. Update Visibility
    mock_engine.intel_manager.update_faction_visibility.assert_any_call(f_name)
    
    # 2. Strategy & Economy
    mock_engine.strategic_ai.process_faction_strategy.assert_called_with(f_name)
    mock_engine.economy_manager.process_faction_economy.assert_called_with(f_name)
    
    # 3. Fleet Logic (Movement)
    fleet.update_movement.assert_called_once()
    
    # 4. Reinforcements
    strategy = mock_engine.strategies[f_name]
    strategy.process_reinforcements.assert_called_with(f_name, mock_engine)

def test_cleanup_destroyed_fleets(turn_processor, mock_engine):
    """Verify destroyed fleets are unregistered during global cleanup."""
    # Setup destroyed fleet
    live_fleet = MagicMock()
    live_fleet.is_destroyed = False
    
    dead_fleet = MagicMock()
    dead_fleet.is_destroyed = True
    dead_fleet.units = MagicMock()
    dead_fleet.cargo_armies = MagicMock()
    
    mock_engine.fleets = [live_fleet, dead_fleet]
    
    # Run turns
    turn_processor.process_faction_turns()
    
    # Verify dead fleet cleanup
    dead_fleet.units.clear.assert_called_once()
    dead_fleet.cargo_armies.clear.assert_called_once()
    mock_engine.unregister_fleet.assert_called_with(dead_fleet)
    
    # Live fleet untouched
    assert live_fleet in mock_engine.fleets # Note: process_turn implementation iterates copy or modifying list?
    # TurnProcessor: destroyed = [f for f in self.engine.fleets if f.is_destroyed]
    # It calls engine.unregister_fleet(f). Minimal Engine mock doesn't actually remove from list unless we make it.
    
def test_analytics_flush(turn_processor, mock_engine):
    """Verify analytics are flushed when history buffer is full."""
    mock_engine.stats_history = [{"Turn": i} for i in range(110)] # Limit is 100
    mock_engine.report_organizer.run_path = "test_run"
    mock_engine.report_organizer.run_id = "001"
    
    with patch("builtins.open", MagicMock()) as mock_file:
        turn_processor.flush_analytics("test_dir", "001")
        
        # Verify file write
        mock_file.assert_called()
        # Verify history clear
        assert len(mock_engine.stats_history) == 0

