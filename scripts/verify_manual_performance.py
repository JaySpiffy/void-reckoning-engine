
import os
import sys
import time

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.managers.campaign_manager import CampaignEngine
from src.core.game_config import GameConfig

def verify_performance():
    print("Initializing Engine for Performance Verification...")
    
    # Custom config
    config_dict = {
        "simulation": {
            "telemetry_level": "summary"
        },
        "performance": {
            "logging_level": "detailed",
            "log_interval": 1,
            "profile_methods": True
        }
    }
    
    config = GameConfig.from_dict(config_dict)
    engine = CampaignEngine(game_config=config)
    
    print("Generating Galaxy...")
    engine.generate_galaxy(num_systems=5, min_planets=1, max_planets=2)
    engine.spawn_start_fleets()
    
    print("Running 3 Turns...")
    for i in range(3):
        print(f"  Turn {i+1}...")
        engine.process_turn()
        
    print("\nVerifying Metrics...")
    
    # 1. Check Engine Metrics
    if engine.performance_metrics:
        print("  [PASS] Engine.performance_metrics is populated:")
        for k, v in engine.performance_metrics.items():
            count = len(v)
            avg = sum(v)/count if count else 0
            print(f"    - {k}: {count} calls, avg {avg*1000:.2f}ms")
    else:
        print("  [FAIL] Engine.performance_metrics is EMPTY.")
        
    # 2. Check Telemetry
    # We can check the buffer if it hasn't flushed yet, or check the file
    if engine.telemetry:
        # Force flush
        engine.telemetry.flush()
        log_file = engine.telemetry.log_file
        if os.path.exists(log_file):
             print(f"  [PASS] Telemetry log file created: {log_file}")
             # Read it to find performance_summary
             found_summary = False
             with open(log_file, 'r') as f:
                 for line in f:
                     if "performance_summary" in line:
                         found_summary = True
                         break
             if found_summary:
                 print("  [PASS] Found 'performance_summary' event in telemetry log.")
             else:
                 print("  [WARNING] 'performance_summary' event NOT found in telemetry log (Level issue?).")
        else:
             print(f"  [FAIL] Telemetry log file NOT found at {log_file}.")
             
    print("\nVerification Complete.")

if __name__ == "__main__":
    verify_performance()
