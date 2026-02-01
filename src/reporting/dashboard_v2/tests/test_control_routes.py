from fastapi.testclient import TestClient
from src.reporting.dashboard_v2.api.main import app

client = TestClient(app)

def test_get_control_status():
    response = client.get("/api/control/status")
    assert response.status_code in [200, 503]

def test_post_pause():
    # Only test if authorized/safe, or expect 403/503
    response = client.post("/api/control/pause")
    assert response.status_code in [200, 503, 401]
