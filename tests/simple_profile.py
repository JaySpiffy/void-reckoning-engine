
import sys
import os
import time
import statistics

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.game_config import GameConfig
from src.managers.campaign_manager import CampaignEngine

def benchmark():
    print("Starting Benchmark...")
    
    # 1. Setup
    config = GameConfig(
        num_systems=50,
        max_turns=20,
        min_planets_per_system=1,
        max_planets_per_system=5,
        starting_fleets=1,
        performance_logging_level="detailed",
        performance_profile_methods=True
    )
    
    engine = CampaignEngine(game_config=config)
    
    # 2. Galaxy Generation
    t0 = time.time()
    engine.generate_galaxy(num_systems=50, min_planets=1, max_planets=5)
    gen_time = time.time() - t0
    print(f"Galaxy Generation (50 systems): {gen_time*1000:.2f}ms")
    
    engine.spawn_start_fleets(1)
    
    # 3. Warmup
    print("Warming up (2 turns)...")
    for _ in range(2):
        engine.process_turn()
        
    # 4. Profile Turns
    print("Profiling 10 turns...")
    timings = []
    for i in range(10):
        t0 = time.time()
        engine.process_turn()
        dt = (time.time() - t0) * 1000
        timings.append(dt)
        print(f"  Turn {i+1}: {dt:.2f}ms")
        
    avg = statistics.mean(timings)
    stdev = statistics.stdev(timings) if len(timings) > 1 else 0
    
    print("-" * 30)
    print(f"Average Turn Time: {avg:.2f}ms +/- {stdev:.2f}ms")
    print(f"Total Time (10 turns): {sum(timings):.2f}ms")
    print("-" * 30)

if __name__ == "__main__":
    benchmark()
