import unittest
import math
from src.combat.combat_state import CombatState
from src.combat.real_time.simulation_loop import SimulationLoop
from src.combat.real_time.formation_manager import Formation

class MockSoldier:
    def __init__(self, name, faction, x, y):
        self.name = name
        self.faction = faction
        self.grid_x = x
        self.grid_y = y
        self.facing = 0
        self.movement_points = 5
        self.is_destroyed = False
        self.current_hp = 100
        self.base_hp = 100
        self.max_hp = 100
        self.abilities = {"Tags": []}
        self.damage = 10
        self.weapon_range_default = 100
        self.formations = []
        self.morale_max = 1000
        self.morale_current = 1000
        self.morale_state = "Steady"
        self.recent_damage_taken = 0.0
        self.time_since_last_damage = 0.0
        self.current_suppression = 0
        self.is_pinned = False
        
    def is_alive(self):
        return not self.is_destroyed and self.current_hp > 0
    
    def take_damage(self, amount, target_component=None):
        self.current_hp -= amount
        if self.current_hp < 0: self.current_hp = 0

class TestGroundFormations(unittest.TestCase):
    def setUp(self):
        # Iron Vanguard Conscripts (Formation) vs Solar Hegemony Cadre (Attacker)
        self.ivan_army = [MockSoldier(f"Vanguard_{i}", "Iron_Vanguard", 50.0 + i, 50.0) for i in range(20)]
        self.target_formation = Formation(self.ivan_army, columns=5, spacing=1.0)
        self.target_formation.facing = 0.0 # Facing East (Pos X)
        
        # Solar Hegemony attacking from the REAR (West)
        self.solar_heg = [MockSoldier("Cadre_1", "Solar_Hegemony", 0.0, 50.0)]
        
        self.armies_dict = {
            "Iron_Vanguard": self.ivan_army,
            "Solar_Hegemony": self.solar_heg
        }
        
        self.state = CombatState(self.armies_dict, {}, {})
        self.state.formations = [self.target_formation]
        # Mock grid
        from src.combat.tactical_grid import TacticalGrid
        self.state.grid = TacticalGrid(100, 100)
        for u in self.ivan_army + self.solar_heg:
            self.state.grid.update_unit_position(u, u.grid_x, u.grid_y)

    def test_flanking_damage(self):
        # Reset for a clean 1v1 flanking test to avoid Boids drift
        self.ivan_army = [MockSoldier("Vanguard_Target", "Iron_Vanguard", 50.0, 50.0)]
        self.ivan_army[0].morale_max = 1000
        self.ivan_army[0].morale_current = 1000
        
        self.target_formation = Formation(self.ivan_army, columns=1, spacing=1.0)
        self.target_formation.facing = 90.0 # Facing East in Compass Grid
        
        self.solar_heg = [MockSoldier("Cadre_Attacker", "Solar_Hegemony", 0.0, 50.0)]
        self.armies_dict = {"Iron_Vanguard": self.ivan_army, "Solar_Hegemony": self.solar_heg}
        self.state.armies_dict = self.armies_dict
        self.state.formations = [self.target_formation]
        self.state.grid.update_unit_position(self.ivan_army[0], 50.0, 50.0)
        self.state.grid.update_unit_position(self.solar_heg[0], 0.0, 50.0)

        loop = SimulationLoop(tick_rate=20)
        loop.on_update = self.state.real_time_update
        
        soldier_0_hp = self.ivan_army[0].current_hp
        
        print("\n[TEST] Commencing Ground Formation Rear-Attack Test...")
        # Run for 2 ticks to trigger one shot (1.0s cooldown)
        loop.start(duration_seconds=0.1) # First tick fires
        
        # Solar Heg damage is 10. Rear multiplier should be 2.0x -> 20 damage.
        actual_dmg = soldier_0_hp - self.ivan_army[0].current_hp
        print(f"[TEST] Damage received by soldier from Rear: {actual_dmg}")
        
        self.assertEqual(actual_dmg, 20, "Rear attack should apply 2.0x damage multiplier.")

    def test_formation_cohesion(self):
        loop = SimulationLoop(tick_rate=20)
        loop.on_update = self.state.real_time_update
        
        # Move the formation center
        # We manually shift grid_x of soldiers to simulate drift, then run loop
        for e in self.ivan_army:
            e.grid_x += 5.0 
            
        print("\n[TEST] Commencing Formation Cohesion Test...")
        loop.start(duration_seconds=1.0)
        
        # Verify units are close to their slot positions
        slots = self.target_formation.get_target_positions()
        for i, u in enumerate(self.ivan_army):
            sx, sy = slots[i]
            dist = math.sqrt((u.grid_x - sx)**2 + (u.grid_y - sy)**2)
            self.assertLess(dist, 5.0, f"Unit {u.name} should stay close to its formation slot. Dist: {dist:.2f}")

if __name__ == '__main__':
    unittest.main()
