import pytest
from multiprocessing import Queue
from src.managers.fleet_queue_manager import FleetQueueManager
from src.utils.validation_schemas import PortalCommandSchema

class TestPortalHandoff:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Create dummy queues
        self.in_q = Queue()
        self.out_q = Queue()
        self.prog_q = Queue()
        
        # Initialize Manager
        # Note: This modifies the singleton. In a real suite we might need to reset/patch it.
        FleetQueueManager.initialize(self.in_q, self.out_q, self.prog_q)
        self.mgr = FleetQueueManager.get_instance()
        
        yield
        # Teardown logic if needed (e.g. resetting singleton)
        # FleetQueueManager._instance = None # Optional but good practice

    def test_manager_initialization(self):
        """Verify singleton instance."""
        inst = FleetQueueManager.get_instance()
        assert inst is not None
        assert inst == self.mgr

    def test_push_outgoing(self):
        """Verify pushing to outgoing queue."""
        success = self.mgr.push_outgoing({"action": "TEST"})
        assert success
        assert not self.out_q.empty()
        item = self.out_q.get()
        assert item["action"] == "TEST"

    def test_pop_incoming(self):
        """Verify popping from incoming queue."""
        self.in_q.put({"action": "INJECT"})
        item = self.mgr.pop_incoming(block=False)
        assert item["action"] == "INJECT"

    def test_progress_push(self):
        """Verify progress queue push."""
        self.mgr.push_progress("EVENT")
        assert not self.prog_q.empty()
        assert self.prog_q.get() == "EVENT"

    def test_schema_validation_integration(self):
        """Verify that validation schemas work with queue items."""
        # Based on previous logic, let's verify assumptions about structure
        real_payload = {
            "action": "INJECT_FLEET",
            "package": {
                "fleet_id": "f1",
                "faction": "Imperium",
                "units": [],
                "portal_exit_coords": (0, 0),
                "origin_universe": "uni_A",
                "destination_universe": "uni_B"
            }
        }
        
        try:
            cmd = PortalCommandSchema(**real_payload)
            assert cmd.action == "INJECT_FLEET"
            assert cmd.package.fleet_id == "f1"
        except Exception as e:
            pytest.fail(f"Schema validation failed: {e}")
