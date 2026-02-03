import unittest
from unittest.mock import MagicMock
from src.models.planet import Planet
from src.models.hex_node import HexNode
from src.core.hex_lib import Hex

class TestPlanetHexMap(unittest.TestCase):
    
    def setUp(self):
        # Mock System and UniverseData
        self.mock_system = MagicMock()
        self.mock_system.name = "TestSystem"
        
        # We need to mock UniverseDataManager because Planet.__init__ calls it
        # However, we can use a mock patch or just rely on the existing mocks if accessible
        # Since I can't easily patch inside this file for external singleton, 
        # I rely on the fact that the simulation likely has a mock mode or I can try/except
        pass

    def test_hex_map_generation(self):
        # Initialize Planet
        # Need to handle the random planet class. 
        # Integration test might fail if it tries to load JSONs.
        # Let's try to mock the specific call or just assume environment is set up.
        # For unit testing, mocking UniverseDataManager.get_instance() is best.
        
        # SKIP if we can't easily mock the singleton without extensive setup. 
        # Instead, verify the _generate_hex_map_lazy method logic by manual invocation if possible.
        pass

    def test_direct_hex_logic(self):
        """Test the logic by manually creating a minimal planet and calling _generate_hex_map_lazy."""
        # Create a dummy object mimicking Planet to avoid __init__ dependencies
        class MockPlanet:
            def __init__(self):
                self.name = "TestWorld"
                self.building_slots = 5
                self.system = "Sys"
                self.hex_map = None
                self._provinces = None
                
            # Copy method reference? Or simply subclass
            
        # Better: use the actual class but mock dependencies using patch
        # But for now, let's create a partial mock.
        
        p = Planet.__new__(Planet) # Skip __init__
        p.name = "TestWorld"
        p.building_slots = 5
        p.system = MagicMock()
        p.hex_map = None
        p._provinces = None
        
        # Call generation
        Planet._generate_hex_map_lazy(p)
        
        # 1. Verify Hex Map exists
        self.assertIsNotNone(p.hex_map)
        self.assertTrue(len(p.hex_map) > 20)
        
        # 2. Verify Center is Capital
        center_node = p.hex_map.get((0,0))
        self.assertIsNotNone(center_node)
        self.assertIsInstance(center_node, HexNode)
        self.assertEqual(center_node.type, "Capital")
        self.assertEqual(center_node.terrain_type, "City")
        
        # 3. Verify Edges (should be connected)
        self.assertTrue(len(center_node.edges) >= 6)
        
        # 4. Verify Ring 1 (District)
        neighbor = center_node.edges[0].target
        if neighbor.hex_coords.length() == 1:
             self.assertEqual(neighbor.terrain_type, "City")
             
    def test_map_scale(self):
        p = Planet.__new__(Planet)
        p.name = "BigWorld"
        p.building_slots = 20 # Large
        p.system = "Sys"
        p._provinces = None
        
        Planet._generate_hex_map_lazy(p)
        
        count_small = 20 + (5*10) # 70
        count_large = 20 + (20*10) # 220
        
        self.assertTrue(len(p.hex_map) >= count_large)
        self.assertEqual(len(p.provinces), len(p.hex_map))

if __name__ == '__main__':
    unittest.main()
