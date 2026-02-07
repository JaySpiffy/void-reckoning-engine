
import pytest
from unittest.mock import MagicMock
import math
from src.combat.tactical.movement_calculator import MovementCalculator

def test_space_inertial_movement():
    """Verify that space units use inertial physics (turn rate, acceleration)."""
    # Setup
    grid = MagicMock()
    grid.get_distance.side_effect = lambda a, b: math.sqrt((a.grid_x - b.grid_x)**2 + (a.grid_y - b.grid_y)**2)
    
    unit = MagicMock()
    unit.domain = "space"
    unit.grid_x, unit.grid_y = 0.0, 0.0
    
    mc = MagicMock()
    mc.base_movement_points = 10.0
    mc.turn_rate = 10.0
    mc.acceleration = 1.0
    mc.facing = 0.0
    mc.current_speed = 0.0
    unit.movement_comp = mc
    
    target = MagicMock()
    target.grid_x, target.grid_y = 0.0, 100.0 # 90 degrees relative
    
    dt = 1.0
    
    # Execute
    MovementCalculator.calculate_movement_vector(unit, target, "CHARGE", grid, dt)
    
    # Assert Turning (0 -> 10)
    assert abs(mc.facing - 10.0) < 0.01, f"Expected 10.0 facing, got {mc.facing}"
    
    # Assert Acceleration (0 -> 1)
    assert abs(mc.current_speed - 1.0) < 0.01, f"Expected 1.0 speed, got {mc.current_speed}"

def test_ground_grid_movement():
    """Verify that ground units use snappy grid movement."""
    # Setup
    grid = MagicMock()
    grid.get_distance.side_effect = lambda a, b: math.sqrt((a.grid_x - b.grid_x)**2 + (a.grid_y - b.grid_y)**2)
    
    unit = MagicMock()
    unit.domain = "ground"
    unit.grid_x, unit.grid_y = 0.0, 0.0
    unit.weapon_range_default = 10
    unit.components = []
    
    target = MagicMock()
    target.grid_x, target.grid_y = 100.0, 0.0
    
    dt = 1.0
    
    # Execute
    dx, dy = MovementCalculator.calculate_movement_vector(unit, target, "CHARGE", grid, dt)
    
    # Assert snappy movement (step vector)
    assert dx == 1 and dy == 0, f"Expected (1, 0), got ({dx}, {dy})"
