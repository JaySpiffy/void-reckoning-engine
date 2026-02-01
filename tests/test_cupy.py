
import pytest
import os
import sys

@pytest.mark.skip(reason="CuPy compatibility issue")
@pytest.mark.gpu
def test_cupy_import_and_device():
    try:
        import cupy as cp
    except ImportError:
        pytest.skip("CuPy not installed")

    if not cp.cuda.is_available():
        pytest.skip("CUDA not available")

    print(f"CuPy version: {cp.__version__}")
    print(f"CUDA version: {cp.cuda.runtime.runtimeGetVersion()}")
    
    device_count = cp.cuda.runtime.getDeviceCount()
    assert device_count > 0, "No GPU devices found"
    
    print(f"GPU count: {device_count}")
    print(f"GPU name: {str(cp.cuda.Device())}")
