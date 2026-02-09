import os
import time
import logging
import hashlib
from typing import Any, Dict, Optional, List
from src.core.config import SAVES_DIR
from src.observability.snapshot_manager import SnapshotManager
from src.utils.rng_manager import RNGManager

class ReplayEngine:
    """
    Engine for deterministic replay of simulation snapshots.
    Loads a snapshot and resumes the simulation loop from that exact point.
    """
    
    def __init__(self, engine: Any):
        self.engine = engine
        self.logger = getattr(engine, 'logger', logging.getLogger(__name__))
        self.snapshot_manager = SnapshotManager(engine)
        self.is_replaying = False
        self.original_log = []
        self.replay_log = []

    def load_snapshot(self, snapshot_id: str) -> bool:
        """
        Loads the specified snapshot and prepares the engine for replay.
        """
        self.logger.info(f"ReplayEngine: Loading snapshot {snapshot_id}...")
        success = self.snapshot_manager.restore_snapshot(snapshot_id)
        if success:
            self.is_replaying = True
            self.logger.info(f"ReplayEngine: Snapshot loaded. Current Turn: {self.engine.turn_counter}")
        else:
            self.logger.error(f"ReplayEngine: Failed to load snapshot {snapshot_id}")
        return success

    def step(self, turns: int = 1):
        """
        Advances the simulation by a specified number of turns strictly deterministically.
        """
        if not self.is_replaying:
            self.logger.warning("ReplayEngine: Not in replay mode. Call load_snapshot first.")
            return

        start_turn = self.engine.turn_counter
        end_turn = start_turn + turns
        
        self.logger.info(f"ReplayEngine: Stepping from Turn {start_turn} to {end_turn}...")
        
        for _ in range(turns):
            # Capture telemetry before step (optional, for granular diffs)
            
            # Execute Engine Step
            if hasattr(self.engine, 'process_turn'):
                self.engine.process_turn()
            elif hasattr(self.engine, 'update'): # Common game loop name
                self.engine.update()
            else:
                 self.logger.error("ReplayEngine: Engine has no known step method (process_turn/update).")
                 return

            # Capture post-turn telemetry for verification
            state_hash = self._calculate_state_hash()
            self.replay_log.append({
                "turn": self.engine.turn_counter,
                "state_hash": state_hash
            })

        self.logger.info(f"ReplayEngine: Replay step complete. Now at Turn {self.engine.turn_counter}")

    def run_to(self, target_turn: int):
        """
        Runs the replay until the target turn is reached.
        """
        if self.engine.turn_counter >= target_turn:
            self.logger.warning(f"ReplayEngine: Already at or past target turn {target_turn} (Current: {self.engine.turn_counter})")
            return

        turns_to_run = target_turn - self.engine.turn_counter
        self.step(turns_to_run)

    def verify_determinism(self, original_log: List[Dict]) -> bool:
        """
        Compares the current replay log with an original run's log.
        Returns True if they match exactly.
        """
        self.logger.info("ReplayEngine: Verifying determinism...")
        match = True
        
        # Create a map of the original log for easy lookup
        # Each entry is expected to be dict(turn=X, state_hash=Y)
        orig_map = {entry['turn']: entry['state_hash'] for entry in original_log}
        
        if not self.replay_log:
            self.logger.warning("ReplayEngine: Replay log is empty. Did you run step()?")
            return False

        for entry in self.replay_log:
            turn = entry['turn']
            replay_hash = entry['state_hash']
            orig_hash = orig_map.get(turn)
            
            if orig_hash is None:
                self.logger.warning(f"ReplayEngine: No original log for Turn {turn}. Skipping verification for this turn.")
                continue
                
            if replay_hash != orig_hash:
                self.logger.error(f"DETERMINISM FAIL: Turn {turn} mismatch! Original: {orig_hash}, Replay: {replay_hash}")
                match = False
            else:
                self.logger.info(f"Turn {turn}: MATCH ({replay_hash})")
                
        if match:
             self.logger.info("ReplayEngine: Determinism VERIFIED.")
        return match

    def _calculate_state_hash(self) -> str:
        """
        Calculates a hash of the current critical state.
        Functionally similar to a lightweight snapshot.
        """
        hasher = hashlib.md5()
        
        # Hash Faction State (Resources, Tech Level)
        # Assuming Faction has a consistent string representation or relevant attributes
        if hasattr(self.engine, 'factions'):
            for f_id in sorted(self.engine.factions.keys()):
                faction = self.engine.factions[f_id]
                hasher.update(str(f_id).encode())
                
                # Check for standard resource attribute
                res = getattr(faction, 'resources', {})
                # If it's a Resource object, convert to something hashable
                if hasattr(res, 'to_dict'): 
                    res = res.to_dict()
                elif hasattr(res, '__dict__'):
                    res = res.__dict__
                    
                # Sort resource keys for stable hashing
                if isinstance(res, dict):
                    sorted_res = sorted(res.items())
                    hasher.update(str(sorted_res).encode())
                else:
                    hasher.update(str(res).encode())

        # Hash Fleet Positions
        if hasattr(self.engine, 'fleets'):
            # Sort fleets by ID to ensure order doesn't affect hash
            sorted_fleets = sorted(self.engine.fleets, key=lambda f: f.id)
            for fleet in sorted_fleets:
                hasher.update(str(fleet.id).encode())
                # Location might be a Node object or string ID
                loc = getattr(fleet, 'location', 'unknown')
                if hasattr(loc, 'id'): loc = loc.id
                hasher.update(str(loc).encode())
                
        return hasher.hexdigest()
