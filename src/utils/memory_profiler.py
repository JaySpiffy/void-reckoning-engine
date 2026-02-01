import tracemalloc
import time
import json
from typing import Dict, Any, Optional
from functools import wraps

class MemoryProfiler:
    """
    Lightweight memory profiler using tracemalloc.
    Tracks memory usage during cross-universe operations.
    """
    
    def __init__(self):
        self.snapshots = []
        self.is_active = False
        
    def start(self):
        """Start memory tracking."""
        tracemalloc.start()
        self.is_active = True
        self.snapshots = []
        
    def snapshot(self, label: str = ""):
        """Take a memory snapshot."""
        if not self.is_active:
            return
            
        current, peak = tracemalloc.get_traced_memory()
        self.snapshots.append({
            "label": label,
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024,
            "timestamp": time.time()
        })
        
    def stop(self) -> Dict[str, Any]:
        """Stop tracking and return report."""
        if not self.is_active:
            return {}
            
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.is_active = False
        
        return {
            "final_current_mb": current / 1024 / 1024,
            "final_peak_mb": peak / 1024 / 1024,
            "snapshots": self.snapshots
        }
        
    def get_report(self) -> str:
        """Generate human-readable report."""
        if not self.snapshots:
            return "No memory snapshots recorded."
            
        lines = ["=== Memory Profile Report ==="]
        for snap in self.snapshots:
            lines.append(f"{snap['label']}: Current={snap['current_mb']:.2f}MB, Peak={snap['peak_mb']:.2f}MB")
            
        return "\n".join(lines)

def profile_memory(label: str = ""):
    """Decorator for profiling function memory usage."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracemalloc.start()
            result = func(*args, **kwargs)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            print(f"[MEMORY] {label or func.__name__}: Current={current/1024/1024:.2f}MB, Peak={peak/1024/1024:.2f}MB")
            return result
        return wrapper
    return decorator
