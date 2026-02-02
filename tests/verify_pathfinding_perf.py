
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.simulation_state import SimulationState
from src.services.pathfinding_service import PathfindingService
from src.core.simulation_topology import GraphNode

def verify():
    print("Verifying Pathfinding Smart Caching...")
    
    # Reset State
    SimulationState.reset()
    pf = PathfindingService()
    
    # Mock Nodes
    n1 = GraphNode("n1", "DeepSpace")
    n1.position = (0, 0)
    n2 = GraphNode("n2", "DeepSpace")
    n2.position = (10, 0)
    
    # Edge
    n1.add_edge(n2, distance=10)
    
    # 1. First Call (Cold)
    print("1. Testing Cold Cache...")
    path, cost, _ = pf.find_cached_path(n1, n2)
    assert path is not None
    assert pf._stats["misses"] == 1
    assert pf._stats["hits"] == 0
    print("   PASS")
    
    # 2. Second Call (Warm - Same Turn/Version)
    print("2. Testing Warm Cache (Intra-turn)...")
    path, cost, _ = pf.find_cached_path(n1, n2)
    assert pf._stats["hits"] == 1
    print("   PASS")
    
    # 3. Simulate Turn Change WITHOUT Topology Change
    print("3. Testing Smart Persistence (Cross-turn)...")
    # Simulate clear_cache call that happens at turn start
    pf.clear_cache()
    
    # Use cache again - should still be hit because versions didn't change
    path, cost, _ = pf.find_cached_path(n1, n2)
    
    if pf._stats["hits"] != 2:
        print(f"   FAILURE: Expected 2 hits, got {pf._stats['hits']}. Misses: {pf._stats['misses']}")
        print(f"   Cache Stats: {pf.cache_stats}")
        sys.exit(1)
    else:
        print("   PASS")

    # 4. Simulate Topology Change
    print("4. Testing Invalidation (Topology Change)...")
    SimulationState.inc_topology_version()
    
    # Scenario A: Mid-Turn Change (No clear_cache call)
    # The key should change, forcing a miss
    path, cost, _ = pf.find_cached_path(n1, n2)
    
    # We expect a miss here because the key (ver 1) != key (ver 0)
    if pf._stats["misses"] != 2:
         print(f"   FAILURE (Mid-Turn): Expected 2 misses, got {pf._stats['misses']}")
         sys.exit(1)
    print("   PASS (Mid-Turn Invalidation)")
         
    # Scenario B: Turn Boundary after Change
    pf.clear_cache() # Should now wipe because local version != global version
    
    # Mocking internal state check...
    # If we check the dict size, it should be empty/small
    # But let's verify via behavior
    
    pf.find_cached_path(n1, n2)
    # This is a miss because cache was wiped (or key is new anyway, and old key is gone)
    if pf._stats["misses"] != 3:
         print(f"   FAILURE (Post-Clear): Expected 3 misses, got {pf._stats['misses']}")
         sys.exit(1)
         
    print("   PASS (Post-Clear Invalidation)")
    
    print("-" * 20)
    print("Smart Caching Verified Successfully.")

if __name__ == "__main__":
    verify()
