import py
import pytest
import time
import os
import shutil
import threading
from src.reporting.telemetry import TelemetryCollector, EventCategory, VerbosityLevel

class TestTelemetryStreaming:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        self.log_dir = str(tmp_path / "logs")
        self.collector = TelemetryCollector(self.log_dir, verbosity='debug')
        self.collector.enable_streaming()
        yield
        # Cleanup handled by tmp_path

    def test_streaming_buffer_put(self):
        """Verify events are added to stream buffer."""
        self.collector.log_event(EventCategory.SYSTEM, "test", {"foo": "bar"})
        
        items = self.collector.get_stream_buffer()
        assert len(items) == 1
        assert items[0]["event_type"] == "test"

    def test_subscriber_callback(self):
        """Verify subscribers receive events."""
        received = []
        def callback(event):
            received.append(event)
            
        self.collector.subscribe(callback)
        self.collector.log_event(EventCategory.SYSTEM, "test_sub", {})
        
        time.sleep(0.1) # Callback via direct call, but buffer async might need time if threaded?
        # Implementation is direct list iteration, so should be instant
        assert len(received) == 1
        assert received[0]["event_type"] == "test_sub"
        
        # Test unsubscribe
        self.collector.unsubscribe(callback)
        self.collector.log_event(EventCategory.SYSTEM, "test_sub_2", {})
        assert len(received) == 1 # Should not increase

    def test_metrics_aggregation(self):
        """Verify metrics aggregation logic."""
        # 1. Battle Start
        self.collector.log_event(EventCategory.COMBAT, "battle_start", {})
        
        # 2. Unit Spawn
        self.collector.log_event(EventCategory.CONSTRUCTION, "unit_built", {"unit": "Marine"}, faction="Imperium")
        
        # 3. Income
        self.collector.log_event(EventCategory.ECONOMY, "income_collected", {"amount": 100}, faction="Imperium")
        
        metrics = self.collector.get_live_metrics()
        
        # Battles per minute = 1 event * (60/60) = 1.0 (if window=60)
        # We need to verify window_seconds defaults to 60 or wait?
        # The Aggregator stores timestamps. 1 timestamp in list.
        
        assert metrics["battles"]["rate"] > 0
        assert "Imperium" in metrics["units"]["spawn_rate"]
        # Rate is per second over 60s window: 100 / 60 = 1.666...
        assert metrics["economy"]["flow_rate"]["Imperium"] == pytest.approx(100/60)
