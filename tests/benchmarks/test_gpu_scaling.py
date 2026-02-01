
import time
import sys
import os
import random
import statistics

# Add src to path
sys.path.append(os.path.join(os.getcwd()))

from src.combat.tactical.gpu_tracker import GPUTracker
from src.models.unit import Unit
from src.core import gpu_utils

class MockUnit:
    def __init__(self, x, y):
        self.grid_x = x
        self.grid_y = y
        self.name = "MockUnit"

def benchmark_scaling():
    print(f"=== GPU Scaling Benchmark ===")
    print(f"Backend: {gpu_utils.get_xp().__name__}")
    
    unit_counts = [100, 500, 1000] # Keep small for quick test, go higher if GPU
    
    results = []
    
    for n in unit_counts:
        print(f"\n--- Testing N={n} ---")
        units = [MockUnit(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(n)]
        
        # 1. Initialize Tracker
        tracker = GPUTracker()
        start_init = time.time()
        tracker.initialize(units)
        end_init = time.time()
        print(f"Initialization: {(end_init - start_init)*1000:.2f} ms")
        
        # 2. Distance Matrix (Vectorized)
        start_matrix = time.time()
        dist_mat = tracker.compute_distance_matrix()
        # Enforce sync if GPU
        if hasattr(dist_mat, 'get'): dist_mat.get() 
        end_matrix = time.time()
        gpu_time = (end_matrix - start_matrix) * 1000
        print(f"Vectorized Matrix: {gpu_time:.2f} ms")
        
        # 3. Legacy Loop (Simulated)
        start_loop = time.time()
        # Simple N*N distance check simulation
        # Only doing 10% of N for larger sets to save time if N is huge
        limit = n if n < 200 else 200 
        cnt = 0
        for i in range(limit):
            u1 = units[i]
            for j in range(n):
                dx = u1.grid_x - units[j].grid_x
                dy = u1.grid_y - units[j].grid_y
                d = (dx*dx + dy*dy)**0.5
                cnt += 1
        end_loop = time.time()
        
        loop_time = (end_loop - start_loop) * 1000
        
        # Extrapolate if we limited
        if limit < n:
            factor = n / limit
            loop_time *= factor
            print(f"Python Loop (Est): {loop_time:.2f} ms")
        else:
            print(f"Python Loop: {loop_time:.2f} ms")
            
        speedup = loop_time / gpu_time if gpu_time > 0 else 0
        print(f"Speedup: {speedup:.1f}x")
        
if __name__ == "__main__":
    benchmark_scaling()
