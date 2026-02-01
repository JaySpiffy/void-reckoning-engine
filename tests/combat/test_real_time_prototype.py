import unittest
import time
from src.combat.combat_state import CombatState
from src.combat.real_time.simulation_loop import SimulationLoop
from src.models.unit import Ship

class TestRealTimePrototype(unittest.TestCase):
    def setUp(self):
        # Solar Hegemony vs Iron Vanguard
        # Barracuda Fighters (Solar Hegemony) attacking a Hammer Class Frigate (Iron Vanguard)
        
        self.frigate = Ship("Hammer_Class", 100, 50, 800, 10, 50, {"Tags": ["Frigate"]}, faction="Iron_Vanguard", shield=100)
        self.frigate.morale_max = 1000
        self.frigate.morale_current = 1000
        self.frigate.grid_x = 90.0 
        self.frigate.grid_y = 90.0 
        
        self.fighters = [
            Ship(f"Barracuda_{i}", 50, 10, 50, 0, 10, {"Tags": ["Fighter"]}, faction="Solar_Hegemony") 
            for i in range(5)
        ]
        
        # Space out fighters and set morale
        for i, f in enumerate(self.fighters):
            f.morale_max = 1000
            f.morale_current = 1000
            f.grid_x = 10.0 
            f.grid_y = 10.0 + 2.0 * i
            
        self.armies_dict = {
            "Iron_Vanguard": [self.frigate],
            "Solar_Hegemony": self.fighters
        }
        
        self.state = CombatState(self.armies_dict, {}, {})
        # Initialize grid for real_time_update
        from src.combat.tactical_grid import TacticalGrid
        self.state.grid = TacticalGrid(100, 100)
        self.state.grid.update_unit_position(self.frigate, 90.0, 90.0)
        for f in self.fighters:
            self.state.grid.update_unit_position(f, f.grid_x, f.grid_y)
        
    def test_simulation_movement_and_flocking(self):
        loop = SimulationLoop(tick_rate=20)
        loop.on_update = self.state.real_time_update
        
        f1 = self.fighters[0]
        f2 = self.fighters[1]
        
        start_x = f1.grid_x
        start_y = f1.grid_y
        
        print("\n[TEST] Starting Real-Time Simulation (2 seconds)...")
        loop.start(duration_seconds=2.0)
        
        print(f"[TEST] Barracuda_0 moved from ({start_x}, {start_y}) to ({f1.grid_x:.2f}, {f1.grid_y:.2f})")
        
        # 1. Verify Movement
        self.assertNotEqual(f1.grid_x, start_x, "Barracuda_0 should have moved.")
        
        # 2. Verify Direction (Moved towards Frigate at 90, 90)
        self.assertGreater(f1.grid_x, start_x, "Barracuda_0 should have moved towards positive X.")
        self.assertGreater(f1.grid_y, start_y, "Barracuda_0 should have moved towards positive Y.")
        
        # 3. Verify Cohesion (Units should still be relatively close)
        dist_12 = ((f1.grid_x - f2.grid_x)**2 + (f1.grid_y - f2.grid_y)**2)**0.5
        print(f"[TEST] Distance between B0 and B1 after 2s: {dist_12:.2f}")
        self.assertLess(dist_12, 5.0, "Barracuda_0 and Barracuda_1 should stay in squadron cohesion.")

if __name__ == '__main__':
    unittest.main()
