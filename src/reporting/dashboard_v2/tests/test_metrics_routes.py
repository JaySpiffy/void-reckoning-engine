def test_get_live_metrics(client, mock_dashboard_service):
    mock_dashboard_service.get_live_metrics.return_value = {"turn": 42, "metrics": {"foo": "bar"}}
    response = client.get("/api/metrics/live")
    assert response.status_code == 200
    data = response.json()
    assert data["turn"] == 42
    assert "metrics" in data
