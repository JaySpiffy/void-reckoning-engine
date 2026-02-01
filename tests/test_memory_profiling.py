import pytest
import sys
import os
from src.utils.memory_profiler import MemoryProfiler, profile_memory

def test_profiler_basic():
    """Test basic profiler functionality."""
    profiler = MemoryProfiler()
    profiler.start()
    
    # Allocate some memory
    data = [0] * 1000000
    profiler.snapshot("After allocation")
    
    report = profiler.stop()
    assert "final_peak_mb" in report
    assert report["final_peak_mb"] > 0
    assert len(report["snapshots"]) == 1
    assert report["snapshots"][0]["label"] == "After allocation"

def test_decorator():
    """Test memory profiling decorator."""
    @profile_memory("test_function")
    def allocate_memory():
        return [0] * 1000000
        
    result = allocate_memory()
    assert len(result) == 1000000
