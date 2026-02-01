import unittest
from src.combat.combat_state import CombatState
from src.combat.real_time.simulation_loop import SimulationLoop
from src.models.unit import Component, Ship

class TestHardpointSniping(unittest.TestCase):
    def setUp(self):
        # Iron Vanguard Foundry Class (Target) vs Solar Hegemony Custodian Class (Sniper)
        # Foundry Class: hp=12000, armor=600, shield=400
        # Custodian Class (Sniping): hp=12000, armor=400, damage=3080
        
        self.foundry = Ship("Foundry_Class", 12000, 400, 12000, 600, 3724, {"Tags": ["Battleship"]}, faction="Iron_Vanguard", shield=400)
        self.foundry.morale_max = 10000
        self.foundry.morale_current = 10000
        
        # Explicit component mapping for Eternal Crusade
        self.foundry.components = [
            Component("Hull", 12000, "Hull"),
            Component("Void Shield Generator", 200, "Shield"),
            Component("Warp Engine", 200, "Engines"),
            Component("Macro Cannon Battery", 200, "Weapon")
        ]
        
        self.custodian = Ship("Custodian_Class", 12000, 400, 20000, 400, 3080, {}, faction="Solar_Hegemony")
        self.custodian.morale_max = 10000
        self.custodian.morale_current = 10000
        self.custodian.grid_x = 0
        self.custodian.grid_y = 0
        self.foundry.grid_x = 10
        self.foundry.grid_y = 10
        
        self.armies_dict = {
            "Iron_Vanguard": [self.foundry],
            "Solar_Hegemony": [self.custodian]
        }
        
        # Set up CombatState
        self.state = CombatState(self.armies_dict, {}, {})
        self.state.formations = [] # Placeholder for self.target_formation, which is not defined in the original context
        # Mock grid/spatial index for the test
        from src.combat.tactical_grid import TacticalGrid
        self.state.grid = TacticalGrid(100, 100)
        # Assuming self.ivan_army and self.solar_heg are lists of units,
        # and that the original grid update lines should be replaced by the loop.
        # If self.ivan_army and self.solar_heg are not defined, this will cause an error.
        # For now, I will assume they are meant to be self.armies_dict["Iron_Vanguard"] and self.armies_dict["Solar_Hegemony"]
        # to maintain syntactic correctness.
        self.ivan_army = self.armies_dict["Iron_Vanguard"]
        self.solar_heg = self.armies_dict["Solar_Hegemony"]
        for u in self.ivan_army + self.solar_heg:
            self.state.grid.update_unit_position(u, u.grid_x, u.grid_y)

    def test_hardpoint_sniping_logic(self):
        loop = SimulationLoop(tick_rate=20)
        loop.on_update = self.state.real_time_update
        
        print("\n[TEST] Commencing Hardpoint Sniping Test...")
        print(f"[TEST] Initial Shields: {self.foundry.shield_current}/{self.foundry.shield_max}")
        
        # Run until Shield Generator is destroyed
        # We'll run for 5 seconds (100 ticks)
        loop.start(duration_seconds=5.0)
        
        gen = next(c for c in self.foundry.components if "Shield" in c.name)
        print(f"[TEST] Shield Generator HP: {gen.current_hp}/{gen.max_hp} | Destroyed: {gen.is_destroyed}")
        print(f"[TEST] Foundry Shields after combat: {self.foundry.shield_current}")
        
        # Verify
        self.assertTrue(gen.is_destroyed, "Custodian should have prioritized and destroyed the Shield Generator.")
        self.assertEqual(self.foundry.shield_regen, 0, "Shield regeneration should be disabled when generator is destroyed.")
        self.assertEqual(self.foundry.shield_current, 0, "Shields should drop to 0 when generator is destroyed.")

if __name__ == '__main__':
    unittest.main()
