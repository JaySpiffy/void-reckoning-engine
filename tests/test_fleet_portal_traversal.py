import pytest
from unittest.mock import MagicMock, patch
from src.core.universe_data import UniverseDataManager
from src.models.fleet import Fleet
from src.core.simulation_topology import PortalNode, GraphNode
from src.models.planet import Planet
from src.services.pathfinding_service import PathfindingService

class MockQueue:
    def __init__(self):
        self.called = False
        self.calls = []
        
    def put(self, *args, **kwargs):
        print(f"DEBUG: MockQueue.put called with {args}")
        self.called = True
        self.calls.append(args)

class TestFleetPortalTraversal:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_udm = MagicMock()
        self.mock_udm.get_planet_classes.return_value = {"Terran": {"req_mod": 1.0, "def_mod": 1.0, "slots": 5}}
        
        # Patch get_instance to return our mock
        with patch('src.core.universe_data.UniverseDataManager.get_instance', return_value=self.mock_udm):
             # Initialize objects that might use UDM
             self.p1 = Planet("P1", 0, 0)
             self.fleet = Fleet("F1", "Solar_Hegemony", self.p1)
             
        self.engine = MagicMock()
        self.engine.turn = 42
        self.engine.universe_name = "eternal_crusade"
        self.engine.progress_queue = MockQueue()
        # Fleet logic prefers _progress_q_ref, so we must alias or set it to None to force fallback.
        # MagicMock auto-creates attributes so we must be explicit.
        self.engine._progress_q_ref = self.engine.progress_queue
            
    def test_traverse_portal_valid(self):
        """Test valid traversal on a portal node."""
        portal = PortalNode("portal_1", "To Eternal Crusade", "eternal_crusade", (100, 100), "p1")
        self.fleet.current_node = portal
        self.fleet.is_engaged = False
        
        result = self.fleet.traverse_portal(self.engine)
        
        assert result is not None
        assert result["fleet_id"] == "F1"
        assert result["portal_exit_coords"] == (100, 100)
        assert result["timestamp"] == 42
        
        assert self.fleet.in_portal_transit
        assert not self.fleet.is_destroyed # Should NOT be destroyed per Comment 2
        
        # Verify queue put
        print(f"DEBUG: Mock Calls: {self.engine.progress_queue.calls}")
        
        # Fallback assertion
        assert self.engine.progress_queue.called, "Queue.put was NOT called at all!"
        
        # Check args if called
        if self.engine.progress_queue.called:
            args = self.engine.progress_queue.calls[0]
            val = args[0] # First arg (tuple)
            assert val[2] == "PORTAL_HANDOFF"
        
    def test_traverse_portal_invalid_node(self):
        """Test traversal on a non-portal node."""
        node = GraphNode("n1", "Normal Node")
        self.fleet.current_node = node
        
        result = self.fleet.traverse_portal(self.engine)
        
        assert result is None
        assert not self.fleet.in_portal_transit
        
    def test_traverse_portal_engaged(self):
        """Test traversal when engaged in combat."""
        portal = PortalNode("portal_1", "To Eternal Crusade", "eternal_crusade", (100, 100), "p1")
        self.fleet.current_node = portal
        self.fleet.is_engaged = True
        
        result = self.fleet.traverse_portal(self.engine)
        
        assert result is None
        assert not self.fleet.in_portal_transit

    def test_pathfinding_portal_metadata(self):
        """Test that pathfinder detects portals and returns metadata."""
        pf = PathfindingService()
        n1 = GraphNode("n1", "Start")
        n2 = GraphNode("n2", "Mid")
        portal = PortalNode("p1", "Portal", "eternal_crusade", (10, 10), "pid")
        
        n1.add_edge(n2, 1)
        n2.add_edge(portal, 1)
        
        path, cost, meta = pf.find_path(n1, portal)
        
        assert path is not None
        assert meta.get("requires_handoff")
        assert meta.get("dest_universe") == "eternal_crusade"
        assert meta.get("portal_node") == portal
