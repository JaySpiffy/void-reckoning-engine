from typing import Dict, Any, List, Optional
from src.reporting.telemetry import EventCategory

class MilestoneManager:
    """
    Tracks and records campaign milestones.
    """
    def __init__(self, telemetry_collector: Any):
        self.telemetry = telemetry_collector
        self._campaign_milestones: List[Dict[str, Any]] = []
        self._milestone_turns = {
            'first_battle': None,
            'first_conquest': None,
            'first_alliance': None,
            'major_expansion': None,
            'tech_breakthrough': None
        }

    def record_milestone(self, milestone_key: str, turn: int, data: Dict[str, Any] = None):
        """Records a major campaign milestone if not already recorded."""
        if milestone_key in self._milestone_turns and self._milestone_turns[milestone_key] is None:
            self._milestone_turns[milestone_key] = turn
            
            event_data = {
                "milestone": milestone_key,
                "turn": turn,
                "data": data or {}
            }
            self._campaign_milestones.append(event_data)
            
            if self.telemetry:
                self.telemetry.log_event(
                    EventCategory.CAMPAIGN,
                    "milestone_reached",
                    event_data,
                    turn=turn
                )
                
    def get_milestones(self) -> List[Dict[str, Any]]:
        return self._campaign_milestones
