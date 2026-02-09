
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

try:
    from void_reckoning_bridge import CorrelationContext
except ImportError:
    CorrelationContext = None

class DecisionLogger:
    """
    Standardized logger for capturing AI decision-making processes ($DEEP_TRACER).
    Logs the 'Why' behind actions, including context, options considered, and rationale.
    """
    def __init__(self, engine=None, telemetry=None):
        self.engine = engine
        self._telemetry = telemetry

    @property
    def telemetry(self):
        if self._telemetry:
            return self._telemetry
        if self.engine and hasattr(self.engine, 'telemetry'):
            return self.engine.telemetry
        return None

    def log_decision(self, 
                     decision_type: str,
                     actor_id: str,
                     context: Dict[str, Any],
                     options: List[Dict[str, Any]],
                     selected_action: str,
                     outcome: str = "Success",
                     trace_id: Optional[str] = None,
                     parent_trace_id: Optional[str] = None):
        """
        Logs a structured decision event.
        
        Args:
            decision_type: Category (e.g., 'FLEET_MOVE', 'PRODUCTION', 'RESEARCH')
            actor_id: ID of the entity making the decision (Faction, Fleet, etc.)
            context: State information relevant to the decision (resources, location, etc.)
            options: List of considered alternatives with scores and rationale.
            selected_action: The chosen option.
            outcome: Result of the decision (if known immediately).
            trace_id: Optional correlation ID. If not provided, a new one is generated.
            parent_trace_id: Optional ID of the causing event (e.g., the PLAN event that caused this ACTION).
        """
        if not self.telemetry:
            return

        # Auto-generate trace_id if missing
        if not trace_id:
            trace_id = str(uuid.uuid4())

        payload = {
            "trace_id": trace_id,
            "parent_trace_id": parent_trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor_id,
            "decision_type": decision_type,
            "context": context,
            "options_considered": options,
            "selected_action": selected_action,
            "outcome": outcome
        }

        # Use the existing telemetry pipeline but with a specific event type
        # We assume EventCategory.STRATEGY or DOCTRINE fits, or we just use a custom event string
        # if the telemetry system supports it. 
        # Looking at telemetry.py, log_event takes (category, event_type, details, faction).
        
        # We'll map decision_type to a category if possible, or default to STRATEGY.
        from src.reporting.telemetry import EventCategory
        
        category = EventCategory.STRATEGY
        if decision_type in ['PRODUCTION', 'CONSTRUCTION']:
            category = EventCategory.ECONOMY
        elif decision_type in ['FLEET_MOVE', 'COMBAT']:
            category = EventCategory.COMBAT
        elif decision_type == 'RESEARCH':
            category = EventCategory.TECHNOLOGY

        # Determine faction for indexing
        faction_name = "Unknown"
        if actor_id:
            # Handle Faction:ID format
            faction_name = actor_id.split(":")[0]
            
        self.telemetry.log_event(
            category,
            "ai_decision", # Standard event type for filtering
            payload,
            faction=faction_name
        )
