import unittest
import math
from src.combat.combat_state import CombatState
from src.combat.real_time.simulation_loop import SimulationLoop
from src.models.unit import Ship

class TestMoraleSystem(unittest.TestCase):
    def setUp(self):
        # Iron Vanguard Conscripts (Target) vs Solar Hegemony Custodian (Attacker)
        self.conscript = Ship("Vanguard_Conscript", 100, 50, 100, 10, 5, {}, faction="Iron_Vanguard")
        self.conscript.grid_x = 10
        self.conscript.grid_y = 10
        
        # Massive damage dealer to break morale
        self.attacker = Ship("Solar_Executioner", 100, 50, 1000, 50, 40, {}, faction="Solar_Hegemony")
        self.attacker.grid_x = 0
        self.attacker.grid_y = 10
        
        self.armies_dict = {
            "Iron_Vanguard": [self.conscript],
            "Solar_Hegemony": [self.attacker]
        }
        
        self.state = CombatState(self.armies_dict, {}, {})
        from src.combat.tactical_grid import TacticalGrid
        self.state.grid = TacticalGrid(100, 100)
        self.state.grid.update_unit_position(self.conscript, 10, 10)
        self.state.grid.update_unit_position(self.attacker, 0, 0)

    def test_morale_routing_on_damage(self):
        loop = SimulationLoop(tick_rate=20)
        loop.on_update = self.state.real_time_update
        
        print("\n[TEST] Commencing Morale Test: Breaking a Unit...")
        print(f"[TEST] Initial Morale: {self.conscript.morale_current}")
        
        # Run for 3 seconds of combat
        loop.start(duration_seconds=3.0)
        
        print(f"[TEST] Final Morale: {self.conscript.morale_current:.2f} | State: {self.conscript.morale_state}")
        print(f"[TEST] Final Pos: ({self.conscript.grid_x:.2f}, {self.conscript.grid_y:.2f})")
        
        # Verify Routing
        self.assertEqual(self.conscript.morale_state, "Routing", "Conscript should be routing after taking heavy damage.")
        
        # Verify Movement (Should have moved further away from attacker at x=0)
        self.assertGreater(self.conscript.grid_x, 10.0, "Routing unit should move away from the threat.")

    def test_morale_rally(self):
        # Force a unit to route, then move it away to see if it rallies
        self.conscript.morale_current = 45 # Start closer to rally threshold (50)
        self.conscript.morale_state = "Routing"
        
        loop = SimulationLoop(tick_rate=20)
        loop.on_update = self.state.real_time_update
        
        # Move attacker very far away (out of range)
        self.attacker.grid_x = 1000
        self.conscript.time_since_last_damage = 20.0 # Force recovery
        
        print("\n[TEST] Commencing Morale Test: Rallying a Unit...")
        loop.start(duration_seconds=5.0) # 5s * 5/s = 25 recovery -> 45 + 25 = 70 (Rallied)
        
        print(f"[TEST] Morale after rest: {self.conscript.morale_current:.2f} | State: {self.conscript.morale_state}")
        
        # It should rally when morale > 50
        self.assertIn(self.conscript.morale_state, ["Shaken", "Steady"])

if __name__ == '__main__':
    unittest.main()
