
import time
import json
import os
import sys
from src.utils.logging import GameLogger
from src.reporting.telemetry import TelemetryCollector, EventCategory
from src.config import logging_config
from src.ai.strategic_planner import StrategicPlanner
from src.managers.task_force_manager import TaskForceManager
from src.ai.economic_engine import EconomicEngine
from src.services.target_scoring_service import TargetScoringService
from src.models.fleet import TaskForce

# Mock Objects for benchmarking
class MockLogger:
    def ai(self, msg): pass
    def mission(self, msg): pass
    def campaign(self, msg): pass
    def research(self, msg): pass
    def debug(self, msg): pass
    def strategy(self, msg): pass

class MockEngine:
    def __init__(self):
        self.turn_counter = 100
        self.logger = MockLogger()
        self.telemetry = type('obj', (object,), {'log_event': lambda *args, **kwargs: None})
        self.factions = {}
        self.all_planets = []
        self.fleets = []
        self.planets_by_faction = {}
        self.all_units = []
    def get_faction(self, name): return self.factions.get(name)
    def get_planet(self, name): return None
    def get_theater_power(self, *args, **kwargs): return {}

class MockAI:
    def __init__(self):
        self.engine = MockEngine()
        self.turn_cache = {}
        self.target_scoring = None # Set later

def benchmark(name, func, iterations=1000):
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()
    duration = end - start
    print(f"| {name:<35} | {duration*1000:8.4f} ms | {(duration/iterations)*1e6:10.4f} us |")
    return duration

def run_benchmarks():
    # Setup
    mock_ai = MockAI()
    planner = StrategicPlanner(mock_ai)
    tf_mgr = TaskForceManager(mock_ai)
    econ_engine = EconomicEngine(mock_ai)
    scoring_service = TargetScoringService(mock_ai)
    mock_ai.target_scoring = scoring_service
    
    # Mock Personality
    mock_personality = type('obj', (object,), {
        'planning_horizon': 5,
        'aggression': 1.0,
        'retreat_threshold': 0.5,
        'rally_point_preference': 'CAPITAL',
        'strategic_doctrine': 'AGGRESSIVE_EXPANSION'
    })
    
    f_test = type('obj', (object,), {
        'name': 'Imperium', 
        'research_queue': [], 
        'unlocked_techs': [],
        'intelligence_memory': {},
        'home_planet_name': 'Terra'
    })
    mock_ai.engine.factions['Imperium'] = f_test
    
    # Reset all flags
    for k in logging_config.LOGGING_FEATURES:
        logging_config.LOGGING_FEATURES[k] = False

    print("\n--- Phase 6 Performance Benchmark (1000 iterations) ---")
    print("-" * 75)
    print(f"| {'Feature/Test':<35} | {'Total Time':<11} | {'Per Call':<11} |")
    print("-" * 75)

    # 1. Baseline (All OFF)
    benchmark("Baseline (All Features OFF)", lambda: planner.create_plan("Imperium", mock_personality, {}))

    # 2. AI Decision Trace
    logging_config.LOGGING_FEATURES['ai_decision_trace'] = True
    benchmark("AI Decision Trace (ON)", lambda: planner.create_plan("Imperium", mock_personality, {}))
    logging_config.LOGGING_FEATURES['ai_decision_trace'] = False

    # 3. Mission Tracking
    tf = TaskForce("TF-1", "Imperium")
    logging_config.LOGGING_FEATURES['task_force_mission_tracking'] = True
    benchmark("Task Force Mission Tracking (ON)", lambda: tf_mgr.log_tf_effectiveness(tf))
    logging_config.LOGGING_FEATURES['task_force_mission_tracking'] = False

    # 4. Tech Path Analysis
    # Need to mock more for econ engine
    mock_ai.engine.tech_manager = type('obj', (object,), {'get_available_research': lambda f: [{"id":"T1", "cost":100}]})
    logging_config.LOGGING_FEATURES['tech_research_path_analysis'] = True
    benchmark("Tech Research Path Analysis (ON)", lambda: econ_engine.evaluate_research_priorities("Imperium"))
    logging_config.LOGGING_FEATURES['tech_research_path_analysis'] = False

    # 5. Planet Assessment
    # Note: This is usually called many times per turn
    logging_config.LOGGING_FEATURES['planet_strategic_value_assessment'] = True
    benchmark("Planet Strategic Assessment (ON)", lambda: scoring_service.calculate_expansion_target_score("Sol", "Imperium", 0,0, "A", "H", 1))
    logging_config.LOGGING_FEATURES['planet_strategic_value_assessment'] = False

    # 6. All Togther
    for k in logging_config.LOGGING_FEATURES:
        logging_config.LOGGING_FEATURES[k] = True
    
    def run_all():
        planner.create_plan("Imperium", mock_personality, {})
        tf_mgr.log_tf_effectiveness(tf)
        econ_engine.evaluate_research_priorities("Imperium")
        scoring_service.calculate_expansion_target_score("Sol", "Imperium", 0,0, "A", "H", 1)
        
    benchmark("COMBINED (All Features ON)", run_all)
    print("-" * 75)

if __name__ == "__main__":
    run_benchmarks()
