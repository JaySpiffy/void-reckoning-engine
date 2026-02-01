import pytest
from fastapi.testclient import TestClient
from src.reporting.dashboard_v2.api.main import app

client = TestClient(app)

def test_root_endpoint():
    """Verify the root endpoint includes the new tactical categories."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "economic_url" in data
    assert "military_url" in data
    assert "industrial_url" in data

@pytest.mark.parametrize("endpoint", [
    "/api/economic/net_profit",
    "/api/economic/revenue_breakdown",
    "/api/economic/stockpile_velocity",
    "/api/economic/resource_roi",
    "/api/military/combat_effectiveness",
    "/api/military/force_composition",
    "/api/military/attrition_rate",
    "/api/military/battle_heatmap",
    "/api/industrial/density",
    "/api/industrial/queue_efficiency",
    "/api/industrial/timeline",
])
def test_endpoints_existence(endpoint):
    """
    Verify all migrated endpoints exist. 
    Note: They might return 503 or 400 if service isn't fully mocked,
    but they should not return 404.
    """
    response = client.get(endpoint)
    # 404 would mean the router registration failed
    assert response.status_code != 404

def test_economic_filters_parsing():
    """Verify that filter parameters are correctly parsed (integration check)."""
    response = client.get("/api/economic/net_profit?faction=Player&min_turn=10&max_turn=20")
    # If it hits the service logic, we check for non-404/422
    assert response.status_code != 422 # Not a validation error
