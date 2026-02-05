import json
import os
import logging
from typing import Dict, List, Any, Optional
from collections import deque

logger = logging.getLogger(__name__)

class DistanceMatrixService:
    """
    R10: Pre-computed Distance Matrix for the Galaxy Map.
    Provides O(1) strategic distance lookups.
    """
    def __init__(self, engine=None):
        self.engine = engine
        self._matrix: Dict[str, Dict[str, float]] = {}
        self._topo_ver = -1

    def ensure_matrix(self):
        """Rebuilds the matrix if the topology has changed."""
        from src.core.simulation_state import SimulationState
        current_ver = SimulationState.get_topology_version()
        if current_ver == self._topo_ver:
            return
        
        self.rebuild_matrix()
        self._topo_ver = current_ver

    def rebuild_matrix(self):
        """Computes all-pairs shortest paths for system nodes (BFS-based for hop counts)."""
        logger.info("[R10] Rebuilding Strategic Distance Matrix...")
        systems = self.engine.galaxy_nodes if hasattr(self.engine, 'galaxy_nodes') else []
        if not systems:
            return

        new_matrix = {}
        for start_sys in systems:
            start_name = start_sys.name
            new_matrix[start_name] = self._compute_bfs_distances(start_sys)
        
        self._matrix = new_matrix
        logger.info(f"[R10] Matrix rebuilt for {len(systems)} systems.")

    def _compute_bfs_distances(self, start_node: Any) -> Dict[str, float]:
        """BFS for unit-cost distances (hops). Can be weighted if useful."""
        distances = {start_node.name: 0.0}
        queue = deque([start_node])
        
        while queue:
            current = queue.popleft()
            curr_dist = distances[current.name]
            
            for edge in getattr(current, 'edges', []):
                neighbor = edge.target
                if neighbor.name not in distances:
                    distances[neighbor.name] = curr_dist + edge.distance
                    queue.append(neighbor)
        
        return distances

    def get_distance(self, system_a: str, system_b: str) -> float:
        """O(1) lookup in pre-computed matrix."""
        self.ensure_matrix()
        return self._matrix.get(system_a, {}).get(system_b, float('inf'))

    def export_data(self, path: str):
        with open(path, 'w') as f:
            json.dump(self._matrix, f)

    def import_data(self, data: Dict):
        self._matrix = data
