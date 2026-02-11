import unittest
from unittest.mock import MagicMock, Mock
from src.ai.strategies.offensive_strategy import OffensiveStrategy
from src.models.fleet import Fleet, TaskForce

class TestPursuitLogic(unittest.TestCase):
    def test_hunter_killer_dispatch(self):
        """Verify that handle_pursuit dispatches a fleet to intercept a retreated enemy."""
        
        # 1. Setup Context
        mock_ai = MagicMock()
        mock_ai.engine.fleets = []
        mock_ai.task_forces = {"FactionA": []}
        mock_ai.tf_counter = 0
        
        # Setup Diplomacy (Enemies)
        mock_diplomacy = Mock()
        mock_diplomacy.get_enemies.return_value = ["FactionB"]
        mock_ai.engine.diplomacy = mock_diplomacy
        
        # Setup Strategy
        strategy = OffensiveStrategy(mock_ai)
        
        # 2. Setup Fleets
        # Location
        loc_a = Mock()
        loc_a.name = "SystemA"
        loc_a.x, loc_a.y = 10, 10
        
        # Enemy Fleet (Vulnerable: Retreated)
        enemy_fleet = MagicMock(spec=Fleet)
        enemy_fleet.id = "EnemyF"
        enemy_fleet.faction = "FactionB"
        enemy_fleet.power = 100
        enemy_fleet.location = loc_a
        enemy_fleet.has_retreated_this_turn = True # <--- KEY TRIGGER
        enemy_fleet.is_destroyed = False
        
        # Friendly Fleet (Hunter)
        hunter_fleet = MagicMock(spec=Fleet)
        hunter_fleet.id = "HunterF"
        hunter_fleet.faction = "FactionA"
        hunter_fleet.power = 500 # Stronger
        hunter_fleet.location = loc_a # Same location (distance 0)
        # hunter_fleet.distance_to.return_value = 0.0 # Removed
        
        mock_ai.engine.fleets = [enemy_fleet, hunter_fleet]
        
        # Setup Faction Manager (Visibility)
        mock_f_mgr = Mock()
        mock_f_mgr.visible_planets = {"SystemA"} # Enemy is visible
        
        available_fleets = [hunter_fleet]
        
        # 3. Execute
        strategy.handle_pursuit("FactionA", available_fleets, mock_f_mgr, [])
        
        # 4. Verify
        # A. Task Force Created?
        tfs = mock_ai.task_forces["FactionA"]
        self.assertEqual(len(tfs), 1, "Should create 1 Task Force")
        
        tf = tfs[0]
        self.assertEqual(tf.mission_role, "PURSUIT")
        self.assertEqual(tf.target, enemy_fleet)
        
        # B. Fleet Consumed?
        self.assertEqual(len(available_fleets), 0, "Hunter fleet should be removed from available list")
        
        print("Success: Hunter-Killer dispatched against retreated enemy!")

    def test_weak_fleet_pursuit(self):
        """Verify that handle_pursuit dispatches a fleet to intercept a WEAK enemy (not retreated)."""
        
        # 1. Setup Context (Similar to above)
        mock_ai = MagicMock()
        mock_ai.engine.fleets = []
        mock_ai.task_forces = {"FactionA": []}
        mock_ai.tf_counter = 0
        mock_diplomacy = Mock()
        mock_diplomacy.get_enemies.return_value = ["FactionB"]
        mock_ai.engine.diplomacy = mock_diplomacy
        strategy = OffensiveStrategy(mock_ai)
        
        loc_a = Mock()
        loc_a.name = "SystemA"
        
        # Enemy Fleet (Vulnerable: Weak)
        enemy_fleet = MagicMock(spec=Fleet)
        enemy_fleet = MagicMock(spec=Fleet)
        enemy_fleet.id = "WeakF"
        enemy_fleet.faction = "FactionB"
        enemy_fleet.power = 50 # < 500 Threshold
        enemy_fleet.location = loc_a
        enemy_fleet.has_retreated_this_turn = False 
        # enemy_fleet.original_owner = "FactionB" # Removed - using faction instead
        enemy_fleet.is_destroyed = False
        
        hunter_fleet = MagicMock(spec=Fleet)
        hunter_fleet.id = "HunterF"
        hunter_fleet.faction = "FactionA"
        hunter_fleet.power = 500 
        hunter_fleet.location = loc_a 
        # hunter_fleet.distance_to.return_value = 5.0 # Removed
        
        # Test scenario: Same location so distance = 0
        loc_a.x, loc_a.y = 10, 10
        
        mock_ai.engine.fleets = [enemy_fleet, hunter_fleet]
        mock_f_mgr = Mock()
        mock_f_mgr.visible_planets = {"SystemA"} 
        
        available_fleets = [hunter_fleet]
        
        # Execute
        strategy.handle_pursuit("FactionA", available_fleets, mock_f_mgr, [])
        
        # Verify
        tfs = mock_ai.task_forces["FactionA"]
        self.assertEqual(len(tfs), 1, "Should create 1 Task Force for weak enemy")
        self.assertEqual(tfs[0].mission_role, "PURSUIT")
        print("Success: Hunter-Killer dispatched against WEAK enemy!")

if __name__ == '__main__':
    unittest.main()
