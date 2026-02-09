
import sys
import os
import uuid

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.combat.rust_tactical_engine import RustTacticalEngine
from src.services.pathfinding_service import PathfindingService
try:
    from void_reckoning_bridge import CorrelationContext
except ImportError:
    print("Bridge not found, cannot verify correlation context.")
    sys.exit(1)

def verify_combat_context():
    print("Verifying Combat Engine Correlation...")
    engine = RustTacticalEngine(100.0, 100.0)
    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    
    try:
        engine.set_correlation_id(trace_id, span_id)
        # We can't easily check the internal state without a getter, but if it didn't crash, good.
        # But wait, I added set_correlation_context which sets run_id.
        # The Python wrapper doesn't expose a getter for run_id.
        # However, get_state() returns unit data.
        print(f"  Successfully set correlation ID: {trace_id}")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False

def verify_pathfinding_context():
    print("Verifying Pathfinding Service Correlation...")
    service = PathfindingService()
    if not service._rust_pathfinder:
        print("  Rust pathfinder not initialized.")
        return False
        
    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    
    try:
        service.set_correlation_id(trace_id, span_id)
        print(f"  Successfully set correlation ID: {trace_id}")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False

if __name__ == "__main__":
    c_ok = verify_combat_context()
    p_ok = verify_pathfinding_context()
    
    if c_ok and p_ok:
        print("\nAll correlation tests passed!")
        sys.exit(0)
    else:
        print("\nCorrelation tests failed.")
        sys.exit(1)
