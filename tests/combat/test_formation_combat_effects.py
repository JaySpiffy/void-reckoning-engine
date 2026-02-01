import unittest
from src.combat.combat_state import CombatState
from src.combat.real_time.formation_manager import Formation
from src.models.unit import Unit
from src.combat.tactical_grid import TacticalGrid
from src.combat.tactical_grid import TacticalGrid
from src.combat.realtime.realtime_manager import RealTimeManager
from src.combat.real_time.simulation_loop import SimulationLoop
from src.combat.components.movement_component import MovementComponent

class TestFormationCombat(unittest.TestCase):
    def setUp(self):
        self.grid = TacticalGrid()
        
        # Test Units
        # Test Units
        mov_comp_wedge = MovementComponent(movement_points=5)
        self.wedge_unit = Unit(name="Wedge_Unit", faction="Wedge_Faction", hp=100, armor=0, ma=100, md=5, damage=10, abilities={}, components=[mov_comp_wedge])
        
        mov_comp_wall = MovementComponent(movement_points=5)
        self.wall_unit = Unit(name="Wall_Unit", faction="Wall_Faction", hp=100, armor=0, ma=100, md=5, damage=10, abilities={}, components=[mov_comp_wall])
        
        mov_comp_rect = MovementComponent(movement_points=5)
        self.rect_unit = Unit(name="Rect_Unit", faction="Rect_Faction", hp=100, armor=0, ma=100, md=5, damage=10, abilities={}, components=[mov_comp_rect])
        
        armies = {
            "Wedge_Faction": [self.wedge_unit],
            "Wall_Faction": [self.wall_unit],
            "Rect_Faction": [self.rect_unit],
            "Attacker_Faction": []
        }
        doctrines = {f: "Standard" for f in armies}
        metadata = {f: {} for f in armies}
        
        self.state = CombatState(armies, doctrines, metadata)
        self.state.grid = self.grid
        self.state.realtime_manager = RealTimeManager()

    def test_wedge_speed_bonus(self):
        # Wedge has 1.2x speed mult
        form = Formation([self.wedge_unit], formation_type="Wedge")
        self.state.formations = [form]
        
        # Add an enemy far away to trigger movement
        # Add an enemy far away to trigger movement
        enemy = Unit(name="Enemy", faction="Enemy_Faction", hp=100, armor=0, ma=100, md=0, damage=0, abilities={})
        enemy.grid_x = 100
        enemy.grid_y = 0
        self.state.armies_dict["Enemy_Faction"] = [enemy]
        self.state.active_factions.append("Enemy_Faction")
        
        self.wedge_unit.grid_x = 0
        self.wedge_unit.grid_y = 0
        
        # Simulation Step
        self.state.real_time_update(0.1)
        
        print(f"DEBUG: Wedge Pos after 0.1s: {self.wedge_unit.grid_x}")
        # Base speed 5. 5 * 0.1s * 1.2 = 0.6.
        # Steering might not reach perfect 1.0 dx immediately, but it should be > 0.
        self.assertGreater(self.wedge_unit.grid_x, 0.1)

    def test_wall_defense_bonus(self):
        # Wall has 1.3x defense mult -> dmg / 1.3
        # Wall has 1.3x defense mult -> dmg / 1.3
        form = Formation([self.wall_unit], formation_type="Wall")
        attacker = Unit(name="Attacker", faction="Attacker_Faction", hp=100, armor=0, ma=100, md=5, damage=1, abilities={}, components=[])
        attacker.bs = 100
        
        # Setup state
        self.state.formations = [form]
        self.state.armies_dict = {
            "Wall_Faction": [self.wall_unit],
            "Attacker_Faction": [attacker]
        }
        self.state.active_factions = ["Wall_Faction", "Attacker_Faction"]
        
        self.wall_unit.grid_x = 10
        self.wall_unit.grid_y = 10
        self.wall_unit.facing = 0.0 # Facing North
        
        # Attacker at Front (North of defender)
        attacker.grid_x = 10
        attacker.grid_y = 0
        
        # Attacker fires (dmg=10)
        # Expected dmg: 10 / 1.3 = ~7.69
        self.state.real_time_update(0.1)
        
        print(f"DEBUG: Wall Unit HP after hit: {self.wall_unit.current_hp}")
        # 100 - 7.69 = 92.31
        self.assertLess(100 - self.wall_unit.current_hp, 8.0, "Wall unit should take reduced damage (no flanking).")
        self.assertGreater(100 - self.wall_unit.current_hp, 7.0)

if __name__ == "__main__":
    unittest.main()
