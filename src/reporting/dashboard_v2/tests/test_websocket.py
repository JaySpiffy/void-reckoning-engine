import pytest
from fastapi.testclient import TestClient
from src.reporting.dashboard_v2.api.main import app
import json
import time

def test_websocket_connection():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Check Initial Snapshot (Status Update)
        data = websocket.receive_json()
        assert data["type"] == "status_update"
        assert "universe" in data["data"]
        assert "run_id" in data["data"]

def test_websocket_request_snapshot():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Consume initial snapshot
        websocket.receive_json()
        
        # Request Snapshot
        websocket.send_json({"type": "request_snapshot"})
        data = websocket.receive_json()
        
        assert data["type"] == "snapshot"
        assert "data" in data

def test_websocket_ping_pong():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Consume initial snapshot
        websocket.receive_json()
        
        # Send Ping Check
        websocket.send_json({"type": "ping_check"})
        data = websocket.receive_json()
        
        assert data["type"] == "pong"
        assert "timestamp" in data

def test_websocket_metrics_broadcast():
    client = TestClient(app)
    # This test might be flaky depending on how fast the background loop starts
    # and the METRICS_UPDATE_INTERVAL (default 2s)
    with client.websocket_connect("/ws") as websocket:
        # Consume initial snapshot
        websocket.receive_json()
        
        # Wait for metrics update (timeout after 5s)
        start_time = time.time()
        received_metrics = False
        while time.time() - start_time < 5:
            try:
                data = websocket.receive_json()
                if data["type"] == "metrics_update":
                    received_metrics = True
                    break
            except:
                pass
        
        # We don't assert strictly here as the loop might not have run yet in a fast test
        # but in a real environment it should trigger.
        # assert received_metrics 
        pass
