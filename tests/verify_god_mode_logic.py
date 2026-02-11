import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())

from src.managers.god_mode.fleet_spawner import FleetSpawner
from src.models.star_system import StarSystem

class TestGodModeLogic(unittest.TestCase):
    def setUp(self):
        # Mock Engine
        self.mock_engine = MagicMock()
        self.mock_engine.factions = {"Humanity": MagicMock()}
        self.mock_engine.systems = []
        self.mock_engine.fleets = []
        self.mock_engine.universe_name = "test_universe"
        
        # Setup dummy system
        self.sol = StarSystem("Sol", 0, 0)
        self.mock_engine.systems.append(self.sol)
        
        # Mock Diplomacy
        self.mock_engine.diplomacy = MagicMock()

    @patch('src.managers.god_mode.fleet_spawner.get_universe_config')
    def test_pirate_spawn(self, mock_get_config):
        mock_get_config.return_value = {}
        
        spawner = FleetSpawner(self.mock_engine)
        
        print("\nAttempting to spawn Pirate Fleet...")
        success = spawner.spawn_pirate_fleet("Sol")
        
        self.assertTrue(success, "Spawn returned False")
        
        # Verify Faction Created
        self.assertIn("Void_Reavers", self.mock_engine.factions, "Void Reavers faction NOT found")
        print("PASS: Void Reavers faction created.")
        
        # Verify Fleet in Engine
        # FleetSpawner appends to self.engine.fleets
        self.assertTrue(len(self.mock_engine.fleets) > 0, "No fleet added to engine.fleets")
        
        fleet = self.mock_engine.fleets[0]
        print(f"PASS: Pirate fleet added: {fleet.name}")
        self.assertEqual(fleet.faction, "Void_Reavers")
        self.assertEqual(fleet.location, self.sol)
        
        # Verify Fleet Composition
        # We expect 1 Galleon, 4 Raiders, 8 Skiffs = 13 ships
        self.assertEqual(len(fleet.units), 13)
        print(f"PASS: Correct unit count: {len(fleet.units)}")

    @patch('src.managers.god_mode.fleet_spawner.get_universe_config')
    def test_pirate_targeting(self, mock_get_config):
        mock_get_config.return_value = {}
        
        # Setup Target Faction
        self.mock_engine.factions["TargetFaction"] = MagicMock()
        
        # Setup Target System
        target_system = StarSystem("TargetSys", 10, 10)
        target_system.owner = "TargetFaction"
        self.mock_engine.systems.append(target_system)
        
        spawner = FleetSpawner(self.mock_engine)
        
        print("\nAttempting to spawn Pirate Raid on TargetFaction...")
        success = spawner.spawn_pirate_fleet("Sol", target_faction="TargetFaction")
        
        self.assertTrue(success, "Spawn returned False")
        
        # Verify War Declared
        # We check if set_relation and declare_war were called
        self.mock_engine.diplomacy.set_relation.assert_called_with("Void_Reavers", "TargetFaction", -100)
        self.mock_engine.diplomacy.declare_war.assert_called_with("Void_Reavers", "TargetFaction")
        print("PASS: War declared on TargetFaction.")
        
        # Verify Spawn Location
        # Should be at TargetSys, not Sol
        fleet = self.mock_engine.fleets[0] # assuming cleared list or new instance, but here we append
        # We need to find the fleet that was just added. 
        # In this simplistic test class, we can just check the last one if we ran test_pirate_spawn first,
        # but unit tests run in arbitrary order. 
        # Let's check if *any* fleet is at TargetSys
        
        fleets_at_target = [f for f in self.mock_engine.fleets if f.location == target_system and f.faction == "Void_Reavers"]
        self.assertTrue(len(fleets_at_target) > 0, "No pirate fleet spawned at TargetSys")
        print(f"PASS: Pirate fleet spawned at {target_system.name}")

if __name__ == "__main__":
    unittest.main()
