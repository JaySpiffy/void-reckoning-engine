
import sys
import os
import time
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.star_system import StarSystem

def verify_topology():
    print("Verifying Topology Generation (NumPy Impl)...")
    
    # Setup
    sys_obj = StarSystem("Test System", 0, 0)
    
    # Measure Generation Time
    start_time = time.time()
    nodes = sys_obj.generate_topology(force=True)
    duration = time.time() - start_time
    
    print(f"  - Generation Time (300 nodes): {duration*1000:.2f} ms")
    
    # 1. Verify Node Count
    assert len(nodes) == 300, f"Expected 300 nodes, got {len(nodes)}"
    print(f"  - Node Count: {len(nodes)} (PASS)")
    
    # 2. Verify Connectivity
    total_edges = sum(len(n.edges) for n in nodes)
    avg_edges = total_edges / 300
    print(f"  - Total Edges: {total_edges}")
    print(f"  - Avg Degree: {avg_edges:.2f}")
    
    assert total_edges > 300, "Graph is too sparse, edges likely failed."
    
    # 3. Verify Hubs
    hubs = [n for n in nodes if n.metadata.get("is_hub")]
    print(f"  - Hub Count: {len(hubs)}")
    assert len(hubs) > 0, "No hubs identified."
    
    # 4. Verify Spatial Coherence (Sanity Check)
    # Pick a random node and check if its neighbors are actually close
    sample = nodes[50]
    if sample.edges:
        edge = sample.edges[0]
        target = edge.target
        dist_calc = np.sqrt( (sample.position[0]-target.position[0])**2 + (sample.position[1]-target.position[1])**2 )
        print(f"  - Sample Edge Dist: {dist_calc:.2f} (Cost: {edge.distance})")
        # Scale is 6.0, close neighbors should be small dist
        assert dist_calc < 20.0, "Connected neighbor is suspiciously far."

    print("Topology Verification: PASS")

if __name__ == "__main__":
    verify_topology()
