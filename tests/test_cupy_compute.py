
import pytest
import sys
import os

@pytest.mark.skip(reason="CuPy compatibility issue")
@pytest.mark.gpu
def test_gpu_matrix_multiplication():
    try:
        import cupy as cp
        import numpy as np
    except ImportError:
        pytest.skip("CuPy or NumPy not installed")

    if not cp.cuda.is_available():
        pytest.skip("CUDA not available")

    print("Testing GPU computation...")
    
    # Create arrays on CPU
    shape = (1000, 1000)
    a_cpu = np.random.rand(*shape)
    b_cpu = np.random.rand(*shape)
    
    # Transfer to GPU
    try:
        a_gpu = cp.asarray(a_cpu)
        b_gpu = cp.asarray(b_cpu)
    except Exception as e:
        pytest.fail(f"Failed to transfer data to GPU: {e}")

    # Perform computation on GPU
    try:
        c_gpu = cp.matmul(a_gpu, b_gpu)
    except Exception as e:
        pytest.fail(f"GPU matrix multiplication failed: {e}")

    # Transfer back to CPU
    c_cpu = cp.asnumpy(c_gpu)
    
    assert c_cpu.shape == shape
    
    # Verify correctness with a smaller subset context (full verify is expensive)
    # We trust CuPy's math, we just want to verify execution completes and shape is right.
    # But let's do a tiny check:
    
    a_small = np.array([[1, 2], [3, 4]])
    b_small = np.array([[5, 6], [7, 8]])
    expected = np.matmul(a_small, b_small)
    
    a_small_gpu = cp.asarray(a_small)
    b_small_gpu = cp.asarray(b_small)
    c_small_gpu = cp.matmul(a_small_gpu, b_small_gpu)
    result = cp.asnumpy(c_small_gpu)
    
    np.testing.assert_allclose(result, expected, atol=1e-5)
    print("GPU computation successful!")
