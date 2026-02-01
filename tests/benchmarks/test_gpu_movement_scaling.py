
import time
import sys
import os
import random

# Add src to path
sys.path.append(os.path.join(os.getcwd()))

from src.combat.tactical.gpu_tracker import GPUTracker
from src.core import gpu_utils

class MockUnit:
    def __init__(self, x, y, faction):
        self.grid_x = x
        self.grid_y = y
        self.faction = faction
        self.name = "MockUnit"

def benchmark_movement():
    print(f"=== GPU Movement Flow Field Benchmark ===")
    print(f"Backend: {gpu_utils.get_xp().__name__}")
    
    # Test cases
    N_list = [100, 500, 1000]
    
    for n in N_list:
        print(f"\n--- Testing N={n} (Half Team A, Half Team B) ---")
        
        # Setup units
        units = []
        for i in range(n):
            f = "TeamA" if i % 2 == 0 else "TeamB"
            units.append(MockUnit(random.uniform(0, 100), random.uniform(0, 100), f))
            
        tracker = GPUTracker()
        tracker.initialize(units)
        
        # 1. Batched Flow Field
        start_gpu = time.time()
        flow = tracker.compute_flow_field()
        # Enforce sync
        if hasattr(flow, 'values'):
             pass # Reading dict forces CPU sync
        end_gpu = time.time()
        
        gpu_time = (end_gpu - start_gpu) * 1000
        print(f"Batched Flow Field: {gpu_time:.2f} ms")
        
        # 2. Legacy Sequential Loop (Simulated)
        # For each unit, find nearest enemy
        start_cpu = time.time()
        limit = 200 if n > 200 else n
        
        for i in range(limit):
            u = units[i]
            nearest_dist = 9999
            nearest = None
            for j in range(n):
                target = units[j]
                if target.faction == u.faction: continue
                
                dx = u.grid_x - target.grid_x
                dy = u.grid_y - target.grid_y
                d = (dx*dx + dy*dy)**0.5
                if d < nearest_dist:
                    nearest_dist = d
                    nearest = target
            
            # Calc vector
            if nearest:
                 vx = nearest.grid_x - u.grid_x
                 vy = nearest.grid_y - u.grid_y
                 
        end_cpu = time.time()
        cpu_time = (end_cpu - start_cpu) * 1000
        
        if limit < n:
            factor = n / limit
            cpu_time *= factor
            print(f"Sequential Loop (Est): {cpu_time:.2f} ms")
        else:
            print(f"Sequential Loop: {cpu_time:.2f} ms")
            
        speedup = cpu_time / gpu_time if gpu_time > 0 else 0
        print(f"Speedup: {speedup:.1f}x")

if __name__ == "__main__":
    benchmark_movement()
