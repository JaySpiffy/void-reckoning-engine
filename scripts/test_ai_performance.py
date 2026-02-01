import sys
import os
import time
import random

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.managers.campaign_manager import CampaignEngine

def run_performance_test():
    print("=== AI Performance Benchmark ===")
    
    # Setup
    config = {
        "mechanics": {"enable_weather": False, "enable_diplomacy": False},
        "simulation": {"telemetry_level": "off", "random_seed": 42}
    }
    engine = CampaignEngine(game_config=config)
    print("Generating Galaxy (50 Systems)...")
    engine.generate_galaxy(num_systems=50, min_planets=1, max_planets=5)
    
    # Spawn Factions & Fleets
    print("Spawning fleets...")
    engine.spawn_start_fleets()
    
    # Add more fleets to stress test (High load)
    print("Adding stress test fleets...")
    for f in engine.factions:
        if f == "Neutral": continue
        my_planets = engine.planets_by_faction.get(f, [])
        if my_planets:
            planet = my_planets[0]
            for _ in range(10): # +10 fleets per faction
                 engine.create_fleet(f, planet)
             
    print(f"Total Fleets: {len(engine.fleets)}")
    
    # Run Turns
    turn_times = []
    
    print("\nRunning 10 Turns...")
    for i in range(1, 11):
        start = time.perf_counter()
        engine.process_turn()
        elapsed = time.perf_counter() - start
        turn_times.append(elapsed)
        print(f"Turn {i}: {elapsed*1000:.2f}ms")
        
    avg_turn = sum(turn_times) / len(turn_times)
    print(f"\nAverage Turn Time: {avg_turn*1000:.2f}ms")
    
    # Report Metrics
    if hasattr(engine, 'log_performance_metrics'):
        engine.log_performance_metrics()
    
    # Check Caches
    print("\n=== CACHE STATISTICS ===")
    if hasattr(engine.calculate_threat_level, 'cache_info'):
        print(f"calculate_threat_level: {engine.calculate_threat_level.cache_info()}")
    if hasattr(engine.calculate_target_score, 'cache_info'):
        print(f"calculate_target_score: {engine.calculate_target_score.cache_info()}")
    if hasattr(engine.get_cached_intel, 'cache_info'):
        print(f"get_cached_intel: {engine.get_cached_intel.cache_info()}")
        
    if hasattr(engine.strategic_ai.calculate_expansion_target_score, 'cache_info'):
         print(f"StrategicAI.exp_score: {engine.strategic_ai.calculate_expansion_target_score.cache_info()}")

if __name__ == "__main__":
    run_performance_test()
