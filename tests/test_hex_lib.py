import unittest
from src.core.hex_lib import Hex, HexGrid, HEX_DIRECTIONS

class TestHexLib(unittest.TestCase):

    def test_hex_equality(self):
        h1 = Hex(1, -1)
        h2 = Hex(1, -1)
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, Hex(0, 0))

    def test_hex_arithmetic(self):
        h1 = Hex(1, -3)
        h2 = Hex(1, 1)
        # Add
        self.assertEqual(h1 + h2, Hex(2, -2))
        # Sub
        self.assertEqual(h1 - h2, Hex(0, -4))
        # Mul
        self.assertEqual(h2 * 2, Hex(2, 2))
        self.assertEqual(3 * h2, Hex(3, 3))

    def test_distance(self):
        # Hex(0,0) to Hex(0,0) -> 0
        self.assertEqual(Hex(0, 0).distance(Hex(0, 0)), 0)
        # Hex(0,0) to Hex(1,0) -> 1
        self.assertEqual(Hex(0, 0).distance(Hex(1, 0)), 1)
        # Hex(0,0) to Hex(2, -2) -> 2
        self.assertEqual(Hex(0, 0).distance(Hex(2, -2)), 2)

    def test_neighbors(self):
        center = Hex(0, 0)
        neighbors = center.get_neighbors()
        self.assertEqual(len(neighbors), 6)
        # Check explicit neighbor
        self.assertIn(Hex(1, 0), neighbors)
        self.assertIn(Hex(0, 1), neighbors)
        self.assertIn(Hex(-1, 0), neighbors)

    def test_ring(self):
        center = Hex(0, 0)
        # Radius 0
        self.assertEqual(HexGrid.get_ring(center, 0), [center])
        
        # Radius 1 (should be neighbors)
        ring1 = HexGrid.get_ring(center, 1)
        self.assertEqual(len(ring1), 6)
        self.assertIn(Hex(1, 0), ring1)
        
        # Radius 2
        ring2 = HexGrid.get_ring(center, 2)
        # Ring 2 has 6 * 2 = 12 hexes?
        self.assertEqual(len(ring2), 12)
        # 2 units east
        self.assertIn(Hex(2, 0), ring2)

    def test_spiral(self):
        center = Hex(0, 0)
        # Radius 1 spiral = 1 (center) + 6 (ring 1) = 7
        spiral = list(HexGrid.get_spiral(center, 1))
        self.assertEqual(len(spiral), 7)
        self.assertIn(center, spiral)
        self.assertIn(Hex(1, 0), spiral)

if __name__ == '__main__':
    unittest.main()
