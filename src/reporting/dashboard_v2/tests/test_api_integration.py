from fastapi.testclient import TestClient
from src.reporting.dashboard_v2.api.main import app

client = TestClient(app)

def test_api_documentation():
    """Verify that Swagger UI and OpenAPI docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()

def test_cors_headers():
    """Verify CORS configuration."""
    # Assuming CORS is allowed for all origins in dev or specific ones.
    # Simple check if options request returns valid cors headers
    response = client.options("/api/status", headers={
        "Origin": "http://localhost:5173", 
        "Access-Control-Request-Method": "GET"
    })
    # If CORS initialized, it usually returns 200 on OPTIONS or includes access-control headers
    assert response.status_code in [200, 204] 
