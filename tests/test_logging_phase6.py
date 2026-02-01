import pytest
import json
from unittest.mock import MagicMock, patch, ANY
from src.combat.combat_tracker import CombatTracker
from src.managers.campaign_manager import CampaignEngine
from src.managers.turn_processor import TurnProcessor
from src.reporting.telemetry import EventCategory
from src.config import logging_config

@pytest.fixture
def mock_telemetry():
    return MagicMock()

@pytest.fixture
def mock_engine(mock_telemetry):
    engine = MagicMock(spec=CampaignEngine)
    engine.telemetry = mock_telemetry
    engine.turn_counter = 10
    engine.logger = MagicMock()
    # Add missing managers
    engine.economy_manager = MagicMock()
    engine.tech_manager = MagicMock()
    engine.battle_manager = MagicMock()
    engine.report_organizer = MagicMock() # Add missing report_organizer
    engine.report_organizer = MagicMock() # Add missing report_organizer
    engine.planets_by_faction = {} # Add missing planets_by_faction
    engine.faction_reporter = MagicMock() # Add missing faction_reporter
    engine.factions = {} # Add missing factions dict
    engine.fleets = [] # Add missing fleets list
    engine.config = MagicMock() # Add missing config
    engine.diplomacy = MagicMock() # Add missing diplomacy
    engine.stats_history = [] # Add missing stats_history
    engine.engine = engine # self-reference for AIManager
    
    # Mock initialization of get_all_factions to return empty list by default
    engine.get_all_factions.return_value = []
    
    return engine

def test_ai_decision_trace_integration(mock_engine):
    """Verifies that ai_decision_trace flag actually results in logs."""
    from src.ai.strategic_planner import StrategicPlanner
    from src.managers.ai_manager import StrategicAI
    
    mock_ai = MagicMock(spec=StrategicAI)
    mock_ai.engine = mock_engine
    
    with patch.dict(logging_config.LOGGING_FEATURES, {"ai_decision_trace": True}):
        # Mock TheaterManager class used inside StrategicPlanner
        with patch('src.ai.strategic_planner.TheaterManager') as MockTheaterManager:
            # Setup the mock instance returned by constructor
            mock_tm_instance = MockTheaterManager.return_value
            
            # Setup analyze_theaters return value
            theater = MagicMock()
            theater.id = "THEATER-1" 
            theater.doctrine = "PURITAN"
            mock_tm_instance.analyze_theaters.return_value = [theater]
            
            planner = StrategicPlanner(mock_ai)
            
            # Create a mock faction
            faction = MagicMock()
            faction.name = "TestFaction"
            
            # Ensure trace (including mock objects) is serializable by json.dumps
            # Since we can't easily make MagicMock json serializable, we'll patch json.dumps to just return string
            with patch('json.dumps', return_value='{}'):
                 # Create a strategic plan (this calls analyze_theaters and should log trace)
                 planner.create_plan(faction, MagicMock(planning_horizon=5), {})
            
            # Verify telemetry call
            # The logic logs 'ai_decision_trace' event
            # Note: The code calls logger.ai() manually in some branches, but _log_plan_execution also calls log_event
            # We are verifying 'ai_decision_trace' which is manually logged.
            # But wait, ai_decision_trace in the code calls `self.ai.engine.logger.ai(json.dumps(trace))` directly?
            # See src/ai/strategic_planner.py line 221. An event is DIFFERENT from logger.ai().
            # Let's check where 'ai_decision_trace' event is logged via telemetry.
            # It seems the code writes it to logger.ai, NOT telemetry.log_event directly?
            # Re-reading code in Step 7575: 
            # line 221: self.ai.engine.logger.ai(json.dumps(trace))
            # line 56: trace_enabled = logging_config.LOGGING_FEATURES.get('ai_decision_trace', False)
            # So it logs to LOGGER 'ai' category, not generic log_event?
            
            mock_engine.logger.ai.assert_called()

def test_tech_research_path_integration(mock_engine):
    """Verifies that tech_research_path_analysis flag results in logs."""
    from src.ai.economic_engine import EconomicEngine
    from src.managers.ai_manager import StrategicAI
    
    ai_mgr = MagicMock(spec=StrategicAI)
    ai_mgr.engine = mock_engine
    
    with patch.dict(logging_config.LOGGING_FEATURES, {"tech_research_path_analysis": True}):
        econ = EconomicEngine(ai_mgr)
        faction = MagicMock()
        faction.name = "TestFaction"
        faction.research_queue = []
        faction.unlocked_techs = []
        
        mock_engine.get_faction.return_value = faction
        mock_engine.tech_manager.get_available_research.return_value = [{"id": "Tech1", "cost": 1000}]
        
        econ.evaluate_research_priorities("TestFaction")
        
        # Verify research logger call (EconomicEngine uses engine.logger.research)
        mock_engine.logger.research.assert_called()
        # Verify message content
        log_msg = mock_engine.logger.research.call_args[0][0]
        assert "research_path_analysis" in log_msg

def test_combat_engagement_analysis_integration(mock_telemetry):
    """Verifies that combat_engagement_analysis flag results in logs in CombatTracker."""
    with patch.dict(logging_config.LOGGING_FEATURES, {"combat_engagement_analysis": True}):
        tracker = CombatTracker(telemetry_collector=mock_telemetry)
        
        faction_units = {
            "FactionA": [MagicMock()]
        }
        for u in faction_units["FactionA"]:
            u.is_alive.return_value = True
            u.name = "UnitA"
            u.cost = 100
            u.components = []
            
        tracker.finalize(
            winner="FactionA",
            rounds=5,
            faction_units=faction_units,
            battle_id="BATTLE-1",
            skip_save=True
        )
        
        mock_telemetry.log_event.assert_any_call(
            EventCategory.COMBAT,
            "combat_engagement_analysis",
            ANY,
            turn=None
        )

def test_faction_elimination_analysis_integration(mock_engine):
    """Verifies that faction_elimination_analysis flag results in logs in TurnProcessor."""
    with patch.dict(logging_config.LOGGING_FEATURES, {"faction_elimination_analysis": True}):
        processor = TurnProcessor(mock_engine)
        
        faction_alive = MagicMock()
        faction_alive.name = "AliveFaction"
        faction_alive.is_alive = True
        
        faction_dead = MagicMock()
        faction_dead.name = "DeadFaction"
        faction_dead.is_alive = True # Starts alive
        
        mock_engine.get_all_factions.return_value = [faction_alive, faction_dead]
        
        # Mock process_faction_turn to kill DeadFaction
        def kill_faction(f_name, **kwargs):
            if f_name == "DeadFaction":
                faction_dead.is_alive = False
        
        with patch.object(processor, 'process_faction_turn', side_effect=kill_faction):
            # Patch dependencies of process_turn to avoid side effects
            mock_engine.check_victory_conditions.return_value = None
            
            # Run the method
            processor.process_turn()
            
            # Verify elimination log
            # The logic refers to engine._log_faction_elimination(f_name)
            mock_engine._log_faction_elimination.assert_called_with("DeadFaction")

def test_logging_feature_disabled(mock_engine):
    """Ensures that when a flag is False, no log event is generated."""
    from src.ai.economic_engine import EconomicEngine
    from src.managers.ai_manager import StrategicAI
    
    ai_mgr = MagicMock(spec=StrategicAI)
    ai_mgr.engine = mock_engine
    
    with patch.dict(logging_config.LOGGING_FEATURES, {"tech_research_path_analysis": False}):
        econ = EconomicEngine(ai_mgr)
        faction = MagicMock()
        faction.name = "TestFaction"
        faction.research_queue = []
        
        mock_engine.get_faction.return_value = faction
        mock_engine.tech_manager.get_available_research.return_value = [{"id": "Tech1", "cost": 1000}]
        
        econ.evaluate_research_priorities("TestFaction")
        
        # Verify research logger was NOT called
        mock_engine.logger.research.assert_not_called()
