import unittest
from unittest.mock import MagicMock
from src.models.planet import Planet
from src.models.hex_node import HexNode
from src.combat.tactical_grid import TacticalGrid
from src.combat.real_time.map_manager import MapGenerator, MapTemplates

class TestHexBattleIntegration(unittest.TestCase):
    
    def test_hex_map_generation_triggers(self):
        # 1. Setup Planet & Hex
        p = Planet.__new__(Planet) # Bypass init
        p.name = "Gladius Prime"
        p.building_slots = 5
        p.system = "SystemA"
        p._provinces = None
        p.hex_map = None
        
        # Manually trigger hex gen
        # We need to ensure imports inside planet.py don't fail, which we fixed.
        Planet._generate_hex_map_lazy(p)
        
        # Get a City Hex (Center)
        city_hex = p.hex_map.get((0,0))
        self.assertIsNotNone(city_hex)
        self.assertEqual(city_hex.terrain_type, "City")
        
        # Get a Wasteland Hex (Outer)
        # Find one
        wasteland_hex = next((h for h in p._provinces if h.terrain_type == "Wasteland"), None)
        self.assertIsNotNone(wasteland_hex)
        
        # 2. Test Map Generator - City
        grid_city = TacticalGrid(100, 100, "Ground")
        MapGenerator.generate_map(grid_city, city_hex)
        
        # Verify City Elements
        # Check for "City Center" objective
        has_city_center = any(obj.name == "City Center" for obj in grid_city.objectives)
        self.assertTrue(has_city_center, "City Hex should generate City Center objective")
        
        # Check for Buildings
        has_buildings = any("Block" in obj.name for obj in grid_city.obstacles)
        self.assertTrue(has_buildings, "City Hex should have buildings")

        # 3. Test Map Generator - Wasteland
        grid_waste = TacticalGrid(100, 100, "Ground")
        MapGenerator.generate_map(grid_waste, wasteland_hex)
        
        # Verify Wasteland Elements
        has_crater = any(area.name == "Crater Field" for area in grid_waste.areas)
        self.assertTrue(has_crater, "Wasteland Hex should have Crater Field")

if __name__ == '__main__':
    unittest.main()
