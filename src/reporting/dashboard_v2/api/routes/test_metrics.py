import pytest
from fastapi.testclient import TestClient
from src.reporting.dashboard_v2.api.main import app

client = TestClient(app)

def test_get_metrics_live_uninitialized():
    response = client.get("/api/metrics/live")
    assert response.status_code == 503

def test_ingest_telemetry_uninitialized():
    payload = {
        "batch_id": "test_batch",
        "events": [{"type": "test_event"}]
    }
    response = client.post("/api/metrics/telemetry/ingest", json=payload)
    assert response.status_code == 503
