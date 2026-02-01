from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class EventType:
    """Registry of all standard event types."""
    # Campaign Lifecycle
    CAMPAIGN_STARTED = "campaign_started"
    CAMPAIGN_COMPLETED = "campaign_completed"
    
    # Turn Cycle
    TURN_STARTED = "turn_started"
    TURN_COMPLETED = "turn_completed"
    
    # Victory & Milestones
    VICTORY_PROGRESS = "victory_progress"
    VICTORY_ACHIEVED = "victory_achieved"
    MILESTONE_REACHED = "milestone_reached"
    FACTION_ELIMINATED = "faction_eliminated"
    
    # Game State Changes
    SYSTEM_CONQUERED = "system_conquered"
    FLEET_CREATED = "fleet_created"
    FLEET_DESTROYED = "fleet_destroyed"
    FLEET_MOVED = "fleet_moved"
    
    # Combat
    BATTLE_STARTED = "battle_started"
    BATTLE_COMPLETED = "battle_completed"
    
    # System
    ERROR = "error"
    DASHBOARD_UPDATE = "dashboard_update"
    TELEMETRY_FLUSH = "telemetry_flush"

@dataclass
class Event:
    """Base event class.
    
    Attributes:
        event_type (str): The type of event (use EventType constants).
        data (Dict[str, Any]): The payload data.
        timestamp (datetime): When the event occurred.
        source (str, optional): The component that originated the event.
    """
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
