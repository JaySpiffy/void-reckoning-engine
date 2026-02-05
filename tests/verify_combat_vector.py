
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.combat.tactical.gpu_tracker import GPUTracker
from src.models.unit import Unit
from src.core import gpu_utils

class TestCombatVectorization(unittest.TestCase):
    def setUp(self):
        # Create mock units
        self.u1 = MagicMock(spec=Unit)
        self.u1.grid_x = 10
        self.u1.grid_y = 20
        self.u1.hp = 100
        self.u1.max_hp = 100
        self.u1.faction = "Empire"
        self.u1.tags = []
        
        self.u2 = MagicMock(spec=Unit)
        self.u2.grid_x = 30
        self.u2.grid_y = 40
        self.u2.hp = 50
        self.u2.max_hp = 100
        self.u2.faction = "Rebels"
        self.u2.tags = ["Starbase"]
        
        self.tracker = GPUTracker()
        self.tracker.initialize([self.u1, self.u2])

    def test_initial_state(self):
        print("\n[R7] Testing Initial GPU State...")
        xp = gpu_utils.get_xp()
        
        # Check Positions
        pos = gpu_utils.to_cpu(self.tracker.positions)
        print(f"Initial Pos: {pos}")
        self.assertEqual(pos[0][0], 10)
        self.assertEqual(pos[0][1], 20)
        
        # Check HPs
        hps = gpu_utils.to_cpu(self.tracker.hps)
        print(f"Initial HPs: {hps}")
        self.assertEqual(hps[0], 100)
        self.assertEqual(hps[1], 50)
        
        # Check Weights (Starbase should be higher)
        weights = gpu_utils.to_cpu(self.tracker.priority_weights)
        print(f"Weights: {weights}")
        self.assertEqual(weights[0], 1.0)
        self.assertEqual(weights[1], 5.0)

    def test_batch_snapshot(self):
        print("\n[R8] Testing Batch Snapshot...")
        # Move units
        self.u1.grid_x = 15
        self.u1.hp = 80
        
        self.u2.grid_y = 45
        self.u2.hp = 20
        
        self.tracker.batch_snapshot([self.u1, self.u2])
        
        # Verify
        pos = gpu_utils.to_cpu(self.tracker.positions)
        hps = gpu_utils.to_cpu(self.tracker.hps)
        
        print(f"Updated Pos: {pos}")
        print(f"Updated HPs: {hps}")
        
        self.assertEqual(pos[0][0], 15)
        self.assertEqual(pos[1][1], 45)
        self.assertEqual(hps[0], 80)
        self.assertEqual(hps[1], 20)

if __name__ == "__main__":
    unittest.main()
