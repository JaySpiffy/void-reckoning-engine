import unittest
import math
from unittest.mock import MagicMock
from src.combat.rust_tactical_engine import RustTacticalEngine
from src.core.constants import TACTICAL_GRID_SIZE, ACTIVE_FACTION_UNIT_CAP

class MockUnit:
    def __init__(self, name, faction, hp=100.0):
        self.name = name
        self.faction = faction
        self.max_hp = hp
        self.current_hp = hp
        self.is_destroyed = False
        self.damage = 10.0
        self.weapon_comps = []

class TestCombatScaling(unittest.TestCase):
    def setUp(self):
        self.engine = RustTacticalEngine()
        if not self.engine.rust_engine:
            self.skipTest("Rust Engine unavailable")

    def test_grid_expansion_dimensions(self):
        """Achievement 2: Verify the grid is expanded to 500x500."""
        self.assertEqual(self.engine.width, 500.0, "Grid width should be 500.0")
        self.assertEqual(self.engine.height, 500.0, "Grid height should be 500.0")
        self.assertEqual(TACTICAL_GRID_SIZE, 500.0, "Constant TACTICAL_GRID_SIZE should be 500.0")

    def test_reinforcement_caps(self):
        """Achievement 1: Verify 200 unit active cap per faction."""
        # Create 300 units for Empire
        armies = {
            "Empire": [MockUnit(f"E_{i}", "Empire") for i in range(300)],
            "Rebels": [MockUnit(f"R_{i}", "Rebels") for i in range(50)]
        }
        
        self.engine.initialize_battle(armies)
        
        # Check active units in Rust
        state = self.engine.get_state()
        empire_active = sum(1 for row in state if self.engine.id_to_faction.get(row[0]) == "Empire" and row[4])
        rebels_active = sum(1 for row in state if self.engine.id_to_faction.get(row[0]) == "Rebels" and row[4])
        
        self.assertEqual(empire_active, ACTIVE_FACTION_UNIT_CAP, f"Empire should have exactly {ACTIVE_FACTION_UNIT_CAP} units active")
        self.assertEqual(rebels_active, 50, "Rebels should have all 50 units active (below cap)")
        self.assertEqual(len(self.engine.reserves["Empire"]), 100, "Empire should have 100 units in reserve")

    def test_reinforcement_warp_in(self):
        """Achievement 1: Verify units warp-in when active units die."""
        armies = {
            "Empire": [MockUnit(f"E_{i}", "Empire", hp=1.0) for i in range(210)]
        }
        self.engine.initialize_battle(armies)
        
        # Initially 200 active, 10 reserve
        self.assertEqual(len(self.engine.reserves["Empire"]), 10, "Should start with 10 in reserve")
        
        # Capture real state
        real_rust = self.engine.rust_engine
        raw_state = list(self.engine.rust_engine.get_state())
        
        # Mocking a dead unit: Set the 5th element (alive) to False for the first 5 units
        mock_state = []
        for row in raw_state:
            new_row = list(row)
            if new_row[0] <= 5: # Kill first 5 IDs
                new_row[4] = False
            mock_state.append(tuple(new_row))
            
        # Replace rust_engine with a mock
        self.engine.rust_engine = MagicMock()
        self.engine.rust_engine.get_state.return_value = mock_state
        
        # Trigger reinforcement
        self.engine._process_reinforcements()
        
        # Should have warped in 5 units (now 5 in reserve)
        # Note: id_to_faction and other state remains on the Python wrapper
        self.assertEqual(len(self.engine.reserves["Empire"]), 5, "5 units should have warped in from reserves")
        
        # Restore
        self.engine.rust_engine = real_rust

    def test_deployment_scaling(self):
        """Achievement 2: Verify circular deployment scales to grid size."""
        # 3 factions
        armies = {
            "F1": [MockUnit("U1", "F1")],
            "F2": [MockUnit("U2", "F2")],
            "F3": [MockUnit("U3", "F3")]
        }
        self.engine.initialize_battle(armies)
        
        # Check centers
        # Center of 500,500 is 250,250
        # Radius is 500 * 0.4 = 200
        # Centers should be ~200 units away from 250,250
        for f, pos in self.engine.faction_centers.items():
            dist = math.sqrt((pos[0]-250)**2 + (pos[1]-250)**2)
            self.assertAlmostEqual(dist, 200.0, delta=1.0, msg=f"Faction {f} should be deployed on the 200-radius ring")

    def test_rust_performance_optimization(self):
        """Achievement 3: Verify performance with 1000 units."""
        import time
        armies = {
            "A": [MockUnit(f"A_{i}", "A") for i in range(500)],
            "B": [MockUnit(f"B_{i}", "B") for i in range(500)]
        }
        self.engine.initialize_battle(armies)
        
        start = time.time()
        for _ in range(5):
            self.engine.resolve_round()
        duration = time.time() - start
        
        # For 1000 units (400 active), 5 rounds should be very fast (< 0.1s)
        # Linear O(N^2) would take much longer as N increases.
        print(f"\n[BENCHMARK] 5 rounds with 400 active units took: {duration:.4f}s")
        self.assertLess(duration, 0.5, "Rust engine tick is too slow for 400 units (Spatial Hash missing?)")

if __name__ == "__main__":
    unittest.main()
