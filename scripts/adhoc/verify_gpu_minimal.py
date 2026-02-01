import sys
import time
print("Starting GPU Verification...", flush=True)

try:
    import cupy as cp
    print(f"CuPy Imported. Version: {cp.__version__}", flush=True)
    
    print("Getting Device...", flush=True)
    dev = cp.cuda.Device(0)
    print(f"Device 0: {dev.compute_capability}", flush=True)
    
    print("Allocating Array...", flush=True)
    x = cp.arange(1000000, dtype=cp.float32)
    print("Performing Computation...", flush=True)
    y = x * 2.0
    cp.cuda.Stream.null.synchronize()
    print("Computation Complete.", flush=True)
    
    print("GPU Verification SUCCESS.", flush=True)
    
except ImportError:
    print("CuPy not installed or not found.", flush=True)
except Exception as e:
    print(f"GPU Verification FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
