
import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from src.core.simulation_topology import GraphNode
from src.core.simulation_state import SimulationState

class StarSystem:
    def __init__(self, name, x, y):
        """
        Initializes a Star System entity.
        
        Args:
            name (str): The display name of the system.
            x (int): Galactic X coordinate.
            y (int): Galactic Y coordinate.
        """
        self.name = name
        self.x = x # Galactic X
        self.y = y # Galactic Y
        self.planets = []
        self.connections = [] # Connected Systems (Flux Lanes)
        self.owner = "Neutral" # System controller (optional)
        
        # Phase 15: Graph Topology
        self.nodes = [] # List of GraphNode
        self.flux_points = [] # Access to Galaxy Map
        
        # Phase 14: Starbase System
        self.starbases = [] # List of Starbase units in the system
        
        # Performance Cache
        self._topology_cached: Optional[List[GraphNode]] = None

    def add_planet(self, planet):
        self.planets.append(planet)
        
    def generate_topology(self, force=False):
        """
        Generates the internal System Graph using a Spiral Mesh Algorithm (Golden Angle Distribution).
        
        Creates ~100 nodes distributed organically, connected via KNN Mesh.
        """
        if self._topology_cached is not None and not force:
            return self._topology_cached

        self.nodes = []
        self.flux_points = []
        
        # Configuration
        num_nodes = 300 # Scaled up for "Grand Strategy" feel (User Request)
        scale = 6.0 # Scale factor for spiral
        
        # 1. Generate Spiral Nodes
        temp_nodes = []
        
        for i in range(num_nodes):
            # Golden Angle Spiral
            angle = i * (math.pi * (3.0 - math.sqrt(5.0))) # Golden Angle ~2.399 rad
            radius = math.sqrt(i) * scale
            
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            # Node Type Determination
            n_type = "DeepSpace"
            n_name = f"Sector {self.name}-{i}"
            
            # Special Nodes
            if i == 0:
                n_type = "Star"
                n_name = f"{self.name} Primary Star"
            elif i >= num_nodes - 5: # Phase 40: Increased Gates to 5
                n_type = "FluxPoint" # Outer edge gates
                n_name = f"Flux Gate {i}"
            
            # Assign Planets to specific indices (Spiral Arms)
            # e.g., Index 10, 25, 45, 70...
            # We need to map `self.planets` to these nodes
            planet_obj = None
            
            # Distribute planets along the spiral
            if self.planets:
                # Calculate indices for planets
                planet_indices = []
                step = num_nodes // (len(self.planets) + 1)
                for k in range(len(self.planets)):
                    planet_indices.append((k+1) * step)
                
                if i in planet_indices:
                    p_idx = planet_indices.index(i)
                    if p_idx < len(self.planets):
                        planet_obj = self.planets[p_idx]
                        n_type = "Planet"
                        n_name = planet_obj.name
            
            # Flavor types for filler
            if n_type == "DeepSpace":
                roll = i % 10
                if roll == 0: n_type = "AsteroidField"
                elif roll == 1: n_type = "Nebula"
            
            node = GraphNode(n_name, n_type, n_name)
            node.position = (x, y)
            node.metadata["system"] = self
            
            if planet_obj:
                node.metadata["object"] = planet_obj
                planet_obj.node_reference = node
                
            if n_type == "FluxPoint":
                self.flux_points.append(node)
                
            self.nodes.append(node)
            temp_nodes.append(node)

        # 2. Connect Mesh (Hub-and-Spoke Choke Points)
        # To create "Choke Points", we limit global connectivity and force travel through Hubs.
        
        # 2. Connect Mesh (Hub-and-Spoke Choke Points) using NumPy
        # Extract positions for vectorized calculation
        positions = np.array([n.position for n in temp_nodes])
        
        # Calculate all-pairs squared Euclidean distance
        # (N, 1, 2) - (1, N, 2) -> (N, N, 2) -> sum -> (N, N)
        diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
        dist_sq_matrix = np.sum(diff**2, axis=-1)

        # Identify hubs early for logic
        hubs = [n for i, n in enumerate(temp_nodes) if i % 30 == 0 or i == 0 or n.type == "FluxPoint"]
        for h in hubs:
            h.metadata["is_hub"] = True
            h.name += " [HUB]"
            
        for i, node in enumerate(temp_nodes):
            is_hub = node.metadata.get("is_hub", False)
            k_neighbors = 6 if is_hub else 2
            
            # Get sorted indices of neighbors by distance
            # N=300 is small enough that full sort is efficient and simpler than argpartition+sort
            sorted_indices = np.argsort(dist_sq_matrix[i])
            
            connected = 0
            
            # Iterate through sorted neighbors (skipping self at index 0 which has dist 0)
            for neighbor_idx in sorted_indices:
                if neighbor_idx == i:
                    continue
                    
                if connected >= k_neighbors:
                    break
                
                other = temp_nodes[neighbor_idx]
                dist_sq = dist_sq_matrix[i, neighbor_idx]
                phys_dist = math.sqrt(dist_sq)

                # CHOKE POINT ENFORCEMENT
                is_other_hub = other.metadata.get("is_hub", False)
                
                # Logic:
                # 1. Always connect very close neighbors (Visual coherence)
                # 2. Prefer connecting to Hubs (Funneling)
                # 3. Avoid long-range connections between two non-hubs (Bypasses choke points)
                if not is_hub and not is_other_hub:
                     if phys_dist > (scale * 2.0):
                         continue # Block long "bypass" edges
                
                # Check for existing edge to avoid duplicates (though our logic iterates unique nodes usually)
                # Note: node.edges contains Edge objects where edge.target is the other node
                has_edge = any(e.target == other for e in node.edges)
                if not has_edge:
                    cost = max(1, int(phys_dist))
                    
                    if node.type == "Nebula" or other.type == "Nebula": cost = int(cost * 2.0)
                    if node.type == "AsteroidField" or other.type == "AsteroidField": cost = int(cost * 1.5)
                    
                    node.add_edge(other, distance=cost)
                    other.add_edge(node, distance=cost)
                    connected += 1

        self._topology_cached = self.nodes
        SimulationState.inc_topology_version() # Optimization 5.1
        return self.nodes



    def get_primary_node(self) -> GraphNode:
        """Returns the central Star node (Node 0)."""
        if self.nodes:
            return self.nodes[0]
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes star system state for Save V2."""
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "owner": self.owner,
            "planets": [p.to_dict() for p in self.planets],
            "nodes": [n.to_dict() for n in self.nodes] if self.nodes else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StarSystem':
        """Hydrates a StarSystem from a dictionary (Save V2)."""
        system = cls(
            name=data["name"],
            x=data["x"],
            y=data["y"]
        )
        system.owner = data.get("owner", "Neutral")
        
        # Nodes hydration
        node_data = data.get("nodes")
        if node_data:
            from src.core.simulation_topology import GraphNode
            system.nodes = [GraphNode.from_dict(n) for n in node_data]
            
        # Planets hydration
        planet_data = data.get("planets", [])
        from src.models.planet import Planet
        system.planets = [Planet.from_dict(p, system) for p in planet_data]
        
        return system
