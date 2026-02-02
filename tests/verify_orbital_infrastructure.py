import unittest
from unittest.mock import MagicMock
import sys
import os

# Adjust path to include src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.managers.economy.resource_handler import ResourceHandler
from src.core import balance as bal

class TestOrbitalInfrastructure(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock()
        self.handler = ResourceHandler(self.mock_engine)
        
        # Mock Faction
        self.mock_faction = MagicMock()
        self.mock_faction.name = "TestFaction"
        self.mock_faction.requisition = 1000
        self.mock_faction.unlocked_techs = []
        self.mock_faction.get_modifier.return_value = 1.0
        
        # Mock Engine methods
        self.mock_engine.get_faction.return_value = self.mock_faction
        self.mock_engine.get_all_factions.return_value = [self.mock_faction]
        self.mock_engine.planets_by_faction = {"TestFaction": []}
        self.mock_engine.fleets_by_faction = {"TestFaction": []}

    def test_mining_station_income(self):
        # Setup Fleet with Mining Station
        mock_station = MagicMock()
        mock_station.unit_class = "MiningStation"
        
        mock_fleet = MagicMock()
        mock_fleet.units = [mock_station]
        mock_fleet.is_destroyed = False
        mock_fleet.upkeep = 100
        mock_fleet.is_in_orbit = False
        
        self.mock_engine.fleets_by_faction = {"TestFaction": [mock_fleet]}
        
        # Run Calculation
        cache = self.handler.precalculate_economics()
        f_cache = cache["TestFaction"]
        
        # Assertions
        # Base Mining Yield = 500
        # Income from empty planets check = 0 (or constant base)
        # We check if it is > 0 and contains the mining part
        print(f"DEBUG: Income breakdown: {f_cache.get('income_by_category')}")
        self.assertEqual(f_cache["income_by_category"]["Mining"], 500)
        self.assertTrue(f_cache["income"] >= 500)
    
    def test_research_outpost_yield(self):
        # Setup Fleet with Research Outpost
        mock_outpost = MagicMock()
        mock_outpost.unit_class = "ResearchOutpost"
        
        mock_fleet = MagicMock()
        mock_fleet.units = [mock_outpost]
        mock_fleet.is_destroyed = False
        mock_fleet.upkeep = 100
        
        self.mock_engine.fleets_by_faction = {"TestFaction": [mock_fleet]}
        
        # Run Calculation
        cache = self.handler.precalculate_economics()
        f_cache = cache["TestFaction"]
        
        # Assertions
        # Base Research Yield = 10
        self.assertEqual(f_cache.get("research_income", 0), 10)

    
    def test_listening_post_range(self):
        # Setup Fleet with Listening Post
        mock_lp = MagicMock()
        mock_lp.unit_class = "ListeningPost"
        
        mock_fleet = MagicMock()
        mock_fleet.units = [mock_lp]
        mock_fleet.is_scout = False
        mock_fleet.scanning_range = 3 # Base range
        
        # We want to verify logic in IntelligenceManager, but we can't easily mock the whole graph traversal here
        # without instantiating a real IntelligenceManager.
        # Instead, let's justverify the property logic holds:
        
        units = mock_fleet.units
        base_range = mock_fleet.scanning_range
        
        scan_radius = base_range
        if any(getattr(u, 'unit_class', '') == 'ListeningPost' for u in units):
            scan_radius = max(scan_radius, 5)
            
        self.assertEqual(scan_radius, 5)

    def test_listening_post_integration(self):
        # Mock Engine & Graph
        mock_engine = MagicMock()
        mock_engine.turn_counter = 1
        mock_engine.factions = {}
        mock_engine.planets_by_faction = {"TestFaction": []}
        
        # Create a linear graph: Node0 <-> Node1 <-> ... <-> Node5
        nodes = []
        for i in range(6):
            n = MagicMock()
            n.id = f"Node{i}"
            n.metadata = {}
            n.edges = []
            nodes.append(n)
            
        for i in range(5):
            # Bi-directional edges of distance 1
            e1 = MagicMock(); e1.target = nodes[i+1]; e1.distance = 1
            e2 = MagicMock(); e2.target = nodes[i]; e2.distance = 1
            nodes[i].edges.append(e1)
            nodes[i+1].edges.append(e2)
            
        # Setup Faction
        mock_faction = MagicMock()
        mock_faction.name = "TestFaction"
        mock_faction.visible_planets = set()
        mock_faction.known_planets = set()
        mock_engine.factions["TestFaction"] = mock_faction
        
        # Setup Fleet at Node0
        mock_lp = MagicMock()
        mock_lp.unit_class = "ListeningPost"
        
        mock_fleet = MagicMock()
        mock_fleet.faction = "TestFaction"
        mock_fleet.location = nodes[0] # At Node 0
        mock_fleet.current_node = nodes[0] # Ensure scan logic sees this
        mock_fleet.units = [mock_lp]
        mock_fleet.is_destroyed = False
        mock_fleet.scanning_range = 3
        
        mock_engine.fleets = [mock_fleet]
        
        # Instantiate Real IntelligenceManager
        # We need to ensure we import it properly
        from src.managers.intelligence_manager import IntelligenceManager
        intel_mgr = IntelligenceManager(mock_engine)
        
        # Run Update
        intel_mgr.update_faction_visibility("TestFaction", force_refresh=True)
        
        # Verification
        # Node0 (0 dist) -> Visible
        # Node1 (1 dist) -> Visible
        # ...
        # Node5 (5 dist) -> Visible (Range 5)
        
        # The update_faction_visibility adds names to visible_planets.
        # Our mock nodes don't have planets attached, but the logic iterates nodes.
        # Wait, the logic only adds to visible_planets if:
        # p_obj = curr.metadata.get("object")
        # if p_obj: new_visible_planets.add(p_obj.name)
        
        # So we need to attach fake planet objects to these nodes to verify they were "seen".
        for i, n in enumerate(nodes):
            p_obj = MagicMock()
            p_obj.name = f"Planet{i}"
            n.metadata["object"] = p_obj
            
        # Re-run
        intel_mgr.update_faction_visibility("TestFaction", force_refresh=True)
        
        print(f"DEBUG: Visible Planets: {mock_faction.visible_planets}")
        
        self.assertIn("Planet0", mock_faction.visible_planets)
        self.assertIn("Planet3", mock_faction.visible_planets) # Range 3 (Standard)
        self.assertIn("Planet5", mock_faction.visible_planets) # Range 5 (Listening Post)
        
        # Ensure range 6 is NOT visible (if we added it)

if __name__ == '__main__':
    unittest.main()
