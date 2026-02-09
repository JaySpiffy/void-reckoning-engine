import sys
import os
import unittest
import shutil
import random
import time

# Fix path to include project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.config import SAVES_DIR 
from src.managers.campaign_manager import CampaignEngine
from src.utils.rng_manager import RNGManager

class TestDeterministicReplay(unittest.TestCase):
    def setUp(self):
        # Clean up snapshots
        self.snapshots_dir = os.path.join(SAVES_DIR, "snapshots")
        if os.path.exists(self.snapshots_dir):
            shutil.rmtree(self.snapshots_dir)
        os.makedirs(self.snapshots_dir)
        
        # Reset RNG
        self.seed = 42
        RNGManager.get_instance().reseed_all(self.seed)
        
    def test_replay_determinism(self):
        print("\n[Test] Starting Deterministic Replay Verification...")
        
        # Run 1: Initial Run
        # ------------------
        engine = CampaignEngine(universe_name="void_reckoning")
        # Initialize basic state (mocking a game start)
        engine.turn_counter = 0
        
        # Run for 5 turns
        print("Running initial simulation (Turns 1-5)...")
        for _ in range(5):
            engine.turn_counter += 1
            engine.turn_processor.process_faction_turns()
            
        # Capture Snapshot at Turn 5
        print("Capturing Snapshot at Turn 5...")
        snap_id = engine.snapshot_manager.create_snapshot(label="mid_game")
        self.assertIsNotNone(snap_id)
        
        # Capture State at Turn 5 (Control)
        state_t5 = self._capture_comparison_state(engine)
        
        # Run for 5 more turns (Total 10)
        print("Running simulation (Turns 6-10)...")
        for _ in range(5):
            engine.turn_counter += 1
            engine.turn_processor.process_faction_turns()
            
        state_t10_original = self._capture_comparison_state(engine)
        
        # Dynamic Faction Check
        check_faction = list(state_t10_original['factions'].keys())[0] if state_t10_original['factions'] else "None"
        req_val = state_t10_original['factions'][check_faction]['requisition'] if check_faction != "None" else 0
        print(f"End of Run 1. {check_faction} req: {req_val}")
        
        # Run 2: Replay from Turn 5
        # -------------------------
        print("\nStarting Replay from Turn 5...")
        
        # Create fresh engine
        engine_replay = CampaignEngine(universe_name="void_reckoning")
        
        # Restore Snapshot
        success = engine_replay.snapshot_manager.restore_snapshot(snap_id)
        self.assertTrue(success, "Snapshot restoration failed")
        
        # Verify State at T5 matches
        state_t5_replay = self._capture_comparison_state(engine_replay)
        self.assertEqual(state_t5, state_t5_replay, "State mismatch immediately after restore!")
        print("State comparison after restore: MATCH")
        
        # Run for 5 more turns (Replay)
        print("Running Replay (Turns 6-10)...")
        for _ in range(5):
            engine_replay.turn_counter += 1
            engine_replay.turn_processor.process_faction_turns()
            
        state_t10_replay = self._capture_comparison_state(engine_replay)
        
        # Compare Final States
        # Compare Final States
        req_val_replay = state_t10_replay['factions'][check_faction]['requisition'] if check_faction != "None" else 0
        print(f"End of Replay. {check_faction} req: {req_val_replay}")
        
        self.assertEqual(state_t10_original, state_t10_replay, "DETERMINISM FAIL: Replay state does not match original run!")
        print("SUCCESS: Replay is bit-perfectly deterministic.")

    def _capture_comparison_state(self, engine):
        """Captures a simplified state dict for equality checking."""
        state = {
            "turn": engine.turn_counter,
            "factions": {},
            "fleets": len(engine.fleets),
            "rng": RNGManager.get_instance().get_all_states() # Critical
        }
        
        for f in engine.get_all_factions():
            state["factions"][f.name] = {
                "requisition": f.requisition,
                "techs": len(f.unlocked_techs),
                "planets": len(engine.galaxy_manager.get_planets_by_owner(f.name))
            }
            
        return state

if __name__ == "__main__":
    unittest.main()
