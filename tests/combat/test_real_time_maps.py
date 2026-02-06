import pytest
import math
from src.combat.combat_state import CombatState
from src.combat.tactical_grid import TacticalGrid
from src.models.unit import Unit
from src.combat.real_time.map_manager import EnvironmentalArea, StaticObstacle, TacticalObjective

@pytest.fixture
def map_setup():
    grid = TacticalGrid(100, 100)
    # TacticalGrid init already calls generate_terrain which adds random 'Heavy'/'Light'.
    # We'll clear them for controlled tests.
    grid.terrain_map = {}
    
    u1 = Unit("Unit_1", 100, 0, 100, 5, 10, {}, faction="Faction_A")
    u2 = Unit("Unit_2", 100, 0, 100, 5, 10, {}, faction="Faction_B")
    
    # Prevent routing, death, and shooting during tests
    for u in [u1, u2]:
        u.morale_max = 1000
        u.morale_current = 1000
        u.current_hp = 10000.0 # Invincible enough for measurement
        u._shooting_cooldown = 9999.0 # Prevent shooting
        u.weapon_range_default = 0
        u.movement_points = 5
    
    armies = {"Faction_A": [u1], "Faction_B": [u2]}
    doctrines = {"Faction_A": "Standard", "Faction_B": "Standard"}
    metadata = {"Faction_A": {}, "Faction_B": {}}
    
    state = CombatState(armies, doctrines, metadata)
    state.grid = grid
    state.active_factions = ["Faction_A", "Faction_B"]
    
    return {
        "grid": grid,
        "state": state,
        "u1": u1,
        "u2": u2
    }

def test_woods_speed_penalty(map_setup):
    grid = map_setup["grid"]
    state = map_setup["state"]
    u1 = map_setup["u1"]
    
    # Place Woods area
    woods = EnvironmentalArea("Woods", 50, 50, 20, {"speed_mult": 0.5})
    grid.add_map_object(woods)
    
    # Unit inside woods
    u1.grid_x = 50
    u1.grid_y = 50
    
    # Target far away to force movement
    target = Unit("Target", 100, 0, 100, 0, 0, {}, faction="Target_F")
    target.grid_x = 100
    target.grid_y = 50
    state.armies_dict = {"Faction_A": [u1], "Target_F": [target]}
    state.active_factions = ["Faction_A", "Target_F"]
    
    # Tick 1s. Base speed 5. Inside woods -> 2.5 distance?
    state.real_time_update(1.0)
    
    # Should have moved around 2.5
    dist_moved = u1.grid_x - 50
    assert 1.0 < dist_moved < 4.0

def test_objective_capture(map_setup):
    grid = map_setup["grid"]
    state = map_setup["state"]
    u1 = map_setup["u1"]
    
    obj = TacticalObjective("Point Alpha", 20, 20, 5)
    grid.add_map_object(obj)
    
    # Unit 1 on point
    u1.grid_x = 20
    u1.grid_y = 20
    
    state.armies_dict = {"Faction_A": [u1]}
    state.active_factions = ["Faction_A"]
    
    # Tick several times. Progress should increase.
    # update_capture adds 20 * dt. Need 5s for 100.
    for _ in range(30):
        state.real_time_update(0.2)
            
    assert obj.owner == "Faction_A"
    assert state.victory_points["Faction_A"] > 0

def test_obstacle_avoidance(map_setup):
    grid = map_setup["grid"]
    state = map_setup["state"]
    u1 = map_setup["u1"]
    
    # Big obstacle at (50, 50)
    rock = StaticObstacle("Rock", 50, 50, 10)
    grid.add_map_object(rock)
    
    # Unit tries to move through (50, 50)
    u1.grid_x = 35
    u1.grid_y = 50
    
    # Target is at 60, 50 (other side of rock)
    target = Unit("Goal", 100, 0, 100, 0, 0, {}, faction="Goal_F")
    target.grid_x = 60
    target.grid_y = 50
    state.armies_dict = {"Faction_A": [u1], "Goal_F": [target]}
    state.active_factions = ["Faction_A", "Goal_F"]
    
    for _ in range(10):
        state.real_time_update(0.2)
            
    # Should not enter the rock's radius (10) centered at 50, so max x should be 40ish
    assert u1.grid_x < 42
