
import json
import os
import shutil
from src.observability.causal_tracer import CausalTracer

def create_dummy_logs(log_dir: str):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    events = [
        # 1. Strategy Formulation (Root Cause)
        {
            "event_type": "ai_decision",
            "timestamp": "2026-02-08T10:00:00Z",
            "faction": "Templars_of_the_Flux",
            "details": {
                "trace_id": "T1",
                "decision_type": "STRATEGY",
                "selected_action": "EXPAND_TO_XANZERA"
            }
        },
        # 2. Income Allocation (Caused by T1)
        {
            "event_type": "resource_transaction",
            "timestamp": "2026-02-08T10:05:00Z",
            "faction": "Templars_of_the_Flux",
            "details": {
                "trace_id": "T2",
                "parent_trace_id": "T1",
                "amount": -5000,
                "category": "FLEET_COMMISSION"
            }
        },
        # 3. Unit Production (Caused by T2)
        {
            "event_type": "unit_production",
            "timestamp": "2026-02-08T10:10:00Z",
            "faction": "Templars_of_the_Flux",
            "details": {
                "trace_id": "T3",
                "parent_trace_id": "T2",
                "unit_id": "Fleet-Alpha"
            }
        },
        # 4. Fleet Movement (Caused by T3 - implicity, usually context is passed)
        {
            "event_type": "fleet_movement",
            "timestamp": "2026-02-08T10:30:00Z",
            "faction": "Templars_of_the_Flux",
            "details": {
                "trace_id": "T4",
                "parent_trace_id": "T3",
                "destination": "Xanzera"
            }
        },
        # 5. Battle (Caused by T4)
        {
            "event_type": "battle_start",
            "timestamp": "2026-02-08T10:45:00Z",
            "faction": "Templars_of_the_Flux",
            "details": {
                "trace_id": "T5",
                "parent_trace_id": "T4",
                "location": "Xanzera"
            }
        }
    ]

    with open(os.path.join(log_dir, "events.json"), 'w') as f:
        for e in events:
            f.write(json.dumps(e) + "\n")

def verify_trace():
    log_dir = "temp_trace_logs"
    try:
        create_dummy_logs(log_dir)
        
        tracer = CausalTracer()
        tracer.load_events(log_dir)
        
        print("--- Testing Backward Trace from Battle (T5) ---")
        chain = tracer.get_root_cause("T5")
        
        expected_ids = ["T1", "T2", "T3", "T4", "T5"]
        actual_ids = [node['id'] for node in chain]
        
        print(f"Chain Length: {len(chain)}")
        print(f"IDs: {actual_ids}")
        
        assert len(chain) == 5, f"Expected chain length 5, got {len(chain)}"
        assert actual_ids == expected_ids, f"Chain mismatch! Expected {expected_ids}, got {actual_ids}"
        
        print("\n--- Explanation ---")
        print(tracer.explain_event("T5"))
        
        print("\n[SUCCESS] Causal Tracing Verified Successfully!")
        
    finally:
        if os.path.exists(log_dir):
            shutil.rmtree(log_dir)

if __name__ == "__main__":
    verify_trace()
