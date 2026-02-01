import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reporting.dashboard_v2.api.main import app
import src.reporting.dashboard_v2.api.dependencies as deps

@pytest.fixture
def mock_service():
    mock = MagicMock()
    mock.universe = "test_universe"
    mock.run_id = "run_test"
    
    # Mock Data Provider
    mock.data_provider = MagicMock()
    
    # Setup mock return data for Resource ROI
    mock.data_provider.get_resource_roi_data.return_value = {
        "roi_data": [
            {"faction": "Imperium", "amount": 500, "resource": "Requisition"},
            {"faction": "Chaos", "amount": 0, "resource": "Requisition"}
        ]
    }
    
    return mock

@pytest.fixture
def client(mock_service):
    # Dependency Override for Routes
    async def get_mock_async():
        return mock_service

    app.dependency_overrides[deps.get_dashboard_service] = get_mock_async
    
    with TestClient(app) as c:
        yield c
            
    # Cleanup overrides
    app.dependency_overrides = {}

def test_roi_endpoint(client, mock_service):
    """Verify detailed ROI endpoint via FastAPI."""
    # Note: FilterParams normally requires universe/run_id in query if service doesn't have default?
    # Actually filter params resolver might use service default if query missing, 
    # but efficient test should provide them.
    
    response = client.get(
        "/api/economic/resource_roi", 
        params={
            "universe": "test_universe", 
            "run_id": "run_test", 
            "factions": "Imperium,Chaos"
        }
    )
    
    assert response.status_code == 200, f"Request failed: {response.text}"
    data = response.json()
    
    assert "roi_data" in data
    assert len(data["roi_data"]) == 2
    
    # Verify mock was called with correct params
    # params: universe, run_id, batch_id, requested_factions, turn_range
    mock_service.data_provider.get_resource_roi_data.assert_called_once()
    args = mock_service.data_provider.get_resource_roi_data.call_args
    # We can check specific args if needed, e.g. run_id="run_test"
    assert args[0][0] == "test_universe"

