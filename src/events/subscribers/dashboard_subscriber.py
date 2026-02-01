from typing import Dict, Any
from src.events.event_bus import EventBus
from src.events.event import Event, EventType
from src.managers.campaign.dashboard_manager import DashboardManager

class DashboardSubscriber:
    """Subscribes to events and updates the DashboardManager state."""
    
    def __init__(self, event_bus: EventBus, manager: DashboardManager):
        self.bus = event_bus
        self.manager = manager
        self._subscribe()
        
    def _subscribe(self):
        self.bus.subscribe(EventType.TURN_COMPLETED, self._handle_turn_completed)
        self.bus.subscribe(EventType.SYSTEM_CONQUERED, self._handle_system_change)
        self.bus.subscribe(EventType.VICTORY_PROGRESS, self._handle_victory_update)
        
    def _handle_turn_completed(self, event: Event):
        # In a real impl, we might push the full turn state or just rely on telemetry
        # For now, we rely on TelemetrySubscriber streaming events to the dashboard backend.
        # This subscriber facilitates direct validaton or specialized TUI updates if needed.
        pass

    def _handle_system_change(self, event: Event):
        # Could trigger manager.update_system_owner(event.data)
        pass

    def _handle_victory_update(self, event: Event):
        # Update victory bars
        pass
