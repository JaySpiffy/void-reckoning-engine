import pytest
import time
from unittest.mock import MagicMock, patch
from src.reporting.analytics_engine import AnalyticsEngine

@pytest.fixture
def mock_indexer():
    indexer = MagicMock()
    indexer.conn = MagicMock()
    return indexer

@pytest.fixture
def analytics_engine(mock_indexer):
    # Patch all specialized analyzers to avoid complex dependencies
    with patch("src.reporting.analytics_engine.TrendAnalyzer"), \
         patch("src.reporting.analytics_engine.AnomalyDetector"), \
         patch("src.reporting.analytics_engine.EconomicHealthAnalyzer"), \
         patch("src.reporting.analytics_engine.MilitaryEfficiencyAnalyzer"), \
         patch("src.reporting.analytics_engine.IndustrialAnalyzer"), \
         patch("src.reporting.analytics_engine.TechAnalyzer"), \
         patch("src.reporting.analytics_engine.ResearchAnalyzer"), \
         patch("src.reporting.analytics_engine.AIAnalyzer"), \
         patch("src.reporting.analytics_engine.PortalAnalyzer"), \
         patch("src.reporting.analytics_engine.ComparativeAnalyzer"), \
         patch("src.reporting.analytics_engine.DifficultyAnalyzer"), \
         patch("src.reporting.analytics_engine.ResourceExhaustionAnalyzer"), \
         patch("src.reporting.analytics_engine.PredictiveAnalytics"):
         
        engine = AnalyticsEngine(mock_indexer)
        return engine

def test_caching_logic(analytics_engine):
    """Test cache validity and expiration."""
    # valid
    analytics_engine.cache["valid_key"] = ("data", 100)
    assert analytics_engine._is_cache_valid("valid_key", 50)
    assert not analytics_engine._is_cache_valid("valid_key", 150)
    
    # expired cleanup
    analytics_engine.cache["expired_key"] = ("data", 10)
    analytics_engine._cleanup_expired_cache(20)
    assert "expired_key" not in analytics_engine.cache
    assert "valid_key" in analytics_engine.cache

def test_get_comprehensive_analysis_orchestration(analytics_engine):
    """Test that it gathers data from sub-analyzers."""
    # Setup mocks
    analytics_engine.economic_health_analyzer.calculate_stockpile_velocity.return_value = 1.0
    analytics_engine.military_efficiency_analyzer.analyze_combat_effectiveness.return_value = {"val": 5}
    
    # Mock get_real_time_insights since it's called internally
    with patch.object(analytics_engine, 'get_real_time_insights', return_value={"summary": "good"}):
        result = analytics_engine.get_comprehensive_analysis("Imperium", "test_universe", 50)
        
        assert result["economic_health"]["velocity"] == 1.0
        assert result["military_efficiency"]["combat_effectiveness"] == {"val": 5}
        assert result["summary_insights"] == {"summary": "good"}
        
        # Check cache was populated
        assert "comprehensive_Imperium_test_universe_50" in analytics_engine.cache

def test_detect_and_trigger_alerts_integration(analytics_engine):
    """Test alert triggering flow."""
    # Mock pandas reading sql
    with patch("pandas.read_sql_query") as mock_pd:
        # 1. Factions query
        mock_factions = MagicMock()
        mock_factions.__getitem__.return_value.tolist.return_value = ["Imperium"]
        
        # 2. ROI key planet query (not used here but good to know)
        
        mock_pd.side_effect = [mock_factions, MagicMock(), MagicMock()] 
        
        # Mock AnomalyDetector returning anomalies
        analytics_engine.anomaly_detector.detect_resource_spikes.return_value = [
            {"type": "economic_death_spiral", "velocity": -5, "projected_bankruptcy_turn": 60}
        ]
        analytics_engine.anomaly_detector.detect_military_inefficiency.return_value = None
        analytics_engine.anomaly_detector.detect_idle_infrastructure.return_value = None
        analytics_engine.anomaly_detector.detect_research_stagnation.return_value = None

        # Mock AlertManager
        with patch("src.reporting.alert_manager.AlertManager") as MockAM:
            am_instance = MockAM.return_value
            
            analytics_engine.detect_and_trigger_alerts("test_universe", 50)
            
            # Verify trigger
            am_instance.trigger_alert.assert_called()
            args = am_instance.trigger_alert.call_args
            assert args[0][1] == "Economic Death Spiral" # rule_name
            assert "velocity -5" in args[0][2] # message

def test_get_real_time_insights_with_cache(analytics_engine):
    """Test getting insights uses cache."""
    # Populate cache
    analytics_engine.cache["insights_Imperium_test_universe_50"] = ({"cached": True}, 60)
    
    result = analytics_engine.get_real_time_insights("Imperium", "test_universe", 50)
    assert result == {"cached": True}
    
    # Verify sub-analyzers NOT called
    analytics_engine.trend_analyzer.analyze_win_rate_trajectory.assert_not_called()
