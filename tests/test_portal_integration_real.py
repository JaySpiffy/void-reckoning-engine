import pytest
import time
import multiprocessing
import queue
from unittest.mock import MagicMock, patch
from src.engine.multi_universe_runner import MultiUniverseRunner

class TestPortalIntegrationReal:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Use real multiprocessing manager for partial integration test
        self.manager = multiprocessing.Manager()
        self.u1_q = self.manager.Queue()
        self.u2_q = self.manager.Queue()
        
        # Patch UDM to avoid loading real configs
        # Use patch decorator context for scope of fixture
        with patch('src.core.universe_data.UniverseDataManager') as mock_udm_cls:
            self.mock_udm = mock_udm_cls.get_instance.return_value
            self.mock_udm.rehydrate_for_universe.side_effect = lambda dna, dest: dna # Identity translation
            
            self.runner = MultiUniverseRunner([])
            self.runner.progress_queues = {
                "u1": self.u1_q,
                "u2": self.u2_q
            }
            
            # Mock queues for fleets
            self.runner.universe_queues = {
                "u1": {"outgoing": self.manager.Queue(), "incoming": self.manager.Queue()},
                "u2": {"outgoing": self.manager.Queue(), "incoming": self.manager.Queue()}
            }
            yield
            
    def test_handoff_timeout_recovery(self):
        """
        Verify that if the source universe fails to confirm removal within the timeout,
        the handoff is aborted and returns False.
        """
        # Mock async results (Destination is running)
        async_results = {"u2": type('obj', (object,), {'ready': lambda: False})}
        
        package = {
            "fleet_id": "f_timeout",
            "faction": "TestFaction",
            "origin_universe": "u1",
            "destination_universe": "u2",
            "units": [] 
        }
        
        # Start time
        t0 = time.time()
        
        # We purposely DO NOT put a confirmation message in u1_q
        
        result = self.runner.handle_portal_handoff(package, "u1", "u2", async_results)
        
        duration = time.time() - t0
        
        # Should return False due to timeout
        assert not result
        
        # Should have waited approx 5 seconds (from current hardcoded buffer time)
        assert duration >= 4.5
        
    def test_handoff_success_with_delayed_confirmation(self):
        """
        Verify that if confirmation arrives late but within window, it proceeds.
        """
        async_results = {"u2": type('obj', (object,), {'ready': lambda: False})}
        
        package = {
            "fleet_id": "f_success",
            "faction": "TestFaction", # Added faction
            "origin_universe": "u1",
            "destination_universe": "u2",
            "units": []
        }
        
        # Inject confirmation after a slight delay
        self.u1_q.put((0, 1, "Running", {}))
        self.u1_q.put((0, 2, "FLEET_REMOVED", "f_success")) # The signal
        
        result = self.runner.handle_portal_handoff(package, "u1", "u2", async_results)
        
        assert result
        
        # Verify Injection to U2
        u2_in = self.runner.universe_queues["u2"]["incoming"]
        assert not u2_in.empty()
        cmd = u2_in.get()
        assert cmd["action"] == "INJECT_FLEET"
        assert cmd["package"]["fleet_id"] == "f_success"

    def test_handoff_refund_on_dest_failure(self):
        """
        Verify that if destination dies mid-process, fleet is refunded to source.
        """
        # We need a dynamic mock for ready()
        ready_states = [False, True] # First call False (Alive), Second call True (Dead)
        result_mock = MagicMock()
        result_mock.ready.side_effect = ready_states
        
        async_results = {"u2": result_mock}
        
        package = {
            "fleet_id": "f_refund",
            "faction": "TestFaction",
            "origin_universe": "u1",
            "destination_universe": "u2",
            "units": []
        }
        
        # Immediate confirmation
        self.u1_q.put((0, 2, "FLEET_REMOVED", "f_refund"))
        
        result = self.runner.handle_portal_handoff(package, "u1", "u2", async_results)
        
        # Should return False (Handoff failed)
        assert not result
        
        # Verify Refund to U1
        u1_in = self.runner.universe_queues["u1"]["incoming"]
        assert not u1_in.empty()
        cmd = u1_in.get()
        assert cmd["action"] == "INJECT_FLEET"
        assert cmd["package"]["fleet_id"] == "f_refund"
        assert cmd["package"].get("is_refund")
