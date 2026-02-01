import unittest
from src.combat.combat_state import CombatState
from src.combat.tactical_grid import TacticalGrid
from src.models.unit import Unit

class TestMapScaling(unittest.TestCase):
    def create_mock_unit(self, name):
         # Unit(name, ma, md, hp, armor, damage, abilities, faction=None, traits=None)
         u = Unit(name, 40, 40, 10, 0, 5, {}, faction="TestFaction")
         return u

    def test_small_skirmish_scaling(self):
        """Test that < 20 units results in a 30x30 grid."""
        armies = {
            "FactionA": [self.create_mock_unit(f"A_{i}") for i in range(5)],
            "FactionB": [self.create_mock_unit(f"B_{i}") for i in range(5)]
        }
        # Total 10 units
        state = CombatState(armies, {}, {})
        state.initialize_battle()
        
        self.assertEqual(state.grid.width, 30)
        self.assertEqual(state.grid.height, 30)
        print(f"\n[TEST] Small Battle (10 units) -> Grid {state.grid.width}x{state.grid.height} (Expected 30x30)")

    def test_medium_battle_scaling(self):
        """Test that 20-59 units results in a 50x50 grid."""
        armies = {
            "FactionA": [self.create_mock_unit(f"A_{i}") for i in range(15)], # 15
            "FactionB": [self.create_mock_unit(f"B_{i}") for i in range(15)]  # 15
        }
        # Total 30 units
        state = CombatState(armies, {}, {})
        state.initialize_battle()
        
        self.assertEqual(state.grid.width, 50)
        self.assertEqual(state.grid.height, 50)
        print(f"[TEST] Medium Battle (30 units) -> Grid {state.grid.width}x{state.grid.height} (Expected 50x50)")

    def test_massive_battle_scaling(self):
        """Test that >= 150 units results in a 100x100 grid."""
        armies = {
            "FactionA": [self.create_mock_unit(f"A_{i}") for i in range(80)], 
            "FactionB": [self.create_mock_unit(f"B_{i}") for i in range(80)]
        }
        # Total 160 units
        state = CombatState(armies, {}, {})
        state.initialize_battle()
        
        self.assertEqual(state.grid.width, 100)
        self.assertEqual(state.grid.height, 100)
        print(f"[TEST] Massive Battle (160 units) -> Grid {state.grid.width}x{state.grid.height} (Expected 100x100)")

    def test_unit_placement_bounds(self):
        """Verify units are placed within the grid bounds."""
        armies = {
            "FactionA": [self.create_mock_unit(f"A_BOUNDS_{i}") for i in range(5)],
            "FactionB": [self.create_mock_unit(f"B_BOUNDS_{i}") for i in range(5)]
        }
        state = CombatState(armies, {}, {})
        state.initialize_battle()
        
        # Check Faction A (Left side)
        # Expected X range: 35% to 45% of 30 -> 10 to 13
        for u in armies["FactionA"]:
            # pos = state.grid.get_unit_position(u) 
            # TacticalGrid sets grid_x/y on unit directly
            x, y = u.grid_x, u.grid_y
            self.assertIsNotNone(x)
            self.assertIsNotNone(y)
            self.assertTrue(0 <= x < 30)
            self.assertTrue(0 <= y < 30)
            # Verify relative placement logic roughly
            self.assertTrue(x >= int(30 * 0.35))
            self.assertTrue(x <= int(30 * 0.45) + 5) # Tolerance for overflow check

if __name__ == '__main__':
    unittest.main()
