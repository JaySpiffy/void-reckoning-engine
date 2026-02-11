
import sys
import os
import json
import uuid

# Ensure we can import the bridge
sys.path.append(os.path.join(os.getcwd(), "native_pulse", "void_reckoning_bridge"))

try:
    import void_reckoning_bridge
    RustAuditor = void_reckoning_bridge.RustAuditor
    RustEconomyEngine = void_reckoning_bridge.RustEconomyEngine
    # Access observability classes as attributes since it might not be a package-level module
    CorrelationContext = void_reckoning_bridge.observability.CorrelationContext
    EventSeverity = void_reckoning_bridge.observability.EventSeverity
    print("Successfully imported void_reckoning_bridge")
except ImportError as e:
    print(f"Failed to import void_reckoning_bridge: {e}")
    sys.exit(1)

def test_auditor_observability():
    print("\n--- Testing Auditor Observability ---")
    auditor = RustAuditor()
    auditor.initialize()
    log = auditor.enable_event_logging()
    
    # 1. Create Context
    root_trace_id = str(uuid.uuid4())
    root_span_id = str(uuid.uuid4())
    context = CorrelationContext()
    context.trace_id = root_trace_id
    context.span_id = root_span_id
    
    print(f"Setting Auditor Context: Trace={root_trace_id}")
    auditor.set_correlation_context(context)
    
    # 2. Trigger Validation Error (Missing required fields for a Unit)
    # Unit requires: name, tier, armor, speed
    invalid_unit = {
        "name": "Invalid Unit",
        # Missing tier, armor, speed
    }
    
    print("Triggering validation error...")
    try:
        auditor.validate_entity("unit_1", "unit", json.dumps(invalid_unit), "univ_1", 1)
    except Exception as e:
        print(f"Validation failed as expected (or unexpected error): {e}")

    # 3. Verify Log
    events = log.get_all()
    print(f"Captured {len(events)} events.")
    
    found = False
    for evt in events:
        print(f"Event: {evt.message} | TraceID: {evt.context.trace_id} | Severity: {evt.severity}")
        if evt.context.trace_id == root_trace_id:
            found = True
            print("[SUCCESS] Found event with correct Trace ID.")
            break
            
    if not found:
        print("[FAILURE] No event found with matching Trace ID.")
        # Don't exit yet, run economy test too

def test_economy_observability():
    print("\n--- Testing Economy Observability ---")
    economy = RustEconomyEngine()
    log = economy.enable_event_logging()
    
    # 1. Create Context
    root_trace_id = str(uuid.uuid4())
    root_span_id = str(uuid.uuid4())
    context = CorrelationContext()
    context.trace_id = root_trace_id
    context.span_id = root_span_id
    
    print(f"Setting Economy Context: Trace={root_trace_id}")
    economy.set_correlation_context(context)
    
    # 2. Trigger Insolvency
    # Create a fleet with high upkeep and no income
    print("Triggering insolvency...")
    
    # Add a planet with 0 income
    planet = {
        "id": "planet_poor",
        "owner_faction": "BrokeFaction",
        "node_type": "Planet",
        "base_income": {"credits": 0, "minerals": 0, "energy": 0, "alloys": 0, "food": 0, "consumer_goods": 0, "research": 0},
        "base_upkeep": {"credits": 0, "minerals": 0, "energy": 0, "alloys": 0, "food": 0, "consumer_goods": 0, "research": 0},
        "efficiency": 1.0,
        "efficiency_scaled": 1000000,
        "modifiers": []
    }
    economy.add_node(json.dumps(planet))
    
    # Add a fleet with high upkeep
    fleet = {
        "id": "fleet_expensive",
        "owner_faction": "BrokeFaction",
        "node_type": "Fleet",
        "base_income": {"credits": 0, "minerals": 0, "energy": 0, "alloys": 0, "food": 0, "consumer_goods": 0, "research": 0},
        "base_upkeep": {"credits": 1000, "minerals": 0, "energy": 0, "alloys": 0, "food": 0, "consumer_goods": 0, "research": 0}, # High credit upkeep
        "efficiency": 1.0, # Not in orbit (no discount)
        "efficiency_scaled": 1000000,
        "modifiers": []
    }
    economy.add_node(json.dumps(fleet))
    
    # Process Faction
    economy.process_faction("BrokeFaction")
    
    # 3. Verify Log
    events = log.get_all()
    print(f"Captured {len(events)} events.")
    
    found = False
    for evt in events:
        msg = evt.message
        trace = evt.context.trace_id
        print(f"Event: {msg} | TraceID: {trace}")
        
        if "insolvent" in msg.lower() and trace == root_trace_id:
            found = True
            print("[SUCCESS] Found insolvency event with correct Trace ID.")
            break
            
    if not found:
        print("[FAILURE] No insolvency event found with matching Trace ID.")
        sys.exit(1)

if __name__ == "__main__":
    test_auditor_observability()
    test_economy_observability()
