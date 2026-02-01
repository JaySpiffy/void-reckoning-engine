import pytest
from unittest.mock import MagicMock, patch, call
from src.reporting.dashboard_data_provider import DashboardDataProvider

@pytest.fixture
def mock_indexer():
    indexer = MagicMock()
    indexer.conn = MagicMock()
    # Setup standard cursor mock
    cursor = MagicMock()
    indexer.conn.cursor.return_value = cursor
    return indexer

@pytest.fixture
def provider(mock_indexer):
    # Patch the *source* class because it is imported inside __init__
    with patch("src.reporting.analytics_engine.AnalyticsEngine"):
        # We need to mock the validation calls in __init__
        with patch.object(DashboardDataProvider, "_validate_connection"):
            return DashboardDataProvider(mock_indexer)

def test_initialization_validation(mock_indexer):
    """Test that init validates connection."""
    # Mock successful validation queries
    cursor = mock_indexer.conn.cursor.return_value
    cursor.fetchall.side_effect = [
        [("events",), ("factions",), ("batches",)], # tables
        [(0, "data_json", "TEXT")] # cols for events
    ]
    
    with patch("src.reporting.analytics_engine.AnalyticsEngine"):
        p = DashboardDataProvider(mock_indexer)
        assert p.is_healthy()
        mock_indexer.conn.cursor.assert_called()

def test_validation_failure(mock_indexer):
    """Test init failure behavior."""
    mock_indexer.conn.execute.side_effect = Exception("DB Down")
    
    with patch("src.reporting.analytics_engine.AnalyticsEngine"):
        p = DashboardDataProvider(mock_indexer)
        assert not p.is_healthy()

def test_get_faction_net_profit_history(provider, mock_indexer):
    """Test net profit history query parsing."""
    cursor = mock_indexer.conn.cursor.return_value
    # Mock result: turn, faction, gross, upkeep, net
    cursor.fetchall.return_value = [
        (1, "Imperium", 100, 50, 50),
        (2, "Imperium", 120, 60, 60),
        (1, "Orks", 80, 80, 0)
    ]
    
    result = provider.get_faction_net_profit_history("u", "r", "all", "b", (0, 10))
    
    assert result["turns"] == [1, 2]
    assert "Imperium" in result["factions"]
    assert result["factions"]["Imperium"]["net_profit"] == [50, 60]
    assert result["factions"]["Orks"]["net_profit"] == [0]

def test_get_resource_roi_data_integration(provider, mock_indexer):
    """Test ROI data retrieval and formatting."""
    # provider.analytics is a Mock (patched in fixture)
    provider.analytics.economic_health_analyzer.calculate_resource_roi.return_value = {
        "roi_percentage": 15.5,
        "cumulative_income": 1000,
        "conquest_cost": 500,
        "payback_turns": 5
    }
    
    # Mock finding top planets
    cursor = mock_indexer.conn.cursor.return_value
    cursor.fetchall.return_value = [("Planet A", 5000)]
    
    # Helper to mock get_active_factions if needed, but we pass specific factions
    result = provider.get_resource_roi_data("u", "r", "b", ["Imperium"], (0, 10))
    
    assert len(result["roi_data"]) == 1
    entry = result["roi_data"][0]
    assert entry["faction"] == "Imperium"
    assert entry["category"] == "Planet A"
    assert entry["roi"] == 15.5
    
    # Verify analytics call
    provider.analytics.economic_health_analyzer.calculate_resource_roi.assert_called_with(
        "Imperium", "u", "Planet A"
    )

def test_get_all_factions_combat_effectiveness(provider, mock_indexer):
    """Test CER query."""
    cursor = mock_indexer.conn.cursor.return_value
    cursor.fetchall.return_value = [
        ("Imperium", 1.5),
        ("Orks", 0.8)
    ]
    
    result = provider.get_all_factions_combat_effectiveness("u", "r", "b", (0, 10))
    
    assert result["factions"]["Imperium"]["cer"] == 1.5
    assert result["factions"]["Orks"]["cer"] == 0.8
