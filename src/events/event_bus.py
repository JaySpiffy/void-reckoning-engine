from typing import Callable, List, Dict, Any, Optional
from collections import defaultdict
from src.events.event import Event

class EventBus:
    """Central event dispatcher."""
    
    _instance: Optional['EventBus'] = None
    
    def __init__(self):
        if EventBus._instance is not None:
            pass
        EventBus._instance = self
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = defaultdict(list)
    
    @classmethod
    def get_instance(cls) -> 'EventBus':
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        self._subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
    
    def publish(self, event_type: str, data: Dict[str, Any], source: Optional[str] = None) -> None:
        """Construct and publish an event to all subscribers."""
        event = Event(
            event_type=event_type,
            data=data,
            source=source
        )
        self.publish_event(event)

    def publish_event(self, event: Event) -> None:
        """Publish a pre-constructed event object."""
        if event.event_type in self._subscribers:
            for handler in self._subscribers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # In a real system we'd use a proper logger here
                    print(f"Error in event handler for {event.event_type}: {e}")
