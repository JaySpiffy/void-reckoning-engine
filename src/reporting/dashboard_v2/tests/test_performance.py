import pytest
import time

@pytest.mark.performance
def test_status_response_time(client):
    start = time.time()
    for _ in range(100):
        client.get("/api/status")
    end = time.time()
    avg_time = (end - start) / 100
    # Expect < 50ms average
    assert avg_time < 0.05

@pytest.mark.performance
def test_metrics_endpoint_load(client, mock_dashboard_service):
    # Setup mock return
    mock_dashboard_service.get_live_metrics.return_value = {"turn": 100, "metrics": {}}
    
    start = time.time()
    client.get("/api/metrics/live")
    elapsed = time.time() - start
    assert elapsed < 0.2
