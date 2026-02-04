import pytest
from unittest.mock import MagicMock, patch
from src.managers.campaign_manager import CampaignEngine

def test_generate_run_summary_regression():
    """
    Test that generate_run_summary handles global statistics in the worker_stats dictionary.
    """
    # 1. Setup Engine mock
    engine = CampaignEngine(game_config={
        "simulation": {"num_runs": 1, "random_seed": 42},
        "campaign": {"num_systems": 2, "min_planets": 1, "max_planets": 1},
        "economy": {"starting_requisition": 10000}
    })
    engine.generate_galaxy(num_systems=2, min_planets=1, max_planets=1)
    
    # Mock report organizer to avoid IO
    engine.report_organizer = MagicMock()
    engine.report_organizer.run_path = "tmp_crash_test"
    
    # 2. Mock SimulationWorker._collect_stats to return mixed faction/global data
    mock_stats = {
        "Hegemony": {"Score": 1500, "P": 1, "R": 5000, "T": 5},
        "GLOBAL_PLANETS": 10,  # This should be skipped
        "GLOBAL_NEUTRAL": 5,    # This should be skipped
        "GLOBAL_DIPLOMACY": []  # This should be skipped
    }
    
    with patch("src.engine.runner.simulation_worker.SimulationWorker._collect_stats", return_value=mock_stats):
        # 3. Call generate_run_summary
        # Before the fix, this would raise AttributeError: 'int' object has no attribute 'get'
        try:
            engine.generate_run_summary()
        except AttributeError as e:
            pytest.fail(f"generate_run_summary crashed with global stats: {e}")
        except Exception as e:
            pytest.fail(f"generate_run_summary failed with unexpected error: {e}")

    # 4. Success is reaching here without exception
    print("SUCCESS: generate_run_summary handled global stats correctly.")

if __name__ == "__main__":
    test_generate_run_summary_regression()
