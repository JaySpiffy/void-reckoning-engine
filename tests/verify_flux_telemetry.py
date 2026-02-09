import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.fleet import Fleet
from src.reporting.telemetry import EventCategory

def test_flux_blocking_telemetry():
    print("Testing Flux Blocking Telemetry...")
    
    # Setup mocks
    engine = MagicMock()
    telemetry = MagicMock()
    engine.telemetry = telemetry
    engine.turn_counter = 10
    
    location = MagicMock()
    location.name = "FluxGate"
    
    # Initialize Fleet
    fleet = Fleet("Fleet_Flux", "TestFaction", location)
    
    # Mock speed and route
    fleet._cached_speed = 1
    fleet._speed_dirty = False
    
    # Mock an edge that is NOT traversable (flux storm)
    edge = MagicMock()
    edge.is_traversable.return_value = False
    edge.distance = 5
    
    next_node = MagicMock()
    fleet.route = [next_node]
    
    # Mock current_node.edges to return our blocked edge
    current_node = MagicMock()
    current_node.edges = [edge]
    edge.target = next_node
    fleet.current_node = current_node
    
    # Call update_movement
    # This should trigger the flux blocking logic and the telemetry call
    fleet.update_movement(engine=engine)
    
    # Verify telemetry was called with the correct enum
    telemetry.log_event.assert_called_once()
    args, kwargs = telemetry.log_event.call_args
    
    category = args[0]
    event_type = args[1]
    
    print(f"Telemetry category: {category} (type: {type(category)})")
    print(f"Telemetry event_type: {event_type}")
    
    if isinstance(category, EventCategory) and category == EventCategory.ENVIRONMENT:
        print("SUCCESS: Telemetry called with EventCategory.ENVIRONMENT.")
    else:
        print("FAILURE: Telemetry called with incorrect category.")

if __name__ == "__main__":
    test_flux_blocking_telemetry()
