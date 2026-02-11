
import os
import sys
import cProfile
import pstats
import io
import time
import json

# Add src to path
sys.path.append(os.getcwd())

from src.managers.campaign_manager import CampaignEngine
from src.core.game_config import GameConfig, MultiUniverseConfig
from src.observability.snapshot_manager import SnapshotManager
from src.core.config import set_active_universe

def profile_snapshot(snapshot_id):
    universe = "void_reckoning"
    set_active_universe(universe)
    
    print(f"Loading config for {universe}...")
    try:
        with open("config/void_reckoning_config.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Config file not found.")
        return

    # Handle Multi-Universe Config
    if data.get("mode") == "multi":
        mu_config = MultiUniverseConfig.from_dict(data)
        game_config = None
        for u in mu_config.universes:
            if u.name == universe:
                game_config = GameConfig.from_dict(u.game_config)
                break
        if not game_config:
            print("Universe config not found, using raw.")
            game_config = GameConfig.from_dict(data) 
    else:
        game_config = GameConfig.from_dict(data)

    print(f"Initializing Engine...")
    # Initialize Engine (Telemtry/Organizer can be None for profiling)
    engine = CampaignEngine(game_config=game_config, universe_name=universe)
    
    # 2. Restore Snapshot
    print(f"Restoring snapshot: {snapshot_id}...")
    snap_mgr = SnapshotManager(engine)
    
    success = snap_mgr.restore_snapshot(snapshot_id)
    
    if not success:
        print("Failed to restore snapshot.")
        return
        
    print(f"Snapshot restored. Turn: {engine.turn_counter}")
    print(f"Factions: {len(engine.factions)}")
    print(f"Fleets: {len(engine.fleets)}")
    
    # 3. Profile Turn
    print("Profiling process_turn()...")
    pr = cProfile.Profile()
    pr.enable()
    
    start_time = time.time()
    engine.process_turn()
    end_time = time.time()
    
    pr.disable()
    
    print(f"Turn processed in {end_time - start_time:.4f} seconds.")
    
    # 4. Analyze Results
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(60)
    
    print(s.getvalue())
    
    # Save to file
    with open("profile_results.txt", "w") as f:
        f.write(s.getvalue())

if __name__ == "__main__":
    profile_snapshot("turn_183_snap_183_1770707936")
