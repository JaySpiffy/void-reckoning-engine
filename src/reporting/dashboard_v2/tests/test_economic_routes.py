from fastapi.testclient import TestClient
from src.reporting.dashboard_v2.api.main import app

client = TestClient(app)

def test_get_economic_health():
    response = client.get("/api/economic/net_profit")
    assert response.status_code in [200, 503]

def test_get_revenue_breakdown():
    response = client.get("/api/economic/revenue_breakdown")
    assert response.status_code in [200, 503]
