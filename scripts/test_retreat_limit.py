import sys
import unittest
from unittest.mock import MagicMock, Mock

# Import models
# Adjust path if needed
sys.path.append('.') 
from src.models.fleet import Fleet
from src.models.army import ArmyGroup

class TestRetreatLimit(unittest.TestCase):
    def setUp(self):
        self.mock_planet = Mock()
        self.mock_planet.name = "TestPlanet"
        self.mock_planet.node_reference = Mock()
        self.mock_planet.type = "Planet"
        
        self.mock_node = Mock()
        self.mock_node.name = "TestNode"
        
        # Mocks for fleet
        self.fleet = Fleet("F1", "FactionA", self.mock_planet)
        self.fleet.move_to = MagicMock() # Disable actual movement logic
        self.fleet.destination = None
        self.fleet.is_engaged = True
        
        # Mocks for army
        self.army = ArmyGroup("A1", "FactionA", [], self.mock_node)
        self.army.is_engaged = True

    def test_fleet_retreat_limit(self):
        """Verify Fleet can only retreat once per turn."""
        print("\n--- Testing Fleet Retreat Limit ---")
        
        # 1. First Retreat
        print("Attempting First Retreat...")
        success = self.fleet.retreat(self.mock_planet)
        self.assertTrue(success, "First retreat should succeed")
        self.assertTrue(self.fleet.has_retreated_this_turn, "Flag should be set")
        self.assertFalse(self.fleet.is_engaged, "Should break engagement")
        
        # Reset engagement for second test
        self.fleet.is_engaged = True 
        
        # 2. Second Retreat (Same Turn)
        print("Attempting Second Retreat (Same Turn)...")
        success = self.fleet.retreat(self.mock_planet)
        self.assertFalse(success, "Second retreat should FAIL")
        self.assertTrue(self.fleet.has_retreated_this_turn, "Flag should remain set")
        
        # 3. New Turn Reset
        print("Simulating New Turn Reset...")
        self.fleet.reset_turn_flags()
        self.assertFalse(self.fleet.has_retreated_this_turn, "Flag should be cleared")
        
        # 4. Retreat after reset
        self.fleet.is_engaged = True
        success = self.fleet.retreat(self.mock_planet)
        self.assertTrue(success, "Retreat after reset should succeed")

    def test_army_retreat_limit(self):
        """Verify Army can only retreat once per turn."""
        print("\n--- Testing Army Retreat Limit ---")
        
        # 1. First Retreat
        print("Attempting First Retreat...")
        success = self.army.retreat(self.mock_node)
        self.assertTrue(success, "First retreat should succeed")
        self.assertTrue(self.army.has_retreated_this_turn, "Flag should be set")
        self.assertFalse(self.army.is_engaged, "Should break engagement")
        
        # Reset for second test
        self.army.is_engaged = True
        
        # 2. Second Retreat
        print("Attempting Second Retreat (Same Turn)...")
        success = self.army.retreat(self.mock_node)
        self.assertFalse(success, "Second retreat should FAIL")
        
        # 3. New Turn Reset
        print("Simulating New Turn Reset...")
        self.army.reset_turn_flags()
        self.assertFalse(self.army.has_retreated_this_turn, "Flag should be cleared")

if __name__ == '__main__':
    unittest.main()
