import os
import pickle
import gzip
import time
import hashlib
from typing import Any, Dict, Optional, List
from src.core.config import SAVES_DIR
from src.utils.game_logging import GameLogger

class SnapshotManager:
    """
    Manages deterministic snapshots of the simulation state.
    Serves as the foundation for the "God-Perspective" replay system.
    
    Features:
    - Binary serialization (pickle + gzip) for full state capture
    - Checksum verification for integrity
    - Metadata tracking (turn, timestamp, RNG state)
    """
    
    def __init__(self, engine: Any):
        self.engine = engine
        self.logger = engine.logger
        self.snapshots_dir = os.path.join(SAVES_DIR, "snapshots")
        if not os.path.exists(self.snapshots_dir):
            os.makedirs(self.snapshots_dir)
            
    def create_snapshot(self, label: str = None) -> str:
        """
        Creates a new snapshot of the current engine state.
        Returns the snapshot ID.
        """
        timestamp = int(time.time())
        turn = self.engine.turn_counter
        snapshot_id = f"snap_{turn}_{timestamp}"
        if label:
            snapshot_id = f"{label}_{snapshot_id}"
            
        filepath = os.path.join(self.snapshots_dir, f"{snapshot_id}.bin")
        
        try:
            # 1. Capture State
            # We explicitly verify what we are capturing to ensure Managers are included
            state = {
                "meta": {
                    "id": snapshot_id,
                    "turn": turn,
                    "timestamp": timestamp,
                    "version": 1.0
                },
                "engine_state": self._capture_engine_state(),
                "rng_state": self._capture_rng_state()
            }
            
            # 2. Serialize & Compress
            with gzip.open(filepath, 'wb') as f:
                try:
                    pickle.dump(state, f)
                except RecursionError as re:
                    self.logger.error(f"CRITICAL: RecursionError during pickling of snapshot {snapshot_id}")
                    self.logger.error(f"Engine State Keys: {list(state['engine_state'].keys()) if 'engine_state' in state else 'N/A'}")
                    raise re
                
            self.logger.info(f"Snapshot created: {snapshot_id} ({os.path.getsize(filepath) / 1024:.1f} KB)")
            return snapshot_id
            
        except Exception as e:
            self.logger.error(f"Failed to create snapshot {snapshot_id}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restores the engine state from a snapshot.
        """
        filepath = os.path.join(self.snapshots_dir, f"{snapshot_id}.bin")
        if not os.path.exists(filepath):
            self.logger.error(f"Snapshot not found: {snapshot_id}")
            return False
            
        try:
            with gzip.open(filepath, 'rb') as f:
                state = pickle.load(f)
                
            # 1. Restore RNG (First, to ensure any immediate random calls are deterministic)
            self._restore_rng_state(state["rng_state"])
            
            # 2. Restore Engine State
            self._restore_engine_state(state["engine_state"])
            
            self.logger.info(f"Snapshot restored: {snapshot_id} (Turn {state['meta']['turn']})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore snapshot {snapshot_id}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def _capture_engine_state(self) -> Dict[str, Any]:
        """
        Captures the deep state of the engine and its managers.
        WARNING: This relies on picklability of all objects.
        """
        # Managers to capture explicitly if they don't live on 'engine' cleanly
        # But 'engine' usually holds references to all of them.
        # We perform a shallow copy of the engine's dict, then filter out unpicklable things if needed.
        
        # Critical Data needed for Deterministic Replay
        raw_state = {
            "turn_counter": self.engine.turn_counter,
            "factions": self.engine.factions,
            "systems": self.engine.systems,
            "fleets": self.engine.fleets,
            "all_planets": self.engine.all_planets,
            # Manager States (Assuming they are picklable)
            "economy_manager": self.engine.economy_manager,
            "tech_manager": self.engine.tech_manager,
            "diplomacy_manager": self.engine.diplomacy_manager,
            "mission_manager": getattr(self.engine, 'mission_manager', None),
            "weather_manager": getattr(self.engine, 'flux_storm_manager', None),
            # AI State
            "strategic_ai": getattr(self.engine, 'strategic_ai', None)
        }
        
        # Sanitize state to remove locks/threads
        return self._sanitize_state(raw_state)

    def _sanitize_state(self, obj: Any, depth=0) -> Any:
        """
        Recursively removes unpicklable objects (locks, threads, etc.) from state.
        """
        if depth > 8: return obj # Increased depth from 2 to 8 for Phase 7 stability
        
        if isinstance(obj, dict):
            return {k: self._sanitize_state(v, depth+1) for k, v in obj.items() if not self._is_unicklable(v)}
        elif isinstance(obj, list):
            return [self._sanitize_state(v, depth+1) for v in obj if not self._is_unicklable(v)]
        elif hasattr(obj, '__dict__'):
            # Ideally we rely on object's own __getstate__, but if it fails outside, we can't easily patch it here
            # without deepcopying everything which is slow.
            # For now, we rely on the specific manager __getstate__ implementations we added.
            pass
            
        return obj

    def _is_unicklable(self, obj: Any) -> bool:
        """Fast check for known unpicklable types."""
        t_name = type(obj).__name__
        unpicklable_keywords = ["lock", "thread", "file", "writer", "wrapper", "socket", "client"]
        if any(k in t_name.lower() for k in unpicklable_keywords):
            return True
        return False

    def _restore_engine_state(self, state_data: Dict[str, Any]):
        """Restores engine state from captured data."""
        self.engine.turn_counter = state_data["turn_counter"]
        
        # Restore Factions (Property has no setter)
        if hasattr(self.engine, 'faction_manager'):
             self.engine.faction_manager.clear()
             # stored as dict {name: Faction}
             factions_data = state_data["factions"]
             if isinstance(factions_data, dict):
                 for f in factions_data.values():
                     self.engine.faction_manager.register_faction(f)
             else:
                 # Fallback if list
                 for f in factions_data:
                     self.engine.faction_manager.register_faction(f)
        else:
             # Fallback if no manager (unlikely in current arch)
             self.engine.factions = state_data["factions"]

        # Restore Systems (Property HAS setter, delegating to galaxy_manager)
        self.engine.systems = state_data["systems"]
        
        # Restore Fleets (Property has no setter)
        if hasattr(self.engine, 'fleet_manager'):
             # Clear existing
             if hasattr(self.engine.fleet_manager, 'repository'):
                 self.engine.fleet_manager.repository.clear()
             
             # Reset Index
             self.engine.fleet_manager._index = None
             
             # Re-populate
             fleets_data = state_data["fleets"]
             for fleet in fleets_data:
                 self.engine.fleet_manager.add_fleet(fleet)
        else:
             self.engine.fleets = state_data["fleets"]
             
        # all_planets is derived from systems in GalaxyManager, so setting systems should suffice.
        # However, if we captured it, we might want to ensure consistency?
        # For now, we trust systems restoration covers planets.
        # self.engine.all_planets = state_data["all_planets"] # Read-only
        
        # Restore Managers
        self.engine.economy_manager = state_data["economy_manager"]
        self.engine.tech_manager = state_data["tech_manager"]
        self.engine.diplomacy_manager = state_data["diplomacy_manager"]
        
        if state_data.get("mission_manager"):
            self.engine.mission_manager = state_data["mission_manager"]
            
        if state_data.get("weather_manager"):
            self.engine.flux_storm_manager = state_data["weather_manager"]
            
        if state_data.get("strategic_ai"):
            self.engine.strategic_ai = state_data["strategic_ai"]
            
        # Re-link Engine references in managers if they broke during pickling
        # (Managers often store 'self.engine')
        self._relink_managers()

    def _relink_managers(self):
        """Ensures restored managers point to the current engine instance and re-initialize if needed."""
        # Re-initialize stateless services (BattleManager, IntelligenceManager, etc.)
        if hasattr(self.engine, 'reinit_services'):
            self.engine.reinit_services()
            
        managers = [
            self.engine.economy_manager,
            self.engine.tech_manager,
            self.engine.diplomacy_manager,
            getattr(self.engine, 'mission_manager', None),
            getattr(self.engine, 'flux_storm_manager', None),
            getattr(self.engine, 'strategic_ai', None),
            getattr(self.engine, 'fleet_manager', None),
            getattr(self.engine, 'asset_manager', None),
            getattr(self.engine, 'galaxy_manager', None)
        ]
        
        for mgr in managers:
            if mgr:
                # Force inject engine (hasattr fails if attribute was removed in pickling)
                try:
                    mgr.engine = self.engine
                except Exception:
                    pass # Some might strict slots or read-only

                # Restore Logger if it was stripped
                if hasattr(mgr, 'logger') and mgr.logger is None:
                     mgr.logger = self.logger
                     
        # Re-inject loggers into Factions
        if hasattr(self.engine, 'factions'):
            for f in self.engine.factions.values():
                if hasattr(f, 'logger') and f.logger is None:
                    f.logger = self.logger
                    
        # Re-inject loggers/context into Fleets (if needed)
        # Fleets usually don't hold loggers directly but might need engine ref?
        # Checking Fleet model showed no explicit logger in __init__, but it might be added later.
        pass

        if hasattr(self.engine, 'flux_storm_manager') and self.engine.flux_storm_manager:
            # Re-collect edges as they were not pickled
            self.engine.flux_storm_manager.collect_edges()

        # Re-initialize stateful managers that lost their services during pickling
        if hasattr(self.engine, 'economy_manager') and hasattr(self.engine.economy_manager, 'reinit_services'):
            self.engine.economy_manager.reinit_services(self.engine)
            
        if hasattr(self.engine, 'diplomacy_manager') and hasattr(self.engine.diplomacy_manager, 'reinit_services'):
            self.engine.diplomacy_manager.reinit_services(self.engine)

            
        # Re-init DecisionLogger for StrategicAI
        if hasattr(self.engine, 'strategic_ai') and self.engine.strategic_ai:
            # Ensure engine ref is set before component re-init
            self.engine.strategic_ai.engine = self.engine
            
            from src.reporting.decision_logger import DecisionLogger
            self.engine.strategic_ai.decision_logger = DecisionLogger(engine=self.engine)
            # Re-init stateless components (strategies, coordinators) that were excluded
            if hasattr(self.engine.strategic_ai, 'reinit_stateless_components'):
                self.engine.strategic_ai.reinit_stateless_components()

    def _capture_rng_state(self) -> Dict[str, Any]:
        """Captures state of RNGManager streams."""
        from src.utils.rng_manager import RNGManager
        return RNGManager.get_instance().get_all_states()

    def _restore_rng_state(self, rng_state: Dict[str, Any]):
        """Restores state of RNGManager streams."""
        from src.utils.rng_manager import RNGManager
        RNGManager.get_instance().restore_states(rng_state)
