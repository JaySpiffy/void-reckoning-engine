import sys
import os
sys.path.append(os.getcwd())

from src.managers.campaign_manager import CampaignEngine
from src.core.game_config import GameConfig

print("Starting Integration Verification...")

# Mock config
config_data = {
    "campaign": {
        "turns": 1,
        "num_systems": 5
    }
}
config = GameConfig.from_dict(config_data)

try:
    engine = CampaignEngine(game_config=config)
    engine.generate_galaxy(num_systems=5, min_planets=1, max_planets=2)

    # Sync (Manual call if not relying on simulate_campaign's injection, 
    # but wait! I added the injection to simulate_campaign.py, NOT CampaignEngine.generate_galaxy.
    # So I must call sync here manually to mimic simulate_campaign, OR verify that simulate_campaign works.
    # I'll call it manually here to verify the SERVICE works with the ENGINE state.)
    
    print("Syncing Topology...")
    engine.pathfinder.sync_topology(engine.systems)

    # Check if pathfinder has rust instance
    pf = engine.pathfinder
    if pf._rust_pathfinder:
        print("VERIFICATION SUCCESS: RustPathfinder is active.")
        
        if len(engine.systems) < 2:
            print("Not enough systems to test path.")
        else:
            start = engine.systems[0]
            end = engine.systems[1]
            print(f"Testing path from {start.name} (ID: {start.name}) to {end.name} (ID: {end.name})...")
            
            # Ensure they are connected or at least valid
            # Rust A* might return None if no path.
            
            path, cost, meta = pf.find_path(start, end)
            print(f"Path result: Cost={cost}, Steps={len(path) if path else 0}")
            
            if path:
                print("Path found!")
            else:
                print("No path found (might be disconnected graph), but call succeeded.")
                
    else:
        print("VERIFICATION FAILED: RustPathfinder is None.")

except Exception as e:
    print(f"VERIFICATION ERROR: {e}")
    import traceback
    traceback.print_exc()
