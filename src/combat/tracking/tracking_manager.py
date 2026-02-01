from typing import Optional, Any
from src.combat.combat_tracker import CombatTracker

class TrackingManager:
    """Manages combat logging and snapshots."""
    
    def __init__(self, json_path: Optional[str] = None, telemetry=None):
        self.tracker = CombatTracker(json_path, telemetry)
        
    def start_round(self, round_num: int):
        self.tracker.start_round(round_num)

    def log_snapshot(self, unit: Any):
        self.tracker.log_snapshot(unit)
        
    def log_event(self, event_type: str, *args, **kwargs):
        self.tracker.log_event(event_type, *args, **kwargs)

    def finalize(self, winner: str, rounds: int, armies: dict, battle_stats: dict):
        self.tracker.finalize(winner, rounds, armies, battle_stats)

    def cleanup(self):
        self.tracker.cleanup()
