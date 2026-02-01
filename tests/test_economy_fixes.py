
import unittest
import sys
import os
sys.path.append(os.getcwd())
from unittest.mock import MagicMock, patch
from src.services.construction_service import ConstructionService
from src.managers.economy.insolvency_handler import InsolvencyHandler
from src.managers.economy_manager import EconomyManager

class TestEconomyFixes(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock()
        self.mock_logger = MagicMock()
        self.mock_engine.logger = self.mock_logger
        self.mock_telemetry = MagicMock()
        self.mock_engine.telemetry = self.mock_telemetry
        self.mock_engine.game_config = {"simulation": {"random_seed": None}}
        
        # Mock EconomyManager
        self.economy_manager = EconomyManager(self.mock_engine)
        self.mock_engine.economy_manager = self.economy_manager
        
        # Mock Data
        self.mock_engine.universe_data.get_building_database.return_value = {
            "expensive_factory": {"cost": 1000, "upkeep_req": 500, "category": "Industry"},
            "cheap_mine": {"cost": 500, "upkeep_req": 10, "requisition_output": 100, "category": "Economy"},
            "useless_monument": {"cost": 200, "upkeep_req": 100, "category": "Culture"}
        }

    def test_construction_sustainability_check(self):
        """Verify that construction is blocked if it causes a deficit."""
        service = self.economy_manager.construction_service
        
        # Mock Faction
        mock_faction = MagicMock()
        mock_faction.requisition = 1000
        mock_faction.can_afford.return_value = True
        mock_faction.research_income = 100
        
        # Mock Econ Cache (Status: Solvent but tight)
        # Income: 1000, Upkeep: 900 -> Net: 100
        self.economy_manager.faction_econ_cache["test_faction"] = {
            "income": 1000,
            "total_upkeep": 900
        }
        
        # Mock Planet
        mock_planet = MagicMock()
        mock_planet.name = "TestPlanet"
        mock_planet.owner = "test_faction"
        mock_planet.construction_queue = []
        mock_planet.buildings = []
        mock_planet.building_slots = 10
        mock_planet.provinces = []
        
        test_db = {
            "expensive_factory": {"cost": 1000, "upkeep_req": 500, "category": "Industry"},
            "cheap_mine": {"cost": 500, "upkeep_req": 10, "requisition_output": 100, "category": "Economy"},
            "useless_monument": {"cost": 200, "upkeep_req": 100, "category": "Culture"}
        }

        # Case 1: Build Expensive Factory (Upkeep 500)
        # Net (100) - New (500) = -400. Should REJECT.
        with patch('src.services.construction_service.get_building_database', return_value=test_db):
            with patch('src.services.construction_service.get_building_category', return_value="Industry"):
                # We need to mock _process_planet_construction calling logic, 
                # but easier to test the logic block directly? 
                # Since I can't easily extract the middle of a method, I have to rely on the behavior.
                # I'll call _process_planet_construction with specific target
                
                # Wait, _process_planet_construction randomizes choice. 
                # I need to mock get_stream("economy").choice to pick my building.
                mock_stream = MagicMock()
                mock_stream.choice.return_value = "expensive_factory"
                
                with patch('src.services.construction_service.get_stream', return_value=mock_stream):
                     # Force candidates to only be this one via the DB mock
                     cost, budget = service._process_planet_construction(mock_planet, "test_faction", mock_faction, 2000, "EXPANSION")
                        
                     # SHOULD FAIL (Return 0,0)
                     self.assertEqual(cost, 0, "Should reject expensive building")
        
        # Case 2: Build Cheap Mine (Upkeep 10. Economic)
        # Income: 1000, Upkeep: 1100 -> Net: -100 (Deficit)
        self.economy_manager.faction_econ_cache["test_faction"]["total_upkeep"] = 1100
        
        with patch('src.services.construction_service.get_building_database', return_value=test_db):
            with patch('src.services.construction_service.get_building_category', return_value="Economy"):
                mock_stream = MagicMock()
                mock_stream.choice.return_value = "cheap_mine"
                with patch('src.services.construction_service.get_stream', return_value=mock_stream):
                        mock_faction.construct_building.return_value = True # Simulate success
                        
                        cost, budget = service._process_planet_construction(mock_planet, "test_faction", mock_faction, 2000, "EXPANSION")
                        
                        # SHOULD SUCCESS
                        self.assertEqual(cost, 500, "Should allow economic building despite deficit")

    def test_insolvency_liquidation(self):
        """Verify that buildings are sold when bankrupt."""
        handler = InsolvencyHandler(self.mock_engine)
        
        # Mock Faction (Bankrupt)
        mock_faction = MagicMock()
        mock_faction.requisition = -5000
        
        # Mock high upkeep
        income = 1000
        upkeep = 3000 # Deficit 2000
        
        # Mock Planets with buildings
        p1 = MagicMock()
        p1.buildings = ["useless_monument", "expensive_factory"] # Upkeep 100 + 500 = 600
        p1.provinces = []
        
        self.mock_engine.planets_by_faction = {"test_faction": [p1]}
        
        # Run Handler
        # It should iterate through buildings and sell sorted by upkeep (expensive_factory first)
        handler.handle_insolvency("test_faction", mock_faction, [], income, upkeep)
        
        # Check if buildings removed
        self.assertNotIn("expensive_factory", p1.buildings)
        self.assertNotIn("useless_monument", p1.buildings)
        
        # Check if money refunded
        # Factory: 1000 * 0.25 = 250
        # Monument: 200 * 0.25 = 50
        # Total gained: 300
        # Requisition should increase by 300
        # mock_faction.requisition += 300
        # Verify the add call happened?
        # MagicMock arithmetic is tricky, but we can check call count on logger
        self.mock_logger.economy.assert_called() 
        args, _ = self.mock_logger.economy.call_args
        self.assertIn("liquidated 2 buildings", args[0])

if __name__ == '__main__':
    unittest.main()
