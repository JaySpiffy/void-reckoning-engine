
import sys
import json
import uuid
import sys
import json
import uuid
import void_reckoning_bridge

# Access classes through the module structure directly
RustCombatEngine = void_reckoning_bridge.RustCombatEngine
CorrelationContext = void_reckoning_bridge.observability.CorrelationContext
EventSeverity = void_reckoning_bridge.observability.EventSeverity
EventLog = void_reckoning_bridge.observability.EventLog

def test_causal_link():
    print("Testing Causal Link in Rust Combat Engine...")
    
    # 1. Create Engine
    engine = RustCombatEngine(1000.0, 1000.0)
    log = engine.enable_event_logging()
    
    # 2. Set Context
    root_trace_id = str(uuid.uuid4())
    root_span_id = str(uuid.uuid4())
    
    context = CorrelationContext()
    context.trace_id = root_trace_id
    context.span_id = root_span_id
    
    print(f"Setting Context: Trace={root_trace_id}, Span={root_span_id}")
    engine.set_correlation_context(context)
    
    # 3. Add Units (One weak, one strong to force a kill)
    # Unit 1: Victim (1 HP)
    # id, name, faction, hp, x, y, weapons, speed, evasion, shields, armor
    engine.add_unit(1, "Victim", 1, 1.0, 100.0, 100.0, [], 0.0, 0.0, 0.0, 0.0)
    
    # Unit 2: Killer (High Damage)
    engine.add_unit(2, "Killer", 2, 100.0, 110.0, 100.0, [("DeathRay", "Energy", 50.0, 100.0, 1.0, 1.0)], 0.0, 0.0, 0.0, 0.0)
    
    # 4. Simulate until event
    print("Simulating...")
    for _ in range(10):
        engine.step()
        
    # 5. Check Log
    events = log.get_all()
    print(f"Captured {len(events)} events.")
    
    found_link = False
    for evt in events:
        print(f"Event: {evt.message}")
        print(f"  Trace ID: {evt.context.trace_id}")
        print(f"  Parent ID: {evt.context.parent_id}")
        
        if evt.context.trace_id == root_trace_id and evt.context.parent_id == root_span_id:
            found_link = True
            print("  [SUCCESS] Causal link confirmed!")
            
    if found_link:
        print("\nTEST PASSED: Causal chain preserved.")
        sys.exit(0)
    else:
        print("\nTEST FAILED: No event linked to parent context found.")
        sys.exit(1)

if __name__ == "__main__":
    test_causal_link()
