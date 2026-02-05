import sys
import os
import time

# Mocking parts of the engine to test the caps
sys.path.append(os.getcwd())

from datetime import datetime
from src.reporting.alert_models import AlertHistory, Alert, AlertSeverity
from src.reporting.indexer import MemoryCacheBackend, QueryProfiler
from src.managers.campaign.victory_manager import VictoryManager
from src.managers.campaign.milestone_manager import MilestoneManager

def test_alert_history_cap():
    history = AlertHistory()
    print("Testing AlertHistory cap...")
    for i in range(1000):
        history.add_alert(Alert(
            id=f"alert_{i}", 
            severity=AlertSeverity.INFO, 
            rule_name="test_rule",
            message="test", 
            timestamp=datetime.now()
        ))
    print(f"AlertHistory size: {len(history.alerts)} (Expected: 500)")
    assert len(history.alerts) == 500

def test_memory_cache_cap():
    cache = MemoryCacheBackend(max_size=100)
    print("Testing MemoryCacheBackend cap...")
    for i in range(200):
        cache.set(f"key_{i}", f"value_{i}")
    # It clears half when full, so it should be between 50 and 100
    print(f"MemoryCache size: {len(cache.cache)} (Expected: <= 100)")
    assert len(cache.cache) <= 100
    assert len(cache.cache) > 0

def test_query_profiler_cap():
    profiler = QueryProfiler()
    print("Testing QueryProfiler cap...")
    for i in range(500):
        profiler.log_query("SELECT 1", (), 0.1, "")
    print(f"QueryProfiler stats size: {len(profiler.stats)} (Expected: 200)")
    assert len(profiler.stats) == 200

def test_milestone_manager_cap():
    # Mocking telemetry
    class MockTelemetry:
        def log_event(self, *args, **kwargs): pass
    
    manager = MilestoneManager(MockTelemetry())
    print("Testing MilestoneManager cap...")
    # Add dummy keys to allow more milestones for testing if needed
    # But current implementation checks against _milestone_turns
    for i in range(200):
        manager.record_milestone(f"milestone_{i}", i, {})
        # Force add to test cap directly if needed, but we added the cap to the method
        if f"milestone_{i}" not in manager._milestone_turns:
            manager._milestone_turns[f"milestone_{i}"] = None
            manager.record_milestone(f"milestone_{i}", i, {})

    print(f"Milestones size: {len(manager._campaign_milestones)} (Expected: 100)")
    assert len(manager._campaign_milestones) == 100

if __name__ == "__main__":
    try:
        test_alert_history_cap()
        test_memory_cache_cap()
        test_query_profiler_cap()
        test_milestone_manager_cap()
        print("\nALL MEMORY CAP TESTS PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
