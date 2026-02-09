
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.reporting.telemetry import TelemetryCollector, EventCategory
    from src.reporting.decision_logger import DecisionLogger
    from src.services.target_scoring_service import TargetScoringService
    from src.managers.intelligence_manager import IntelligenceManager
    from src.ai.strategies.standard import StandardStrategy
    from src.services.construction_service import ConstructionService
    from src.ai.tactical_ai import TacticalAI
except ImportError as e:
    print(f"Import Error: {e}")
    # Fallback/Mock for environment where imports might fail due to complex dependencies
    TelemetryCollector = MagicMock()
    EventCategory = MagicMock()
    DecisionLogger = MagicMock()

class TestAIInstrumentation(unittest.TestCase):
    def setUp(self):
        self.telemetry = MagicMock()
        from src.reporting.decision_logger import DecisionLogger
        self.logger = MagicMock(spec=DecisionLogger)
        self.engine = MagicMock()
        self.engine.telemetry = self.telemetry
        self.engine.turn_counter = 1
        self.engine.get_planet = MagicMock()
        self.engine.get_faction = MagicMock()
        self.engine.intel_manager = MagicMock()
        self.engine.intel_manager.calculate_threat_level.return_value = 1.0
        
        # Setup AI Manager
        self.ai = MagicMock()
        self.ai.decision_logger = self.logger
        self.ai.engine = self.engine # LINK ENGINE
        self.engine.ai_manager = self.ai

    def test_expansion_rationale_generation(self):
        """Verify TargetScoringService returns rationale."""
        from src.services.target_scoring_service import TargetScoringService
        service = TargetScoringService(self.ai)
        
        # Mock dependencies for scoring
        class FakeSystem:
            def __init__(self):
                self.x = 100
                self.y = 100
                self.connections = [1, 2, 3] # Add connections
        class FakePlanet:
            def __init__(self):
                self.name = "TestPlanet"
                self.owner = "Neutral"
                self.system = FakeSystem()
                self.strategic_value = 1.0
                self.income_req = 100
                self.income_prom = 10
                self.planet_class = "Gaia"
                self.provinces = []
        
        planet = FakePlanet()
        self.engine.get_planet.return_value = planet
        
        # Patch logging_config to avoid trace errors
        with patch('src.services.target_scoring_service.logging_config') as mock_log_config:
            mock_log_config.LOGGING_FEATURES = {}
            
            # Use a plain object to ensure dict behavior
            class FakeFaction:
                def __init__(self):
                    self.intelligence_memory = {"TestPlanet": {"last_seen_turn": 0, "income": 400, "strength": 1000}}
                    self.personality = MagicMock()
                    self.personality.get_weight.return_value = 1.0
            
            faction = FakeFaction()
            self.engine.get_faction.return_value = faction
            
            # Explicit weights from DynamicWeightSystem
            weights = {
                "income": 1.0,
                "strategic": 1.0,
                "distance": 1.0,
                "threat": 1.0,
                "capital": 1.0,
                "weakness": 1.0,
                "expansion_bias": 1.0
            }

            # Test scoring directly
            result = service.calculate_expansion_target_score(
                "TestPlanet", "TestFaction", 0, 0, "Balanced", "NORMAL", 1, weights=weights, include_rationale=True
            )
            
            self.assertIsInstance(result, tuple)
            score, rationale = result
            self.assertIsInstance(rationale, dict)
            self.assertIn("base_economic_value", rationale)
            self.assertGreater(score, 0)

    def test_production_logging(self):
        """Verify ConstructionService logs PRODUCTION decisions."""
        from src.services.construction_service import ConstructionService
        svc = ConstructionService(self.engine)
        svc.decision_logger = self.logger
        
        planet = MagicMock()
        planet.name = "PlanetX"
        planet.owner = "FactionA"
        planet.buildings = []
        planet.construction_queue = []
        planet.building_slots = 5
        planet.provinces = []
        
        faction_mgr = MagicMock()
        faction_mgr.requisition = 20000
        faction_mgr.research_income = 10
        faction_mgr.has_tech.return_value = True
        faction_mgr.can_afford.return_value = True
        
        self.engine.economy_manager.faction_econ_cache = {}
        
        # Mock building DB
        with patch('src.services.construction_service.get_building_database') as mock_db:
            mock_db.return_value = {
                "Mine": {"id": "Mine", "cost": 500, "turns": 2, "effects": {"description": "Requisition+10"}},
                "Barracks": {"id": "Barracks", "cost": 1000, "turns": 3, "effects": {"description": "Garrison"}}
            }
            with patch('src.services.construction_service.get_building_category') as mock_cat:
                mock_cat.return_value = "Economy"
                
                svc._process_planet_construction(planet, "FactionA", faction_mgr, 5000, "NORMAL")
                
                # Check for log_decision call
                self.assertTrue(self.logger.log_decision.called)
                _, kwargs = self.logger.log_decision.call_args
                # Check positional or keyword
                call_args = self.logger.log_decision.call_args[0]
                d_type = call_args[0] if call_args else kwargs.get("decision_type")
                self.assertEqual(d_type, "PRODUCTION")

    def test_combat_logging(self):
        """Verify TacticalAI logs COMBAT_TARGET decisions."""
        from src.ai.tactical_ai import TacticalAI
        tai = TacticalAI(self.ai)
        
        unit = MagicMock()
        unit.faction = "F1"
        unit.id = "U1"
        unit.name = "Soldier"
        unit.components = []
        
        enemy = MagicMock()
        enemy.id = "E1"
        enemy.name = "Target"
        enemy.current_hp = 10
        enemy.max_hp = 100
        
        grid = MagicMock()
        grid.get_distance.return_value = 5
        
        tai.select_target(unit, [enemy], grid, context={"doctrine": "CHARGE"})
        
        # Check for log_decision call
        self.assertTrue(self.logger.log_decision.called)
        call_args = self.logger.log_decision.call_args[0]
        call_kwargs = self.logger.log_decision.call_args[1]
        d_type = call_args[0] if call_args else call_kwargs.get("decision_type")
        self.assertEqual(d_type, "COMBAT_TARGET")

    def test_offensive_expansion_logging(self):
        """Verify OffensiveStrategy logs FLEET_MOVE decisions."""
        from src.ai.strategies.offensive_strategy import OffensiveStrategy
        strategy = OffensiveStrategy(self.ai)
        
        # Mock dependencies
        fleet = MagicMock()
        fleet.faction = "FactionA"
        fleet.id = "Fleet-1"
        fleet.power = 1000
        fleet.units = []
        fleet.transport_capacity = 0
        fleet.location = MagicMock()
        fleet.location.name = "StartNode"
        
        f_mgr = MagicMock()
        f_mgr.requisition = 5000
        f_mgr.known_planets = ["TargetPlanet"]
        f_mgr.learning_history = {"target_outcomes": []}
        
        personality = MagicMock()
        personality.name = "Aggressive"
        personality.aggression = 1.2
        personality.doctrine_intensity = 0.5
        personality.combat_doctrine = "ASSAULT"
        personality.retreat_threshold = 0.1
        personality.quirks = {"tier": 3, "navy_recruitment_mult": 1.0}
        
        planet = MagicMock()
        planet.name = "TargetPlanet"
        planet.owner = "Neutral"
        planet.provinces = []
        planet.system.x = 200
        planet.system.y = 200
        
        self.ai.engine.all_planets = [planet]
        self.ai.engine.turn_counter = 1
        self.ai.is_valid_target.return_value = True
        self.ai.task_forces = {"FactionA": []}
        self.ai.tf_counter = 0
        self.ai.engine.intel_manager.get_cached_intel.return_value = (0, 500, 100, 1.0, "Neutral")
        
        # Mock rationale return
        self.ai.calculate_expansion_target_score.return_value = (100.0, {"logic": "high value"})
        
        # Trigger expansion logic
        # Mock random.random and random.uniform to force path
        with patch('random.random', return_value=0.0): # wants_to_expand = True
            with patch('random.uniform', return_value=50.0): # picks the target
                strategy.handle_offensive_expansion(
                    "FactionA", [fleet], f_mgr, personality, "NORMAL", [planet], 1.0, weights={}
                )
        
        # Check for log_decision call
        self.assertTrue(self.logger.log_decision.called)
        _, kwargs = self.logger.log_decision.call_args
        call_args = self.logger.log_decision.call_args[0]
        d_type = call_args[0] if call_args else kwargs.get("decision_type")
        self.assertEqual(d_type, "FLEET_MOVE")

if __name__ == '__main__':
    unittest.main()
