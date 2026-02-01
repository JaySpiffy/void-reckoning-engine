import pytest
from fastapi.testclient import TestClient
from src.reporting.dashboard_v2.api.main import app

client = TestClient(app)

def test_get_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()

def test_get_status_uninitialized():
    # If service is not initialized, get_dashboard_service dependency will raise 503
    response = client.get("/api/status")
    assert response.status_code == 503
    assert "detail" in response.json()

def test_get_health_uninitialized():
    response = client.get("/api/health")
    # Health check might return 503 if service is uninitialized
    assert response.status_code == 503
    data = response.json()
    assert data["detail"]["status"] == "unhealthy"

def test_get_max_turn_uninitialized():
    response = client.get("/api/run/max_turn")
    assert response.status_code == 503
