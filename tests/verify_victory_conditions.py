import sys
import os
import unittest
from unittest.mock import MagicMock

# Ensure src path is available
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.managers.mission_manager import MissionManager
from src.core.constants import VICTORY_PLANET_THRESHOLD

class TestVictoryConditions(unittest.TestCase):
    def setUp(self):
        self.mm = MissionManager()
        self.mock_engine = MagicMock()
        self.mock_engine.game_config.max_turns = 100
        self.mock_engine.factions = {"Empire": MagicMock(), "Rebels": MagicMock()}

    def test_score_victory(self):
        print("\n--- Testing Score Victory ---")
        # Setup: Turn limit reached
        self.mock_engine.turn_counter = 100
        
        # Setup Faction Assets for Scoring
        # Empire: 2 Planets, 1 Tech
        # Rebels: 1 Planet, 0 Tech
        
        p1 = MagicMock(); p1.owner = "Empire"; p1.buildings = []; p1.system = None; p1.provinces = []
        p2 = MagicMock(); p2.owner = "Empire"; p2.buildings = []; p2.system = None; p2.provinces = []
        p3 = MagicMock(); p3.owner = "Rebels"; p3.buildings = []; p3.system = None; p3.provinces = []
        
        self.mock_engine.all_planets = [p1, p2, p3]
        self.mock_engine.fleets = []
        self.mock_engine.systems = []
        
        # Faction Object Data
        self.mock_engine.factions["Empire"].requisition = 10000 # +10 pts
        self.mock_engine.factions["Empire"].unlocked_techs = ["A"] # +1000 pts
        
        self.mock_engine.factions["Rebels"].requisition = 0
        self.mock_engine.factions["Rebels"].unlocked_techs = []
        
        # Empire Score: (2*100) + 1000 + 10 = 1210
        # Rebels Score: (1*100) = 100
        
        winner = self.mm.check_victory_conditions(self.mock_engine)
        print(f"Winner declared: {winner}")
        
        self.assertEqual(winner, "Empire")
        print("PASS: Score Victory Correct.")

    def test_conquest_victory(self):
        print("\n--- Testing Conquest Victory ---")
        # Setup: Turn limit NOT reached
        self.mock_engine.turn_counter = 50
        
        # Setup Planets: Total 10. Threshold (default 0.6?)
        # Let's check VICTORY_PLANET_THRESHOLD in code or assume standard
        # Actually in mission_manager.py it uses the constant.
        
        # If Threshold is 60%, owning 6/10 should win.
        total = 10
        planets = []
        for i in range(7): # 70%
            p = MagicMock()
            p.owner = "Empire"
            p.buildings = []; p.system = None; p.provinces = []
            planets.append(p)
            
        for i in range(3): # 30%
            p = MagicMock()
            p.owner = "Rebels"
            p.buildings = []; p.system = None; p.provinces = []
            planets.append(p)
            
        self.mock_engine.all_planets = planets
        
        winner = self.mm.check_victory_conditions(self.mock_engine)
        print(f"Winner declared: {winner}")
        
        self.assertEqual(winner, "Empire")
        print("PASS: Conquest Victory Correct.")
        
    def test_elimination_check(self):
        print("\n--- Testing Elimination (Implicit Conquest) ---")
        # Verify that if one owns 100% planets, they win regardless of other conditions
        self.mock_engine.turn_counter = 10
        
        planets = []
        for i in range(5):
            p = MagicMock()
            p.owner = "Empire"
            p.buildings = []; p.system = None; p.provinces = []
            planets.append(p)
            
        self.mock_engine.all_planets = planets
         
        winner = self.mm.check_victory_conditions(self.mock_engine)
        print(f"Winner declared: {winner}")
        
        self.assertEqual(winner, "Empire")
        print("PASS: Elimination/Dominance Victory Correct.")

if __name__ == "__main__":
    unittest.main()
