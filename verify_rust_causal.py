
import json
import time
from void_reckoning_bridge import RustCausalGraph, CorrelationContext, Event, EventSeverity

def verify_rust_causal():
    print("--- Initializing RustCausalGraph ---")
    graph = RustCausalGraph()
    
    # 1. Create a chain of events
    # Root: Strategic Plan
    ctx1 = CorrelationContext()
    ctx1.trace_id = "trace-001"
    ctx1.span_id = "span-001"
    
    event1 = {
        "timestamp": 1000.0,
        "severity": "Info",
        "category": "Strategy",
        "message": "Formulated Plan Alpha",
        "context": json.loads(ctx1.to_json()),
        "data": None
    }
    
    # Child: Allocating Budget
    ctx2 = ctx1.child() 
    # Note: ctx1.child() generates new span_id and sets parent_id = ctx1.span_id
    
    event2 = {
        "timestamp": 1001.0,
        "severity": "Info",
        "category": "Economy",
        "message": "Allocated 500 Credits",
        "context": json.loads(ctx2.to_json()), # Use Rust-generated child context
        "data": None
    }
    
    # Grandchild: Recruiting Unit
    ctx3 = ctx2.child()
    
    event3 = {
        "timestamp": 1002.0,
        "severity": "Info",
        "category": "Production",
        "message": "Recruited Unit X",
        "context": json.loads(ctx3.to_json()),
        "data": None
    }
    
    print("--- Ingesting Events ---")
    graph.add_event_json(json.dumps(event1))
    graph.add_event_json(json.dumps(event2))
    graph.add_event_json(json.dumps(event3))
    
    print(f"Graph Size: {graph.size()}")
    assert graph.size() == 3
    
    print("--- Testing Backward Trace (Why did Unit X get recruited?) ---")
    # Query: ctx3.span_id
    start_time = time.time()
    chain = graph.get_causal_chain(ctx3.span_id)
    end_time = time.time()
    
    print(f"Trace Time: {(end_time - start_time)*1000:.4f} ms")
    print(f"Chain Length: {len(chain)}")
    
    # Validation
    assert len(chain) == 3
    assert chain[0].message == "Formulated Plan Alpha"
    assert chain[1].message == "Allocated 500 Credits"
    assert chain[2].message == "Recruited Unit X"
    
    print("Lineage:")
    for e in chain:
        print(f"  [{e.timestamp}] {e.category}: {e.message}")
        
    print("--- Testing Forward Trace (Impact of Plan Alpha) ---")
    # Query: ctx1.span_id
    start_time = time.time()
    impact = graph.get_consequences(ctx1.span_id)
    end_time = time.time()
    
    print(f"Impact Time: {(end_time - start_time)*1000:.4f} ms")
    print(f"Consequences Count: {len(impact)}")
    
    # Validation: Should include Child and Grandchild (BFS order usually)
    # Note: BFS might include self? My implementation logic: queue starts with span_id, pops, finds children.
    # Logic: 
    # queue = [root]
    # pop root. find children [child]. add child to result. push child.
    # pop child. find children [grandchild]. add grandchild to result. push grandchild.
    # So result is [child, grandchild].
    assert len(impact) == 2
    
    print("Consequences:")
    for e in impact:
        print(f"  [{e.timestamp}] {e.category}: {e.message}")

    print("\n[SUCCESS] Rust Causal Graph Verified!")

if __name__ == "__main__":
    verify_rust_causal()
