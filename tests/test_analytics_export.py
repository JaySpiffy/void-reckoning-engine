import pytest
import os
import shutil
import json
from unittest.mock import MagicMock
import sys

# Handle environment dependencies
libs_to_mock = ['scipy', 'scipy.stats', 'sklearn', 'sklearn.linear_model', 'networkx', 'plotly', 'matplotlib', 'matplotlib.pyplot']
for lib in libs_to_mock:
    if lib not in sys.modules:
        m = MagicMock()
        m.__version__ = "1.0.0"
        sys.modules[lib] = m

# Force CuPy to be missing
sys.modules['cupy'] = None

# Mock Pandas if missing
try:
    import pandas as pd
except ImportError:
    if 'pandas' not in sys.modules:
         mock_pd = MagicMock()
         sys.modules['pandas'] = mock_pd
         pd = mock_pd
         
    class MockDataFrame:
        def __init__(self, data=None):
            self.data = data or {}
            self._empty = not bool(self.data)
        
        @property
        def empty(self):
            return self._empty
        
        def __getitem__(self, key):
             val = self.data.get(key, [])
             m = MagicMock()
             m.values = val
             m.__iter__ = lambda x: iter(val if isinstance(val, (list, tuple)) else [])
             m.iloc = MagicMock()
             m.iloc.__getitem__ = lambda s, idx: val[idx] if isinstance(val, (list, tuple)) and idx < len(val) else 0
             
             if isinstance(val, (list, tuple)) and len(val) > 0:
                 m.max.return_value = max(val)
                 m.mean.return_value = sum(val)/len(val)
             else:
                 m.max.return_value = 0
                 m.mean.return_value = 0
             m.std.return_value = 0
             
             vc = MagicMock()
             vc.head.return_value = vc
             vc.to_dict.return_value = {"Test": 1}
             m.value_counts.return_value = vc
             
             m.cumsum.return_value = val 
             m.diff.return_value = m 
             m.fillna.return_value = m
             return m
             
        @property
        def columns(self):
            return list(self.data.keys())
            
        def __setitem__(self, key, value):
             self.data[key] = value
             self._empty = False
             
        def tail(self, n): return self
        def pivot_table(self, **kwargs):
             m = MagicMock()
             m.values = [[0]]
             return m
        def pivot(self, **kwargs): return self
        def fillna(self, val): return self
        def iterrows(self): return []
        def std(self): return 0
        def mean(self): return 0

    pd.DataFrame = MockDataFrame
    pd.read_sql_query = lambda q, c, params=None: MockDataFrame() 

from src.reporting.faction_reporter import FactionReporter
from src.reporting.analytics_engine import AnalyticsEngine
from src.reporting.indexing import ReportIndexer

@pytest.fixture
def analytics_setup(tmp_path):
    test_dir = tmp_path / "temp_analytics"
    os.makedirs(test_dir, exist_ok=True)
    
    # Mock Engine and Indexer
    mock_engine = MagicMock()
    mock_engine.universe_data.name = "TestUniv"
    mock_engine.factions = {"Imperium": MagicMock(), "Chaos": MagicMock()}
    mock_engine.report_organizer = MagicMock()
    # Batch dir needs to be a string normally
    mock_engine.report_organizer.batch_dir = str(test_dir)
    
    reporter = FactionReporter(mock_engine)
    
    # Mock Analytics Engine + Indexer
    mock_indexer = MagicMock(spec=ReportIndexer)
    # Mock Analyzers directly
    reporter.analytics_engine.trend_analyzer = MagicMock()
    reporter.analytics_engine.anomaly_detector = MagicMock()
    reporter.analytics_engine.comparative_analyzer = MagicMock()
    reporter.analytics_engine.predictive_analytics = MagicMock()
    reporter.analytics_engine.tech_analyzer = MagicMock()
    reporter.analytics_engine.difficulty_analyzer = MagicMock()
    reporter.analytics_engine.ai_analyzer = MagicMock()
    reporter.analytics_engine.portal_analyzer = MagicMock()
    reporter.analytics_engine.resource_exhaustion = MagicMock()

    # Mock Data Responses
    reporter.analytics_engine.trend_analyzer.analyze_win_rate_trajectory.return_value = {"trend": "improving"}
    reporter.analytics_engine.anomaly_detector.detect_battle_anomalies.return_value = []
    reporter.analytics_engine.comparative_analyzer.calculate_faction_balance_score.return_value = 85.0
    reporter.analytics_engine.difficulty_analyzer.calculate_difficulty_rating.return_value = "Normal"
    reporter.analytics_engine.portal_analyzer.analyze_usage_patterns.return_value = {"hubs": ["Terra"]}
    reporter.analytics_engine.resource_exhaustion.check_exhaustion_risk.return_value = {"risk": "low"}
    reporter.analytics_engine.tech_analyzer.calculate_tech_velocity.return_value = {"velocity": 1.5}
    reporter.analytics_engine.ai_analyzer.detect_behavior_deviations.return_value = []
    
    # Mock indexer data
    mock_indexer.query_faction_time_series.return_value = pd.DataFrame({
        "turn": [1, 2, 3],
        "requisition": [100, 200, 300],
        "promethium": [10, 20, 30],
        "fleets_count": [1, 2, 5]
    })
    
    mock_indexer.query_battle_statistics.return_value = pd.DataFrame({
        "turn": [2, 3],
        "planet": ["Terra", "Cadia"],
        "rounds": [10, 5],
        "units_destroyed": [100, 50],
        "winner": ["Imperium", "Chaos"]
    })
    
    mock_indexer.query_latest_faction_stats.return_value = pd.DataFrame({
        "faction": ["Imperium", "Chaos"],
        "planets_controlled": [5, 5],
        "requisition": [1000, 1000], 
        "battles_won": [10, 10]
    })
    
    mock_indexer.query_tech_progression.return_value = pd.DataFrame({
        "turn": [1, 5],
        "tech_unlocks": [1, 2],
        "cumulative_techs": [1, 3]
    })
    
    mock_indexer.query_ai_action_patterns.return_value = pd.DataFrame({
        "construction_complete": [5, 6, 5],
        "unit_recruited": [10, 20, 10]
    })
    
    mock_indexer.query_portal_usage.return_value = pd.DataFrame({
        "turn": [1],
        "faction": ["Eldar"],
        "location": ["Webway Gate"]
    })
    
    mock_indexer.query_diplomacy_events.return_value = [("Imperium", "Eldar")]
    
    reporter.analytics_engine.indexer = mock_indexer
    
    return reporter, str(test_dir)

def test_export_analytics_report(analytics_setup):
    reporter, test_dir = analytics_setup
    reporter.export_analytics_report(test_dir)
    
    # Verify JSON
    json_path = os.path.join(test_dir, "analytics_summary.json")
    assert os.path.exists(json_path)
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        assert "difficulty_rating" in data
        assert "portal_patterns" in data
    
    # Verify Visualizations dir
    viz_dir = os.path.join(test_dir, "visualizations")
    assert os.path.exists(viz_dir)
