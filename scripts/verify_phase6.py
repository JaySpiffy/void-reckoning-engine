
import os
import sys
import logging
from src.utils.logging import GameLogger
from src.reporting.telemetry import TelemetryCollector, EventCategory
# Import config directly to manipulate it for testing
from src.config import logging_config 

def verify_logging_foundation():
    print("--- Phase 6 Logging Foundation Verification ---")
    
    # Setup
    log_dir = "logs_test_phase6"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logger = GameLogger(log_dir=log_dir, console_verbose=True)
    
    # 1. Test Default Configuration (Should be OFF)
    print("\n[TEST 1] Default Configuration (Expect NO logs for new categories)")
    print(f"DEBUG: ai_decision_trace flag is: {logging_config.LOGGING_FEATURES['ai_decision_trace']}")
    
    # These should NOT appear in the logs if logic is correct
    # Wait... the Logger itself doesn't check the flag, the call site does.
    # The PLAN said "Implement proper checking at call site". 
    # But for this infrastructure test, we just want to ensure the logger *can* handle the category.
    
    logger.intelligence("This is an INTEL log")
    logger.mission("This is a MISSION log")
    logger.strategy("This is a STRATEGY log")
    
    print(">> Check logs/campaign.log manually for [INTEL], [MISSION], [STRATEGY] tags.")
    
    # 2. Test Telemetry Category
    print("\n[TEST 2] Telemetry Categories")
    try:
        # Just verifying the Enums exist and work
        cat = EventCategory.INTELLIGENCE
        print(f"SUCCESS: EventCategory.INTELLIGENCE exists: {cat}")
        cat = EventCategory.PORTAL
        print(f"SUCCESS: EventCategory.PORTAL exists: {cat}")
    except AttributeError as e:
        print(f"FAILURE: Missing Enum Category: {e}")

    
    # 3. Test AI Decision Trace (Mocked)
    print("\n[TEST 3] AI Decision Trace Logic")
    from src.ai.strategic_planner import StrategicPlanner
    from universes.base.personality_template import FactionPersonality
    
    # Mock Objects
    class MockLogger:
        def ai(self, msg): print(f"  [MOCK LOG] {msg}")
        def mission(self, msg): print(f"  [MOCK LOG] {msg}")
        def campaign(self, msg): print(f"  [MOCK LOG] {msg}")
        def research(self, msg): print(f"  [MOCK LOG] {msg}")
        def debug(self, msg): print(f"  [MOCK LOG] {msg}")
        def strategy(self, msg): print(f"  [MOCK LOG] {msg}")

    class MockEngine:
        def __init__(self):
            self.turn_counter = 100
            self.logger = MockLogger()
            self.telemetry = type('obj', (object,), {'log_event': lambda *args, **kwargs: None})
            
    class MockAI:
        def __init__(self):
            self.engine = MockEngine()
            
    class MockTheater(object):
        def __init__(self, tid, name):
            self.id=tid
            self.name=name
            self.strategic_value=10
            self.threat_score=5
            self.assigned_goal="DEFEND"
            self.system_names=["Sol"]
            self.border_systems=["Sol"]
            self.doctrine="STATIC"
    
    class MockTheaterManager:
        def __init__(self, engine): pass
        def analyze_theaters(self, faction): return [MockTheater("T1", "Sol Theater")]
        def assign_theater_doctrine(self, f, t, p): pass
        def _analyze_choke_points(self, t): pass
        def calculate_strategic_value(self, t): pass
        def _get_system_by_name(self, name): return None

    # Setup Planner
    mock_ai = MockAI()
    planner = StrategicPlanner(mock_ai)
    planner.theater_manager = MockTheaterManager(mock_ai.engine)
    
    personality = FactionPersonality("DefaultPersonality") # Default
    state = {"econ_health": {"state": "STABLE"}}
    
    # Test A: Flag OFF (Default)
    sys.stdout.write("  > Running with Flag OFF... ")
    logging_config.LOGGING_FEATURES['ai_decision_trace'] = False
    planner.create_plan("Imperium", personality, state)
    print("Done. (Should see NO [MOCK LOG])")
    
    # Test B: Flag ON
    sys.stdout.write("  > Running with Flag ON... ")
    logging_config.LOGGING_FEATURES['ai_decision_trace'] = True
    planner.create_plan("Imperium", personality, state)
    print("Done. (Should see [MOCK LOG] with JSON trace)")
    
    # 4. Test Task Force Mission Tracking
    print("\n[TEST 4] Task Force Mission Tracking")
    from src.managers.task_force_manager import TaskForceManager
    from src.models.fleet import TaskForce
    
    # Setup TF Manager
    tf_mgr = TaskForceManager(mock_ai)
    tf_mgr.engine = mock_ai.engine # Ensure engine link
    
    # Mock Planet for Raid
    class MockPlanet:
        def __init__(self, name):
            self.name = name
            self.owner = "Orks"
            self.income_req = 500
            
    mock_target = MockPlanet("RaidWorld")
    
    print("  > Testing RAID Log (Flag OFF)...")
    logging_config.LOGGING_FEATURES['task_force_mission_tracking'] = False
    
    # Manually trigger log logic for raid (since we can't easily mock full fleet selection in unit test)
    # We'll just verify the flag check works by monkey-patching the method or just checking the logging logic directly?
    # Actually, let's just make a dummy TF and call the log method manually or trigger the path.
    # Triggering log_tf_effectiveness is easiest.
    
    tf = TaskForce("TF-1", "Imperium")
    tf.battles_won = 5
    tf.enemies_destroyed = 10
    
    tf_mgr.log_tf_effectiveness(tf) # Should remain silent
    
    print("  > Testing RAID Log (Flag ON)...")
    logging_config.LOGGING_FEATURES['task_force_mission_tracking'] = True
    tf_mgr.log_tf_effectiveness(tf) # Should log valid mission complete message

    # 5. Test Research Path Logic
    print("\n[TEST 5] Research Path Logic")
    from src.ai.economic_engine import EconomicEngine
    
    # Mock Objects for Economy
    class MockTechManager:
        def get_available_research(self, f):
            return [
                {"id": "Lasers_I", "cost": 1000},
                {"id": "Shields_I", "cost": 1500},
                {"id": "Warp_Drive_Mk4", "cost": 5000}, 
                {"id": "Useless_Tech", "cost": 10000}
            ]
            
    class MockEngineEcon:
        def __init__(self):
            self.turn_counter = 50
            self.logger = MockLogger()
            self.tech_manager = MockTechManager()
            self.factions = {}
            
        def get_faction(self, name):
            return self.factions.get(name)
            
    class MockFaction:
        def __init__(self, name):
            self.name = name
            self.research_queue = []
            self.unlocked_techs = ["Lasers_Basic"]
            self.requisition = 0
            
    # Setup
    mock_engine_econ = MockEngineEcon()
    mock_ai_econ = type('obj', (object,), {'engine': mock_engine_econ})
    econ_engine = EconomicEngine(mock_ai_econ)
    
    f_test = MockFaction("Mechanicus")
    mock_engine_econ.factions["Mechanicus"] = f_test
    
    print("  > Testing RESEARCH Log (Flag OFF)...")
    logging_config.LOGGING_FEATURES['tech_research_path_analysis'] = False
    econ_engine.evaluate_research_priorities("Mechanicus")
    
    print("  > Testing RESEARCH Log (Flag ON)...")
    logging_config.LOGGING_FEATURES['tech_research_path_analysis'] = True
    econ_engine.evaluate_research_priorities("Mechanicus")

    # 6. Test Planet Assessment Logic
    print("\n[TEST 6] Planet Assessment Logic")
    from src.services.target_scoring_service import TargetScoringService

    # Mock Planet
    class MockSystem:
        def __init__(self):
            self.x = 100
            self.y = 100
            self.connections = [1, 2, 3]

    class MockPlanetDetailed:
        def __init__(self, name):
            self.name = name
            self.owner = "Neutral"
            self.income_req = 1000
            self.provinces = []
            self.system = MockSystem()
            self.position = (100, 100)

    class MockFactionDetailed:
        def __init__(self):
            self.intelligence_memory = {}

    class MockEngineDetailed:
        def __init__(self):
            self.logger = MockLogger()
            self.planets = {"Terra": MockPlanetDetailed("Terra")}
            self.factions = {"Imperium": MockFactionDetailed()}
        def get_planet(self, name): return self.points.get(name) if hasattr(self, 'points') else self.planets.get(name)
        def get_faction(self, name): return self.factions.get(name)

    # Setup
    mock_engine_det = MockEngineDetailed()
    mock_ai_det = type('obj', (object,), {'engine': mock_engine_det})
    scoring_service = TargetScoringService(mock_ai_det)

    print("  > Testing PLANET Log (Flag OFF)...")
    logging_config.LOGGING_FEATURES['planet_strategic_value_assessment'] = False
    scoring_service.calculate_expansion_target_score("Terra", "Imperium", 0, 0, "Aggressive", "HEALTHY", 10)

    print("  > Testing PLANET Log (Flag ON)...")
    logging_config.LOGGING_FEATURES['planet_strategic_value_assessment'] = True
    scoring_service.calculate_expansion_target_score("Terra", "Imperium", 0, 0, "Aggressive", "HEALTHY", 10)
    
if __name__ == "__main__":
    verify_logging_foundation()
