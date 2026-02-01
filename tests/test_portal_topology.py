import pytest
from src.core.simulation_topology import GraphNode, GraphEdge, PortalNode
from src.managers.galaxy_generator import GalaxyGenerator
from src.services.pathfinding_service import PathfindingService
from src.models.fleet import Fleet
from src.core.universe_data import UniverseDataManager

class TestPortalTopology:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Mock UniverseDataManager for tests
        UniverseDataManager._instance = None
        self.udm = UniverseDataManager.get_instance()
        self.udm.universe_name = "eternal_crusade"
        
        self.pathfinder = PathfindingService()
        self.gen1 = GalaxyGenerator()
        self.gen2 = GalaxyGenerator()
    
    def test_portal_node_attributes(self):
        """Verify GraphNode correctly stores portal attributes."""
        portal = PortalNode(
            node_id="p1", 
            portal_dest_universe="eternal_crusade",
            portal_dest_coords=(10, 20),
            portal_id="portal_alpha"
        )
        
        assert portal.is_portal()
        assert portal.metadata["portal_dest_universe"] == "eternal_crusade"
        assert portal.metadata["portal_dest_coords"] == (10, 20)
        assert portal.metadata["portal_id"] == "portal_alpha"
        assert "PORTAL to eternal_crusade" in repr(portal)

    def test_bidirectional_linking(self):
        """Verify linking between portals in different universes."""
        # Setup Portal in Universe A
        p_a = PortalNode("p_a", portal_id="link_1", portal_dest_universe="universe_b")
        self.gen1.portals = [p_a]
        
        # Setup Portal in Universe B
        p_b = PortalNode("p_b", portal_id="link_1", portal_dest_universe="eternal_crusade")
        self.gen2.portals = [p_b]
        
        # Link them
        count = self.gen1.link_cross_universe_portals(self.gen2, "universe_b")
        
        assert count == 1
        assert len(p_a.edges) == 1
        assert p_a.edges[0].target == p_b
        assert p_a.edges[0].distance == 50
        assert len(p_b.edges) == 1
        assert p_b.edges[0].target == p_a

    def test_pathfinding_with_portal(self):
        """Verify pathfinding detects and returns portal metadata."""
        start = GraphNode("start", "Planet")
        portal = PortalNode("p", portal_id="link_1", portal_dest_universe="eternal_crusade")
        destination = GraphNode("dest", "Planet")
        
        # start -> portal (Universe A)
        start.add_edge(portal, distance=10)
        # portal -> destination (Universe B) - this edge represents a cross-universe link
        portal.add_edge(destination, distance=50)
        
        path, cost, meta = self.pathfinder.find_path(start, destination)
        print(f"DEBUG_PATH: {path}")
        
        assert path is not None
        assert len(path) == 2
        assert cost == 10
        assert meta.get("requires_handoff")
        assert meta.get("portal_node") == portal

    def test_fleet_portal_detection(self):
        """Verify fleet update_movement detects arrival at portal."""
        # Setup basic topology
        start = GraphNode("start", "Planet")
        portal = PortalNode("portal", portal_id="p1", portal_dest_universe="eternal_crusade")
        start.add_edge(portal, distance=1)
        
        # Mock Engine for context - Must differ from portal dest
        class MockEngine:
            def __init__(self):
                self.universe_name = "origin_universe"
                self.fleets = []
                self.turn = 1
        
        engine = MockEngine()
        
        # Fleet setup
        fleet = Fleet("F1", "Solar_Hegemony", start)
        fleet.current_node = start
        fleet.route = [portal]
        
        # Execute movement
        status = fleet.update_movement(engine=engine)
        
        assert status["status"] == "PORTAL_TRANSIT"
        assert fleet.current_node == portal
        assert len(fleet.route) == 0

    def test_portal_serialization(self):
        """Verify portal attributes survive to_dict/from_dict."""
        portal = PortalNode(
            node_id="p1", 
            portal_dest_universe="eternal_crusade",
            portal_id="portal_alpha"
        )
        
        data = portal.to_dict()
        restored = GraphNode.from_dict(data)
        
        assert restored.is_portal()
        assert restored.metadata["portal_dest_universe"] == "eternal_crusade"
        assert restored.metadata["portal_id"] == "portal_alpha"
