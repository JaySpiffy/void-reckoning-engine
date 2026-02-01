import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.combat.tactical_engine import initialize_battle_state, execute_battle_round
from src.models.unit import Regiment

class TestCombatRefactor(unittest.TestCase):
    def setUp(self):
        # Create mock units
        self.unit1 = Regiment("Marine", 10, 10, 100, 4, 10, {})
        self.unit1.current_hp = 100
        self.unit1.leadership = 7
        self.unit1.current_suppression = 0
        self.unit1.movement_points = 6
        self.unit1.grid_x = 0
        self.unit1.grid_y = 0
        self.unit1.is_deployed = True
        self.unit1.components = []

        self.unit2 = Regiment("Ork", 8, 8, 100, 6, 12, {})
        self.unit2.current_hp = 100
        self.unit2.leadership = 6
        self.unit2.current_suppression = 0
        self.unit2.movement_points = 5
        self.unit2.grid_x = 90
        self.unit2.grid_y = 90
        self.unit2.is_deployed = True
        self.unit2.components = []

        self.armies_dict = {
            "Imperium": [self.unit1],
            "Orks": [self.unit2]
        }
        
    def test_execute_battle_round_flow(self):
        # Initialize battle state
        manager = initialize_battle_state(self.armies_dict)
        manager.round_num = 0
        
        # Mock detailed log
        log_path = "test_battle_log.txt"
        
        # Execute round
        print("Executing battle round...")
        result = execute_battle_round(manager, detailed_log_file=log_path)
        
        print(f"Round Result: {result}")
        print(f"Manager Round Num: {manager.round_num}")
        
        # Verify round number incremented
        self.assertEqual(manager.round_num, 1)
        
        # Verify log file created
        self.assertTrue(os.path.exists(log_path))
        with open(log_path, 'r') as f:
            content = f.read()
            print("Log Content Snippet:")
            print(content[:500])
            self.assertIn("ABILITY PHASE", content)
            self.assertIn("MOVEMENT PHASE", content)
            self.assertIn("SHOOTING PHASE", content)
            self.assertIn("MELEE PHASE", content)
            self.assertIn("MORALE PHASE", content)
            
        # Cleanup
        if os.path.exists(log_path):
            os.remove(log_path)

if __name__ == "__main__":
    unittest.main()
