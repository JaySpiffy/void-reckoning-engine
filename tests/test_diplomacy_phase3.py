import unittest
from unittest.mock import MagicMock, patch
import sys

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
from src.managers.treaty_coordinator import TreatyCoordinator
from src.services.relation_service import RelationService

class TestDiplomacyPhase3(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock()
        self.mock_engine.turn_counter = 100
        
        # Use valid Void Reckoning factions
        self.factions = ["Aurelian_Hegemony", "Templars_of_the_Flux", "SteelBound_Syndicate", "BioTide_Collective"]
        self.mock_engine.factions = {f: MagicMock() for f in self.factions}
        
        self.patcher = patch('src.services.relation_service.UniverseDataManager')
        self.MockUDM = self.patcher.start()
        self.MockUDM.get_instance.return_value.get_historical_bias.return_value = {}
        
        self.diplomacy_manager = DiplomacyManager(self.factions, self.mock_engine)
        self.relation_service = self.diplomacy_manager.relation_service
        self.treaty_coordinator = self.diplomacy_manager.treaty_coordinator
        
        self.mock_engine.diplomacy = self.diplomacy_manager
        self.mock_engine.get_faction.side_effect = lambda f: self.mock_engine.factions.get(f)
        
        # Setup FOW
        for f in self.factions:
             self.mock_engine.factions[f].known_factions = self.factions
             self.mock_engine.factions[f].economy = {"margin": 1.2, "income": 100}
             
    def tearDown(self):
        self.patcher.stop()

    def test_ideological_drift(self):
        """Verify alignment-based drift works."""
        f1 = "Aurelian_Hegemony" # ORDER
        f2 = "Templars_of_the_Flux" # CHAOS
        
        # Check Initial Relations
        self.relation_service.relations[f1][f2] = 0
        self.relation_service.relations[f2][f1] = 0
        
        # 1. Apply Drift
        self.relation_service.apply_ideological_drift()
        
        # 2. Check Order vs Chaos (Should be -2)
        rel = self.relation_service.get_relation(f1, f2)
        self.assertEqual(rel, -2, f"{f1} vs {f2} shoud be -2, got {rel}")
        
    def test_existential_threat_drift(self):
        """Verify Destruction factions cause massive negative drift."""
        f1 = "SteelBound_Syndicate" # PROFIT
        f2 = "BioTide_Collective" # DESTRUCTION
        
        # 0. Neutral vs Threat
        self.relation_service.relations[f1][f2] = 0
        
        # 1. Apply Drift
        self.relation_service.apply_ideological_drift()
        
        # 2. Check (Should be -5)
        rel = self.relation_service.get_relation(f1, f2)
        self.assertEqual(rel, -5, f"{f1} vs {f2} should be -5, got {rel}")

    def test_peace_terms_cede_conquests(self):
        """Verify 'Cede Conquests' terms grant relation bonus to offset grudges."""
        proposer = "Templars_of_the_Flux" # Loser
        target = "Aurelian_Hegemony" # Winner
        
        # 1. Setup War and Grudge
        self.relation_service.relations[proposer][target] = -90
        self.relation_service.relations[target][proposer] = -90
        # CRITICAL: Must start at War
        self.treaty_coordinator.set_treaty(proposer, target, "War")
        
        # Target hates Proposer due to war crimes
        self.relation_service.add_grudge(target, proposer, 80, "War Crimes")
        
        # 2. Mock War Exhaustion (Make target willing to accept)
        # Score = 70*1.5 (105) + 40 (Terms) - 80 (Grudge) = 65 > 50 ACCEPT
        self.diplomacy_manager.war_exhaustion[target] = 70 
        
        # 3. Sue for Peace (CEDE_CONQUESTS)
        self.diplomacy_manager.sue_for_peace(proposer, target, "CEDE_CONQUESTS")
        
        # 4. Check Result
        # Treaty should be Peace
        treaty = self.treaty_coordinator.get_treaty(proposer, target)
        self.assertEqual(treaty, "Peace")
        
        # Relations: -90 + 50 (Bonus) = -40, then reset to -10 if < -10... NO, wait.
        # Logic: If < -10, set to -10. 
        # -40 is < -10, so it becomes -10.
        rel = self.relation_service.get_relation(target, proposer)
        self.assertEqual(rel, -10)
        
    def test_peace_rejection_low_score(self):
        """Verify peace is rejected if score is too low."""
        proposer = "SteelBound_Syndicate"
        target = "Aurelian_Hegemony"
        
        # CRITICAL: Start at WAR (otherwise defaults to something else)
        self.treaty_coordinator.set_treaty(proposer, target, "War")
        
        self.diplomacy_manager.war_exhaustion[target] = 0 # Fresh and angry
        self.relation_service.add_grudge(target, proposer, 50, "Heresy")
        
        # Sue for peace
        # Score = 0 - 10 (White Peace) - 50 = -60 < 50 REJECT
        self.diplomacy_manager.sue_for_peace(proposer, target, "WHITE_PEACE")
        
        # Should stay at War
        treaty = self.treaty_coordinator.get_treaty(proposer, target)
        self.assertEqual(treaty, "War") # Not Peace

if __name__ == '__main__':
    unittest.main()
