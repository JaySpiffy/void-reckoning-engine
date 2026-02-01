from typing import Dict, Any, Optional
from src.events.event_bus import EventBus
from src.events.event import Event, EventType
from src.reporting.telemetry import TelemetryCollector, EventCategory

class TelemetrySubscriber:
    """Subscribes to events and pushes them to the TelemetryCollector."""
    
    def __init__(self, event_bus: EventBus, collector: TelemetryCollector):
        self.bus = event_bus
        self.collector = collector
        self._subscribe_all()
        
    def _subscribe_all(self):
        """Subscribes to all relevant event types."""
        # Campaign & Turn
        self.bus.subscribe(EventType.CAMPAIGN_STARTED, self._handle_event)
        self.bus.subscribe(EventType.CAMPAIGN_COMPLETED, self._handle_event)
        self.bus.subscribe(EventType.TURN_STARTED, self._handle_event)
        self.bus.subscribe(EventType.TURN_COMPLETED, self._handle_event)
        
        # Victory & Milestones
        self.bus.subscribe(EventType.VICTORY_PROGRESS, self._handle_event)
        self.bus.subscribe(EventType.VICTORY_ACHIEVED, self._handle_event)
        self.bus.subscribe(EventType.MILESTONE_REACHED, self._handle_event)
        self.bus.subscribe(EventType.FACTION_ELIMINATED, self._handle_event)
        
        # Combat
        self.bus.subscribe(EventType.BATTLE_STARTED, self._handle_event)
        self.bus.subscribe(EventType.BATTLE_COMPLETED, self._handle_event)
        
        # Entities
        self.bus.subscribe(EventType.SYSTEM_CONQUERED, self._handle_event)
        self.bus.subscribe(EventType.FLEET_MOVED, self._handle_event)
        self.bus.subscribe(EventType.FLEET_CREATED, self._handle_event)
        self.bus.subscribe(EventType.FLEET_DESTROYED, self._handle_event)
        
        # System
        self.bus.subscribe(EventType.TELEMETRY_FLUSH, self._handle_flush)
        self.bus.subscribe(EventType.ERROR, self._handle_event)

    def _handle_event(self, event: Event):
        """Generic handler that delegates to collector."""
        category = self._map_category(event.event_type)
        
        # Extract metadata
        turn = event.data.get('turn', self.collector.current_turn)
        faction = event.data.get('faction')
        
        self.collector.log_event(
            category=category,
            event_type=event.event_type,
            data=event.data,
            turn=turn,
            faction=faction
        )

    def _handle_flush(self, event: Event):
        """Handles telemetry flush requests."""
        if hasattr(self.collector, 'flush'):
            self.collector.flush()

    def _map_category(self, event_type: str) -> EventCategory:
        """Maps EventType to Telemetry EventCategory."""
        if event_type in [EventType.BATTLE_STARTED, EventType.BATTLE_COMPLETED]:
            return EventCategory.COMBAT
            
        if event_type in [EventType.FLEET_MOVED]:
            return EventCategory.MOVEMENT
            
        if event_type in [EventType.FLEET_CREATED, EventType.FLEET_DESTROYED]:
            return EventCategory.CONSTRUCTION # Or COMBAT/MILITARY? 
            # Telemetry has CONSTRUCTION, COMBAT, etc.
            # Using CAMPAIGN for generic fleet lifecycle for now if mostly unused.
            return EventCategory.CAMPAIGN 
            
        if event_type in [EventType.SYSTEM_CONQUERED]:
            return EventCategory.CAMPAIGN
            
        if event_type in [EventType.VICTORY_PROGRESS, EventType.VICTORY_ACHIEVED, 
                         EventType.MILESTONE_REACHED, EventType.FACTION_ELIMINATED]:
            return EventCategory.CAMPAIGN
            
        if event_type in [EventType.CAMPAIGN_STARTED, EventType.CAMPAIGN_COMPLETED,
                         EventType.TURN_STARTED, EventType.TURN_COMPLETED]:
            return EventCategory.CAMPAIGN
            
        if event_type == EventType.ERROR:
            return EventCategory.SYSTEM
            
        return EventCategory.SYSTEM
