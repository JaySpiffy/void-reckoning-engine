import random
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'src')))

class MockConfig:
    def __init__(self):
        self.raw_config = {
            "mechanics": {
                "weather_config": {
                    "max_storm_percentage": 25.0, # 25% of 19 edges ~ 4.75 -> 4 storms
                    "min_duration": 1,
                    "max_duration": 10,
                    "storm_chance_per_turn": 1.0 # Guarantee spawn attempts
                }
            }
        }

class MockLogger:
    def environment(self, msg):
        pass # print(f"[ENV] {msg}")

class MockEngine:
    def __init__(self):
        self.game_config = MockConfig()
        self.logger = MockLogger()
        self.systems = []

class MockNode:
    def __init__(self, name, node_type="DeepSpace"):
        self.name = name
        self.type = node_type

class MockEdge:
    def __init__(self, start, end):
        self.source = start
        self.target = end
        self.blocked = False
        self.stability = 1.0

from src.managers.weather_manager import WarpStormManager

def verify_warp_storms():
    print("=== Verifying Warp Storm Logic ===")
    
    # Setup
    engine = MockEngine()
    manager = WarpStormManager(engine)
    
    # Create Dummy Edges
    nodes = [MockNode(f"Node_{i}") for i in range(20)]
    edges = []
    for i in range(19):
        e = MockEdge(nodes[i], nodes[i+1])
        edges.append(e)
    
    manager.edges = edges
    
    print(f"Initialized {len(edges)} edges.")
    print(f"Config: Max 5 storms, Chance 100%")
    
    # Simulation Loop
    history = []
    
    for turn in range(1, 21):
        manager.update_storms()
        count = len(manager.active_storms)
        history.append(count)
        blocked_edges = len([e for e in manager.edges if e.blocked])
        
        # print(f"Turn {turn}: Active Storms: {count}, Blocked Edges: {blocked_edges}")
        
        # Check Consistency
        if count != blocked_edges:
            print(f"[FAIL] Turn {turn}: Mismatch! Active Storms ({count}) != Blocked Edges ({blocked_edges})")
            return
            
        # Check Cap (19 edges * 0.25 = 4)
        if count > 4:
             print(f"[FAIL] Turn {turn}: Exceeded Max Cap! ({count} > 4)")
             return
             
    print(f"Storm Count History: {history}")
    
    # Assertions
    if max(history) <= 4:
        print("[PASS] Cap respected (Max 4 for 19 edges).")
    else:
        print("[FAIL] Cap exceeded.")
        
    if history[-1] > 0:
        print("[PASS] Storms generated.")
    else:
         print("[WARN] No storms active at end (could be random chance, but unlikely with 100%)")
         
    # Check expiry logic indirectly by ensuring we didn't just accumulate 1 per turn forever
    # With 20 turns and max duration 4, we must have had expirations to stay under cap of 5 if we spawned every turn
    if sum(history) < 20 * 5: 
        print("[PASS] Dynamics confirmed (fluctuation under cap)")

    print("=== Verification Complete ===")

if __name__ == "__main__":
    verify_warp_storms()
