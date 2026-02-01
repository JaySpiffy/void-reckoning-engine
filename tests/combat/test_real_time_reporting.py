import unittest
import os
from src.combat.combat_state import CombatState
from src.combat.reporting.real_time_replay import RealTimeReplayGenerator
from src.models.unit import Unit
from src.combat.real_time.map_manager import MapTemplates

class TestRealTimeReporting(unittest.TestCase):
    def setUp(self):
        # Setup mock units
        self.u1 = Unit("Infantry", 10, 10, 100, 5, 10, {}, faction="Faction_A")
        self.u2 = Unit("Tank", 12, 12, 500, 10, 50, {}, faction="Faction_B")
        self.u1.grid_x, self.u1.grid_y = 10, 10
        self.u2.grid_x, self.u2.grid_y = 90, 90
        
        armies = {"Faction_A": [self.u1], "Faction_B": [self.u2]}
        self.state = CombatState(armies, {}, {})
        self.state.initialize_battle()
        MapTemplates.apply_land_forest_ruins(self.state.grid)

    def test_report_generation(self):
        # Simulate some ticks
        dt = 0.1
        for _ in range(30): # 3 seconds
            self.state.real_time_update(dt)
        
        # Manually log some events to test PAR
        self.state.log_event("shooting", "Infantry", "Tank", "DMG: 20")
        self.state.log_event("capture", "Faction_A", "North Hill", "Owned by Faction_A")
        self.state.log_event("morale", "Tank", "Unit", "State changed to Routing")
        
        gen = RealTimeReplayGenerator(self.state)
        par = gen.generate_par()
        
        self.assertEqual(par["meta"]["winner"], "Draw") # Both alive
        self.assertEqual(par["factions"]["Faction_A"]["damage_dealt"], 20)
        self.assertEqual(len(par["objective_timeline"]), 1)
        
        # Export
        json_path = "test_battle.json"
        html_path = "test_battle.html"
        gen.export_json(json_path)
        gen.export_html_summary(html_path)
        
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(html_path))
        
        # Cleanup
        os.remove(json_path)
        os.remove(html_path)

if __name__ == "__main__":
    unittest.main()
