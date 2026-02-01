import pytest
import os
import sys
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from src.reporting.dashboard_v2.api.main import app
from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service

# Mock Service Fixture
@pytest.fixture
def mock_dashboard_service():
    service = MagicMock()
    service.universe = "test_universe"
    service.run_id = "test_run"
    service.status = "running"
    service.control_paused = False
    service.running = True
    
    # Mock Data Provider
    service.data_provider = MagicMock()
    service.data_provider.get_active_factions.return_value = ["Faction1", "Faction2"]
    service.data_provider.get_trend_analysis.return_value = {"trend": "up"}
    service.data_provider.get_anomaly_alerts.return_value = []
    service.data_provider.get_faction_balance_scores.return_value = {}
    service.data_provider.get_predictive_insights.return_value = {}
    
    # Mock other methods
    service.get_live_metrics.return_value = {"turn": 10, "metrics": {}}
    service.get_max_turn.return_value = 100
    service.pause_simulation = MagicMock()
    service.resume_simulation = MagicMock()
    service.trigger_step = MagicMock()
    
    return service

@pytest.fixture
def client(mock_dashboard_service):
    async def override_get_dashboard_service():
        return mock_dashboard_service

    app.dependency_overrides[get_dashboard_service] = override_get_dashboard_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}
