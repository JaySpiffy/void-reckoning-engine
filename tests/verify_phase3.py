
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.distance_matrix import DistanceMatrixService
from src.services.pathfinding_service import PathfindingService
from src.core.simulation_topology import GraphNode, GraphEdge

class TestPhase3Optimizations(unittest.TestCase):
    def setUp(self):
        # Create a simple 3-system graph: A - B - C
        self.node_a = GraphNode("A", "System", "System A")
        self.node_b = GraphNode("B", "System", "System B")
        self.node_c = GraphNode("C", "System", "System C")
        
        # Connect A <-> B
        self.node_a.add_bidirectional_edge(self.node_b, 10.0)
        
        # Connect B <-> C
        self.node_b.add_bidirectional_edge(self.node_c, 10.0)
        
        # Mock Engine
        self.engine = MagicMock()
        self.engine.galaxy_nodes = [self.node_a, self.node_b, self.node_c]
        
        self.dist_service = DistanceMatrixService(self.engine)
        self.pathfinder = PathfindingService()
        self.pathfinder.set_distance_service(self.dist_service)

    def test_distance_matrix_logic(self):
        print("\n[R10] Testing Distance Matrix...")
        self.dist_service.rebuild_matrix()
        
        dist_ac = self.dist_service.get_distance("System A", "System C")
        print(f"Distance A -> C: {dist_ac} (Expected 20.0)")
        self.assertEqual(dist_ac, 20.0)
        
        dist_aa = self.dist_service.get_distance("System A", "System A")
        self.assertEqual(dist_aa, 0.0)

    def test_pathfinding_heuristic(self):
        print("\n[R9] Testing Pathfinding Heuristic...")
        self.dist_service.rebuild_matrix()
        
        # Use metadata for system assignment (since property is readonly)
        self.node_a.metadata["system"] = self.node_a
        self.node_b.metadata["system"] = self.node_b
        self.node_c.metadata["system"] = self.node_c
        
        path, cost, meta = self.pathfinder.find_path(self.node_a, self.node_c)
        print(f"Path A -> C: {[n.name for n in path]} Cost: {cost}")
        
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 3)
        self.assertEqual(cost, 20.0)

if __name__ == "__main__":
    unittest.main()
