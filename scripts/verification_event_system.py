import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.getcwd())

from src.events.event_bus import EventBus
from src.events.event import Event, EventType
from src.managers.campaign.orchestrator import CampaignOrchestrator
from unittest.mock import MagicMock

def verify_event_system():
    print("Verifying Event System Integration...")
    
    # 1. Mock Engine
    mock_engine = MagicMock()
    mock_engine.config.raw_config = {}
    mock_engine.telemetry = MagicMock()
    mock_engine.logger = MagicMock()
    
    # 2. Initialize Orchestrator
    try:
        orchestrator = CampaignOrchestrator(mock_engine)
        print("[OK] CampaignOrchestrator initialized.")
    except Exception as e:
        print(f"[FAIL] Failed to initialize Orchestrator: {e}")
        return

    # 3. Verify Bus and Subscribers
    if not orchestrator.event_bus:
        print("[FAIL] EventBus not initialized in Orchestrator.")
        return
    print("[OK] EventBus initialized.")
    
    if not orchestrator.telemetry_subscriber:
        print("[FAIL] TelemetrySubscriber not initialized.")
        return
    print("[OK] TelemetrySubscriber initialized.")
    
    # 4. Verify Event flow
    # Publish an event via TurnManager path (simulated)
    print("Testing Turn Start Event...")
    
    # Mock the handler in TelemetrySubscriber to verify it gets called
    # We can't easily mock the method of the *already created* subscriber instance 
    # unless we patch it or inspect side effects on mock_engine.telemetry
    
    orchestrator.event_bus.publish(EventType.TURN_STARTED, {"turn": 1})
    
    # Check if telemetry.log_event was called
    # TelemetrySubscriber delegates to mock_engine.telemetry.log_event
    
    if mock_engine.telemetry.log_event.called:
        args = mock_engine.telemetry.log_event.call_args
        print(f"[OK] Telemetry log_event called with: {args}")
    else:
        print("[FAIL] Telemetry log_event NOT called after TURN_STARTED event.")
        
    # 5. Verify Victory Event
    print("Testing Victory Event...")
    orchestrator.event_bus.publish(EventType.VICTORY_PROGRESS, {"valid": True})
    
    if mock_engine.telemetry.log_event.call_count >= 2:
         print(f"[OK] Telemetry log_event called count: {mock_engine.telemetry.log_event.call_count}")
    else:
         print("[FAIL] Telemetry log_event NOT called for Victory Event.")
         
    print("Event System Verification Complete.")

if __name__ == "__main__":
    verify_event_system()
