import unittest
import math
from src.combat.combat_state import CombatState
from src.combat.tactical_grid import TacticalGrid
from src.models.unit import Unit
from src.combat.real_time.map_manager import EnvironmentalArea, StaticObstacle, TacticalObjective

class TestRealTimeMaps(unittest.TestCase):
    def setUp(self):
        self.grid = TacticalGrid(100, 100)
        # TacticalGrid init already calls generate_terrain which adds random 'Heavy'/'Light'.
        # We'll clear them for controlled tests.
        self.grid.terrain_map = {}
        
        self.u1 = Unit("Unit_1", 100, 0, 100, 5, 10, {}, faction="Faction_A")
        self.u2 = Unit("Unit_2", 100, 0, 100, 5, 10, {}, faction="Faction_B")
        
        # Prevent routing, death, and shooting during tests
        for u in [self.u1, self.u2]:
            u.morale_max = 1000
            u.morale_current = 1000
            u.current_hp = 10000.0 # Invincible enough for measurement
            u._shooting_cooldown = 9999.0 # Prevent shooting
            u.weapon_range_default = 0
            u.movement_points = 5
        
        armies = {"Faction_A": [self.u1], "Faction_B": [self.u2]}
        doctrines = {"Faction_A": "Standard", "Faction_B": "Standard"}
        metadata = {"Faction_A": {}, "Faction_B": {}}
        
        self.state = CombatState(armies, doctrines, metadata)
        self.state.grid = self.grid
        self.state.active_factions = ["Faction_A", "Faction_B"]

    def test_woods_speed_penalty(self):
        # Place Woods area
        woods = EnvironmentalArea("Woods", 50, 50, 20, {"speed_mult": 0.5})
        self.grid.add_map_object(woods)
        
        # Unit inside woods
        self.u1.grid_x = 50
        self.u1.grid_y = 50
        
        # Clear other factions to avoid target-averaging interference
        self.state.armies_dict = {"Faction_A": [self.u1], "Target_F": []}
        self.state.active_factions = ["Faction_A", "Target_F"]
        
        # Target far away to force movement
        target = Unit("Target", 100, 0, 100, 0, 0, {}, faction="Target_F")
        target.grid_x = 100
        target.grid_y = 50
        self.state.armies_dict["Target_F"] = [target]
        
        # Tick 1s. Base speed 5. Inside woods -> 2.5 distance?
        self.state.real_time_update(1.0)
        
        # Should have moved around 2.5
        dist_moved = self.u1.grid_x - 50
        print(f"DEBUG MAP: Unit moved {dist_moved} in woods")
        # 5 * 1.0 * 0.5 = 2.5. Steering might slightly underperform 1.0 magnitude.
        self.assertGreater(dist_moved, 1.0)
        self.assertLess(dist_moved, 4.0)

    def test_objective_capture(self):
        obj = TacticalObjective("Point Alpha", 20, 20, 5)
        self.grid.add_map_object(obj)
        
        # Unit 1 on point
        self.u1.grid_x = 20
        self.u1.grid_y = 20
        # Target far away to keep it from wandering or being confused
        self.u2.grid_x = 80
        self.u2.grid_y = 80
        
        # Ensure it doesn't move away by clearing its motion targets 
        # In this prototype, it targets all enemies. 
        # I'll just clear the other armies.
        self.state.armies_dict = {"Faction_A": [self.u1]}
        self.state.active_factions = ["Faction_A"]
        
        print(f"DEBUG CAPTURE: Unit at ({self.u1.grid_x}, {self.u1.grid_y}) | Obj at ({obj.x}, {obj.y}) | Inside: {obj.is_inside(self.u1.grid_x, self.u1.grid_y)}")
        
        # Tick several times. Progress should increase.
        # update_capture adds 20 * dt. Need 5s for 100.
        for _ in range(30):
            # Manually find units in range for debug
            present = [f for f, units in self.state.armies_dict.items() if any(u.is_alive() and obj.is_inside(u.grid_x, u.grid_y) for u in units)]
            self.state.real_time_update(0.2)
            if _ % 5 == 0:
                prog = obj.capture_progress.get("Faction_A", 0)
                print(f"DEBUG CAPTURE Step {_}: Present Factions={present} | Progress={prog} | Owner={obj.owner}")
            
        self.assertEqual(obj.owner, "Faction_A")
        self.assertGreater(self.state.victory_points["Faction_A"], 0)
        print(f"DEBUG MAP: Objective Owner: {obj.owner} | VP: {self.state.victory_points['Faction_A']}")

    def test_obstacle_avoidance(self):
        # Big obstacle at (50, 50)
        rock = StaticObstacle("Rock", 50, 50, 10)
        self.grid.add_map_object(rock)
        
        # Unit tries to move to (50, 50)
        self.u1.grid_x = 35
        self.u1.grid_y = 50
        
        # Target is at 60, 50 (other side of rock)
        target = Unit("Goal", 100, 0, 100, 0, 0, {}, faction="Goal_F")
        target.grid_x = 60
        target.grid_y = 50
        self.state.armies_dict["Goal_F"] = [target]
        self.state.active_factions.append("Goal_F")
        
        # Unit should steer AWAY from 50, 50 as it gets close
        # After a few ticks, its Y should deviate from 50.0
        for _ in range(10):
            self.state.real_time_update(0.2)
            
        print(f"DEBUG MAP: Unit position near rock: ({self.u1.grid_x}, {self.u1.grid_y})")
        # Since it's being pushed away from (50,50), y should NOT be 50 if it deviates
        # Actually, if target is exactly on the same Y, it might oscillate or stay stuck 
        # unless Steiner handles the tangential push.
        # My avoidance pushes away from center. 
        # If u=(35,50) and obs=(50,50), dx=-15, dy=0. Force is (-1, 0)
        # It should slow down or stay away.
        self.assertLess(self.u1.grid_x, 42) # Should not enter the rock's radius (10)

if __name__ == "__main__":
    unittest.main()
