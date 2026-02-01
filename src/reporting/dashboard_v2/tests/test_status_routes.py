def test_get_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["universe_name"] == "test_universe"

def test_get_health(client):
    # Ensure prefix is correct now
    response = client.get("/api/diagnostics/health") 
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] in ["healthy", "degraded", "error"]
