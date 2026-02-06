import pytest
import math
from src.combat.combat_state import CombatState
from src.combat.real_time.simulation_loop import SimulationLoop
from src.combat.real_time.formation_manager import Formation
from src.combat.tactical_grid import TacticalGrid

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

@pytest.fixture
def ground_combat_setup():
    ivan_army = [MockSoldier(f"Vanguard_{i}", "Iron_Vanguard", 50.0 + i, 50.0) for i in range(20)]
    target_formation = Formation(ivan_army, columns=5, spacing=1.0)
    target_formation.facing = 0.0 # Facing East (Pos X)
    
    solar_heg = [MockSoldier("Cadre_1", "Solar_Hegemony", 0.0, 50.0)]
    
    armies_dict = {
        "Iron_Vanguard": ivan_army,
        "Solar_Hegemony": solar_heg
    }
    
    state = CombatState(armies_dict, {}, {})
    state.grid = TacticalGrid(100, 100)
    state.formations = [target_formation]
    
    # Initialize positions in grid
    for u in ivan_army + solar_heg:
        state.grid.update_unit_position(u, u.grid_x, u.grid_y)
        
    return {
        "state": state,
        "ivan_army": ivan_army,
        "solar_heg": solar_heg,
        "target_formation": target_formation
    }

def test_flanking_damage(ground_combat_setup):
    state = ground_combat_setup["state"]
    # Reset for a clean 1v1 flanking test
    ivan_unit = MockSoldier("Vanguard_Target", "Iron_Vanguard", 50.0, 50.0)
    ivan_unit.morale_max = 1000
    ivan_unit.morale_current = 1000
    
    target_formation = Formation([ivan_unit], columns=1, spacing=1.0)
    target_formation.facing = 90.0 # Facing East in Compass Grid
    
    solar_unit = MockSoldier("Cadre_Attacker", "Solar_Hegemony", 0.0, 50.0)
    
    state.armies_dict = {"Iron_Vanguard": [ivan_unit], "Solar_Hegemony": [solar_unit]}
    state.formations = [target_formation]
    state.grid.update_unit_position(ivan_unit, 50.0, 50.0)
    state.grid.update_unit_position(solar_unit, 0.0, 50.0)

    loop = SimulationLoop(tick_rate=20)
    loop.on_update = state.real_time_update
    
    initial_hp = ivan_unit.current_hp
    loop.start(duration_seconds=0.1)
    
    actual_dmg = initial_hp - ivan_unit.current_hp
    # Solar Heg damage is 10. Rear multiplier should be 2.0x -> 20 damage.
    assert actual_dmg == 20, "Rear attack should apply 2.0x damage multiplier."

def test_formation_cohesion(ground_combat_setup):
    state = ground_combat_setup["state"]
    ivan_army = ground_combat_setup["ivan_army"]
    target_formation = ground_combat_setup["target_formation"]
    
    loop = SimulationLoop(tick_rate=20)
    loop.on_update = state.real_time_update
    
    # Manually shift grid_x of soldiers to simulate drift
    for e in ivan_army:
        e.grid_x += 5.0 
            
    loop.start(duration_seconds=1.0)
    
    # Verify units are close to their slot positions
    slots = target_formation.get_target_positions()
    for i, u in enumerate(ivan_army):
        sx, sy = slots[i]
        dist = math.sqrt((u.grid_x - sx)**2 + (u.grid_y - sy)**2)
        assert dist < 5.0, f"Unit {u.name} should stay close to its formation slot."
