
import math
import sys
import os

# Add src to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.models.star_system import StarSystem
from src.models.planet import Planet
from src.core.simulation_topology import GraphNode

from src.core.universe_data import UniverseDataManager
from unittest.mock import MagicMock

def setup_mocks():
    udm = UniverseDataManager.get_instance()
    udm.get_planet_classes = MagicMock(return_value={
        "Terran": {"req_mod": 1.0, "def_mod": 0, "slots": 5},
        "Desert": {"req_mod": 1.0, "def_mod": 0, "slots": 4}
    })

def bfs_distance(start_node, target_node):
    queue = [(start_node, 0)]
    visited = {start_node}
    
    while queue:
        current, dist = queue.pop(0)
        if current == target_node:
            return dist
        
        for edge in current.edges:
            neighbor = edge.target
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + edge.distance))
                
    return float('inf')

def verify_highway_removal():
    print("--- Verifying Map Graph Integrity ---")
    
    # Generate System
    system = StarSystem("TestSys", 0, 0)
    p1 = Planet("P1", system, 1)
    system.add_planet(p1)
    
    
    # Generate Mesh
    system.generate_topology()
    
    print(f"Total Nodes Generated: {len(system.nodes)}")
    
    # Find Nodes
    planet_node = next((n for n in system.nodes if n.type == "Planet"), None)
    warp_gate = next((n for n in system.nodes if n.type == "WarpPoint"), None)
    
    if not planet_node or not warp_gate:
        print("FAIL: Could not find planet or warp gate nodes.")
        return
        
    print(f"Planet Node: {planet_node.name}")
    print(f"Warp Gate: {warp_gate.name}")
    
    # Check Direct Edge
    direct_link = any(e.target == warp_gate for e in planet_node.edges)
    if direct_link:
        print("FAIL: Direct edge (Highway) still exists!")
        edge = next(e for e in planet_node.edges if e.target == warp_gate)
        print(f"Edge Distance: {edge.distance}")
    else:
        print("PASS: No direct edge found.")
        
    # Calculate Travel Cost
    dist = bfs_distance(planet_node, warp_gate)
    print(f"Shortest Path Distance: {dist}")
    
    # CHOKE POINT VERIFICATION
    hubs = [n for n in system.nodes if "[HUB]" in n.name]
    print(f"Hub Nodes Found: {len(hubs)}")
    
    # Check Connectivity Profile
    hub_edges = sum(len(n.edges) for n in hubs) / max(1, len(hubs))
    regular_nodes = [n for n in system.nodes if "[HUB]" not in n.name]
    reg_edges = sum(len(n.edges) for n in regular_nodes) / max(1, len(regular_nodes))
    
    print(f"Avg Hub Connectivity: {hub_edges:.2f}")
    print(f"Avg Regular Connectivity: {reg_edges:.2f}")
    
    if hub_edges > reg_edges * 1.5:
         print("PASS: Hubs significantly more connected than regular nodes (Choke Points created).")
    else:
         print("FAIL: Connectivity profile too uniform.")

if __name__ == "__main__":
    setup_mocks()
    verify_highway_removal()
