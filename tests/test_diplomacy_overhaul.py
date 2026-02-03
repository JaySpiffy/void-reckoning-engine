import unittest
from unittest.mock import MagicMock, patch
from src.managers.diplomacy_manager import DiplomacyManager
from src.managers.treaty_coordinator import TreatyCoordinator
from src.services.relation_service import RelationService
from src.ai.coalition_builder import CoalitionBuilder

import sys
from unittest.mock import MagicMock, patch

# Mock dependencies before import
sys.modules['src.core.universe_data'] = MagicMock()
sys.modules['src.managers.task_force_manager'] = MagicMock()
sys.modules['src.ai.strategic_planner'] = MagicMock()
sys.modules['src.ai.adaptation.learning_engine'] = MagicMock()
sys.modules['src.ai.economic_engine'] = MagicMock()
sys.modules['src.services.target_scoring_service'] = MagicMock()
sys.modules['src.ai.coordinators.personality_manager'] = MagicMock()
sys.modules['src.ai.coordinators.intelligence_coordinator'] = MagicMock()
sys.modules['src.ai.coordinators.tech_doctrine_manager'] = MagicMock()
sys.modules['src.ai.strategies.economic_strategy'] = MagicMock()
sys.modules['src.ai.strategies.defensive_strategy'] = MagicMock()
sys.modules['src.ai.strategies.offensive_strategy'] = MagicMock()
sys.modules['src.ai.strategies.interception_strategy'] = MagicMock()
sys.modules['src.ai.strategies.exploration_strategy'] = MagicMock()
sys.modules['src.utils.profiler'] = MagicMock()
sys.modules['src.ai.strategies.standard'] = MagicMock()

# Additional Mocks for StrategicAI imports
sys.modules['src.models.fleet'] = MagicMock()
sys.modules['src.reporting.telemetry'] = MagicMock()
sys.modules['universes.base.personality_template'] = MagicMock()
sys.modules['src.core.config'] = MagicMock()
sys.modules['src.core.interfaces'] = MagicMock()

sys.modules['src.ai.dynamic_weights'] = MagicMock()
sys.modules['src.ai.opponent_profiler'] = MagicMock()
sys.modules['src.ai.proactive_diplomacy'] = MagicMock()
sys.modules['src.ai.tactical_ai'] = MagicMock()
sys.modules['src.ai.strategic_memory'] = MagicMock()
sys.modules['src.ai.composition_optimizer'] = MagicMock()

from src.managers.diplomacy_manager import DiplomacyManager
sys.modules['src.ai.opponent_profiler'] = MagicMock()
sys.modules['src.ai.proactive_diplomacy'] = MagicMock()
sys.modules['src.ai.tactical_ai'] = MagicMock()
sys.modules['src.ai.strategic_memory'] = MagicMock()
sys.modules['src.ai.composition_optimizer'] = MagicMock()

from src.managers.diplomacy_manager import DiplomacyManager

class TestDiplomacyOverhaul(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock()
        self.mock_engine.turn_counter = 1
        
        self.factions = ["FactionA", "FactionB", "FactionC"]
        self.mock_engine.factions = {f: MagicMock() for f in self.factions}
        
        # Mock UniverseDataManager at the source where it's used
        self.patcher = patch('src.services.relation_service.UniverseDataManager')
        self.MockUDM = self.patcher.start()
        self.MockUDM.get_instance.return_value.get_historical_bias.return_value = {}
        
        # Setup Managers
        self.diplomacy_manager = DiplomacyManager(self.factions, self.mock_engine)
        self.treaty_coordinator = self.diplomacy_manager.treaty_coordinator
        self.relation_service = self.diplomacy_manager.relation_service
        
        # Link Diplomacy to Engine
        self.mock_engine.diplomacy = self.diplomacy_manager
        
        # Mock get_faction to return the mocks in self.mock_engine.factions
        self.mock_engine.get_faction.side_effect = lambda f: self.mock_engine.factions.get(f)
        
        # Setup FOW for all factions (know everyone for testing)
        for f in self.factions:
             self.mock_engine.factions[f].known_factions = self.factions
             self.mock_engine.factions[f].known_factions = self.factions
             # Fix economy mock for treaty checks (Direct attribute)
             self.mock_engine.factions[f].economy = {"margin": 1.2, "income": 100}

        # Fix economy manager report (via Engine)
        self.mock_engine.economy_manager.get_faction_economic_report.return_value = {"margin": 1.2, "income": 100}
        
        self.mock_ai_manager = MagicMock()
        self.mock_ai_manager.engine = self.mock_engine
        self.mock_ai_manager.get_faction_personality.return_value.diplomatic_tendency = 1.0 # Allow coalitions
        self.coalition_builder = CoalitionBuilder(self.mock_ai_manager)

    def tearDown(self):
        self.patcher.stop()

    def test_border_tension_drift(self):
        """Verify that shared borders cause negative relation drift over time."""
        # 1. Initialize Relations
        self.relation_service.relations["FactionA"]["FactionB"] = 0
        self.relation_service.relations["FactionB"]["FactionA"] = 0
        
        # 2. Mock Planets and Systems for Border Detection
        # FactionA owns P1 (Sys1), FactionB owns P2 (Sys2). Sys1 is connected to Sys2.
        
        mock_p1 = MagicMock(); mock_p1.owner = "FactionA"; mock_p1.name = "P1"
        mock_p2 = MagicMock(); mock_p2.owner = "FactionB"; mock_p2.name = "P2"
        
        # Connection: P1's system connects to P2's system
        mock_sys1 = MagicMock(); mock_sys1.name = "Sys1"
        mock_sys2 = MagicMock(); mock_sys2.name = "Sys2"
        
        # Proper structure: connections are System objects
        mock_sys1.connections = [mock_sys2]
        mock_sys1.planets = [mock_p1]
        
        mock_sys2.connections = [mock_sys1]
        mock_sys2.planets = [mock_p2]
        
        mock_p1.system = mock_sys1
        mock_p2.system = mock_sys2
        
        self.mock_engine.planets_by_faction = {
            "FactionA": [mock_p1],
            "FactionB": [mock_p2]
        }
        
        # 3. Apply Tension
        self.diplomacy_manager._apply_border_tension()
        
        # 4. Verify Drift
        new_rel = self.relation_service.get_relation("FactionA", "FactionB")
        # Should drop from 0 to -1
        self.assertEqual(new_rel, -1, f"Rel should be -1, got {new_rel}")

    def test_treaty_violation_penalty(self):
        """Verify attacking a treaty partner causes massive penalties."""
        # 1. Sign NAP
        self.treaty_coordinator.set_treaty("FactionA", "FactionB", "Non_Aggression_Pact")
        
        # 2. Check Violation
        penalty = self.treaty_coordinator.check_treaty_violation("FactionA", "FactionB", "ATTACK")
        
        # Expectation: 50 for NAP violation
        self.assertEqual(penalty, 50)
        
    def test_coalition_resource_pooling(self):
        """Verify coalition members contribute resources to a pool."""
        # Setup Faction Objects with Requisition
        mock_fa = MagicMock(); mock_fa.requisition = 2000
        mock_fc = MagicMock(); mock_fc.requisition = 2000
        
        def get_faction(name):
             if name == "FactionA": return mock_fa
             if name == "FactionC": return mock_fc
             return None
        self.mock_engine.get_faction.side_effect = get_faction
        
        # 1. Form Coalition
        self.coalition_builder._form_coalition("FactionA", "FactionC", "CONTAIN")
        c_id = list(self.coalition_builder.coalitions.keys())[0]
        c = self.coalition_builder.coalitions[c_id]
        
        # Add FactionC as member (in _form_coalition it invites, but acceptance depends on relation)
        # We'll manually force add
        c.add_member("FactionC")
        
        # 2. Trigger Pooling (Called in process_turn usually)
        self.coalition_builder.pool_resources(c_id)
        
        # 3. Check balances
        # FactionC: 2000 - 5% (100) = 1900
        # FactionA (Leader): 2000 - 100 + 200 (100 from A, 100 from C added to pool then paid out to leader?)
        # Logic: 
        # total_collected = 100 (from A) + 100 (from C) = 200
        # pool += 200
        # leader += 200
        # Wait, if A is leader, A contributes to pool, then pool pays leader. Net change = +100 (from C).
        # A starts 2000. Contribs 100. Becomes 1900.
        # Pool pays 200. A becomes 2100.
        
        self.assertEqual(mock_fc.requisition, 1900)
        self.assertEqual(mock_fa.requisition, 2100)
        self.assertEqual(c.resource_pool, 200)

    def test_war_goal_generation(self):
        """Verify that declaring war generates a specific War Goal."""
        self.diplomacy_manager._declare_war("FactionA", "FactionB", -80, 1, reason="Test", war_goal="HUMILIATION")
        
        goal = self.diplomacy_manager.active_war_goals.get(("FactionA", "FactionB"))
        self.assertEqual(goal, "HUMILIATION")

    def test_ai_respects_nap(self):
        """[INTEGRATION] Verify AI filters out targets protected by NAP."""
        from src.managers.ai_manager import StrategicAI
        
        # 1. Setup AI and Treaty
        ai = StrategicAI(self.mock_engine)
        self.mock_engine.diplomacy.treaty_coordinator.set_treaty("FactionA", "FactionB", "Non-Aggression Pact")
        
        # 2. Setup Targets
        # FactionA targeting FactionB (NAP partner) and FactionC (Enemy)
        target_b = MagicMock(); target_b.owner = "FactionB"
        target_c = MagicMock(); target_c.owner = "FactionC"
        
        candidates = [target_b, target_c]
        
        # Mock Personality (Honorable)
        ai.get_faction_personality = MagicMock()
        ai.get_faction_personality.return_value.honor = 1.0 
        ai.get_faction_personality.return_value.aggression = 0.5
        
        # 3. Filter Matches
        filtered = ai.evaluate_offensive_targets("FactionA", candidates)
        
        # Expectation: FactionB removed due to NAP, FactionC remains
        self.assertNotIn(target_b, filtered)
        self.assertIn(target_c, filtered)

    def test_trade_agreement_drift(self):
        """[INTEGRATION] Verify Trade Agreements increase relations."""
        # 1. Zero Relations
        self.relation_service.relations["FactionA"]["FactionB"] = 0
        
        # 2. Sign Trade Agreement
        self.treaty_coordinator.set_treaty("FactionA", "FactionB", "Trade Agreement")
        
        
        # 3. Process Turn (Drift)
        self.diplomacy_manager.process_turn()
        
        # 4. Check Relation
        # Should be +1
        rel = self.relation_service.get_relation("FactionA", "FactionB")
        self.assertEqual(rel, 1)
