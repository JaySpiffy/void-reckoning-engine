import sys
import os
import pytest

# Add src to path
sys.path.append(os.getcwd())

from src.engine.runner.simulation_worker import SimulationWorker
from src.engine.runner.progress_dashboard import ProgressDashboard
from src.engine.runner.results_aggregator import ResultsAggregator

class TestRunnerRefactor:
    def test_component_imports(self):
        """Verify components can be imported and instantiated."""
        dashboard = ProgressDashboard()
        assert dashboard is not None
        
        aggregator = ResultsAggregator("dummy_path", 1)
        assert aggregator is not None
        
        # Worker is static but class should exist
        assert hasattr(SimulationWorker, 'run_single_campaign_logic')
        print("\n[PASS] Simulation Runner components verified.")
