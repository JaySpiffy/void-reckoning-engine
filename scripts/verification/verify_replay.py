
import sys
import os
import time
import logging

# Ensure src is in path
sys.path.append(os.getcwd())

from src.managers.campaign_manager import CampaignEngine
from src.observability.snapshot_manager import SnapshotManager
from src.observability.replay_engine import ReplayEngine
from src.utils.game_logging import GameLogger

def run_verification():
    print("--- Deterministic Replay Verification ---")
    
    # Setup Logging to console
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # 1. Initialize Engine
    print("1. Initializing CampaignEngine...")
    engine = CampaignEngine(universe_name="void_reckoning")
    # Initialize basic components if needed strictly for test
    # (Assuming __init__ does enough for a runnable state or run_turn handles it)
    
    # 2. Run Initial Phase (Turns 1-5)
    print("2. Running Turns 1-5...")
    for _ in range(5):
        engine.process_turn()
        
    # 3. Take Snapshot
    print(f"3. Taking Snapshot at Turn {engine.turn_counter}...")
    sm = SnapshotManager(engine)
    snapshot_id = sm.create_snapshot("verify_replay")
    
    if not snapshot_id:
        print("CRITICAL FAILURE: Snapshot creation failed.")
        return
        
    print(f"   Snapshot ID: {snapshot_id}")
    
    # 4. Run 'Future' Phase (Turns 6-10) - THE CONTROL GROUP
    print("4. Running Turns 6-10 (Control Run)...")
    control_log = []
    
    for _ in range(5):
        engine.process_turn()
        # Capture state hash manually for verify script
        state_hash = _calculate_hash(engine)
        control_log.append({
            "turn": engine.turn_counter,
            "state_hash": state_hash
        })
        print(f"   Turn {engine.turn_counter} Hash: {state_hash}")
        
    # 5. Initialize Replay
    print("5. Initializing ReplayEngine...")
    # Create a NEW engine instance to prove independence
    # But wait, ReplayEngine takes an engine instance. 
    # To test properly, we should probably reset the engine or create a new one.
    # Let's create a fresh engine for replay.
    replay_engine_instance = CampaignEngine(universe_name="void_reckoning")
    # Note: We don't strictly need to initialize_campaign because restore_snapshot should overwrite state.
    # But some stateless singletons might persist if not careful. 
    # Using a new process would be safest, but new instance is second best.
    
    replayer = ReplayEngine(replay_engine_instance)
    
    # 6. Load Snapshot
    print(f"6. Loading Snapshot {snapshot_id}...")
    if not replayer.load_snapshot(snapshot_id):
        print("CRITICAL FAILURE: Snapshot load failed.")
        return
        
    print(f"   Replay Engine at Turn: {replay_engine_instance.turn_counter}")
    if replay_engine_instance.turn_counter != 5:
        print(f"   MISMATCH: Expected Turn 5, got {replay_engine_instance.turn_counter}")
        
    # 7. Run Replay (Turns 6-10) - THE EXPERIMENTAL GROUP
    print("7. Running Replay (Turns 6-10)...")
    replayer.is_replaying = True # Force flag just in case load_snapshot didn't set it (it should)
    
    # Manually step to verify against control log
    success = True
    for entry in control_log:
        target_turn = entry['turn']
        control_hash = entry['state_hash']
        
        replayer.step(1)
        
        replay_hash = _calculate_hash(replay_engine_instance)
        print(f"   Replay Turn {replay_engine_instance.turn_counter} Hash: {replay_hash}")
        
        if replay_hash != control_hash:
            print(f"CRITICAL FAILURE: Mismatch at Turn {target_turn}!")
            print(f"   Control: {control_hash}")
            print(f"   Replay:  {replay_hash}")
            success = False
            break
            
    if success:
        print("\nSUCCESS: Replay matched Control run exactly.")
        print("Deterministic Replay VERIFIED.")
    else:
        print("\nFAILURE: Replay divergence detected.")

def _calculate_hash(engine):
    """
    Independent hash calculation for verification script.
    """
    import hashlib
    hasher = hashlib.md5()
    
    # Hash Faction Resources (Key State)
    if hasattr(engine, 'factions'):
        for f_id in sorted(engine.factions.keys()):
            faction = engine.factions[f_id]
            hasher.update(str(f_id).encode())
            
            res = getattr(faction, 'resources', {})
            if hasattr(res, 'to_dict'): res = res.to_dict()
            elif hasattr(res, '__dict__'): res = res.__dict__
            
            if isinstance(res, dict):
                hasher.update(str(sorted(res.items())).encode())
            else:
                hasher.update(str(res).encode())
                
    # Hash Fleet Positions
    if hasattr(engine, 'fleets'):
        sorted_fleets = sorted(engine.fleets, key=lambda f: f.id)
        for fleet in sorted_fleets:
            hasher.update(str(fleet.id).encode())
            loc = getattr(fleet, 'location', 'unknown')
            if hasattr(loc, 'id'): loc = loc.id
            hasher.update(str(loc).encode())
            
    return hasher.hexdigest()

if __name__ == "__main__":
    run_verification()
