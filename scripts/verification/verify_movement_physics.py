
import math
from unittest.mock import MagicMock
from src.combat.tactical.movement_calculator import MovementCalculator

def test_movement_physics():
    print("Testing Movement Physics...")
    
    # Mock Grid
    grid = MagicMock()
    # Simple distance mock
    grid.get_distance.side_effect = lambda a, b: math.sqrt((a.grid_x - b.grid_x)**2 + (a.grid_y - b.grid_y)**2)
    
    # --- Space Unit Test ---
    print("\n[SPACE] Testing Inertial Movement")
    space_unit = MagicMock()
    space_unit.name = "SpaceShip"
    space_unit.domain = "space"
    space_unit.grid_x = 0.0
    space_unit.grid_y = 0.0
    
    # Movement Component
    mc = MagicMock()
    mc.base_movement_points = 10.0 # Max Speed
    mc.turn_rate = 10.0 # 10 degrees per sec
    mc.acceleration = 1.0 # 1 unit/sec^2
    mc.facing = 0.0 # East (0 degrees)
    mc.current_speed = 0.0
    space_unit.movement_comp = mc
    
    target = MagicMock()
    target.grid_x = 0.0
    target.grid_y = 100.0 # North (90 degrees relative to 0,0)
    
    dt = 1.0
    
    # Test 1: Turning
    # Facing 0 -> Target is at (0, 100). Angle should be 90 degrees.
    # Diff = 90. Turn rate = 10 * dt = 10.
    # New facing should be 0 + 10 = 10.
    
    MovementCalculator.calculate_movement_vector(space_unit, target, "CHARGE", grid, dt)
    
    print(f"Tick 1: Facing {mc.facing}, Speed {mc.current_speed}")
    
    # Facing check
    # Note: calculate_movement_vector modifies mc.facing in place
    if abs(mc.facing - 10.0) < 0.01:
        print("SUCCESS: Turning correctly (0 -> 10).")
    else:
        print(f"FAIL: Expected facing 10.0, got {mc.facing}")
        
    # Speed check
    # Target Angle 90. Current Facing 0 (before update) -> 10 (after update).
    # Diff was 90.
    # Logic: if abs(diff) > 45: throttle = 0.5. If > 90: throttle = 0.1.
    # Diff 90. So throttle 0.5?
    # Max speed 10. Desired 5.
    # Current 0. Accel 1 * dt = 1.
    # New speed = min(5, 0 + 1) = 1.0.
    
    if abs(mc.current_speed - 1.0) < 0.01:
         print("SUCCESS: Accelerating correctly (0 -> 1.0).")
    else:
         print(f"FAIL: Expected speed 1.0, got {mc.current_speed}")

    # --- Ground Unit Test ---
    print("\n[GROUND] Testing Grid Movement")
    ground_unit = MagicMock()
    ground_unit.name = "Tank"
    ground_unit.domain = "ground"
    ground_unit.grid_x = 0.0
    ground_unit.grid_y = 0.0
    ground_unit.weapon_range_default = 10 # Short range
    ground_unit.components = [] # No weapons
    # Mocking MagicMock behavior for getattr(..., 'movement_comp') on ground unit
    # If we don't set it, default magicmock is truthy.
    # But MovementCalculator checks `if domain == "space" and ...`
    # We set domain="ground". So it should go to else.

    # Target far away to ensure movement
    target_ground = MagicMock()
    target_ground.grid_x = 100.0
    target_ground.grid_y = 0.0
    
    dx, dy = MovementCalculator.calculate_movement_vector(ground_unit, target_ground, "CHARGE", grid, dt)
    
    print(f"Ground Vector: ({dx}, {dy})")
    
    # Should move towards target (x+ direction) -> step_x=1
    if dx == 1 and dy == 0:
        print("SUCCESS: Ground unit moving directly to target.")
    else:
        print(f"FAIL: Expected (1, 0), got ({dx}, {dy})")

if __name__ == "__main__":
    test_movement_physics()
