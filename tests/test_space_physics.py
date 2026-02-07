
import pytest
import math
from src.combat.components.movement_component import MovementComponent
from src.factories.unit_factory import UnitFactory
from src.combat.tactical.movement_calculator import MovementCalculator
from src.models.unit import Ship, Regiment

class MockGrid:
    def get_distance(self, u1, u2):
        return math.sqrt((u1.grid_x - u2.grid_x)**2 + (u1.grid_y - u2.grid_y)**2)

@pytest.fixture
def mock_grid():
    return MockGrid()

def test_unit_factory_physics_defaults():
    # Test Fighter Defaults (Fast turn, high accel)
    fighter_bp = type('Blueprint', (), {
        'name': 'Test Fighter',
        'type': 'Fighter',
        'movement_points': 20,
        'base_stats': {},
        'cost': 100
    })
    fighter = UnitFactory.create_from_blueprint(fighter_bp, "Imperium")
    assert fighter.movement_comp.turn_rate == 90.0
    assert fighter.movement_comp.acceleration == 5.0

    # Test Capital Defaults (Slow turn, low accel)
    capital_bp = type('Blueprint', (), {
        'name': 'Test Battleship',
        'type': 'Battleship',
        'movement_points': 6,
        'base_stats': {},
        'cost': 1000
    })
    battleship = UnitFactory.create_from_blueprint(capital_bp, "Imperium")
    assert battleship.movement_comp.turn_rate == 5.0
    assert battleship.movement_comp.acceleration == 0.1

    # Test Explicit Overrides
    custom_bp = type('Blueprint', (), {
        'name': 'Custom Corvette',
        'type': 'Corvette',
        'movement_points': 12,
        'turn_rate': 60.0,
        'acceleration': 3.0,
        'base_stats': {},
        'cost': 200
    })
    corvette = UnitFactory.create_from_blueprint(custom_bp, "Rebels")
    assert corvette.movement_comp.turn_rate == 60.0
    assert corvette.movement_comp.acceleration == 3.0

def test_inertial_movement_turn_rate(mock_grid):
    # Setup Ship facing East (0)
    ship = Ship("Test Frigate", "Imperium")
    ship.movement_comp = MovementComponent(movement_points=10, turn_rate=10.0, acceleration=1.0)
    ship.movement_comp.facing = 0.0
    ship.grid_x, ship.grid_y = 0, 0
    ship.domain = "space"

    # Target straight North (90 degrees)
    target = Ship("Target", "Rebels")
    target.grid_x, target.grid_y = 0, 100 
    
    # Tick 1: Should turn max 10 degrees
    dt = 1.0
    MovementCalculator.calculate_movement_vector(ship, target, "CHARGE", mock_grid, dt)
    assert ship.movement_comp.facing == 10.0
    
    # Tick 2: Should turn another 10 degrees
    MovementCalculator.calculate_movement_vector(ship, target, "CHARGE", mock_grid, dt)
    assert ship.movement_comp.facing == 20.0

def test_inertial_movement_acceleration(mock_grid):
    ship = Ship("Test Frigate", "Imperium")
    ship.movement_comp = MovementComponent(movement_points=10, turn_rate=100.0, acceleration=2.0)
    ship.movement_comp.facing = 0.0
    ship.movement_comp.current_speed = 0.0
    ship.grid_x, ship.grid_y = 0, 0
    ship.domain = "space"

    # Target East (No turn needed)
    target = Ship("Target", "Rebels")
    target.grid_x, target.grid_y = 100, 0
    
    dt = 1.0
    
    # Tick 1: Speed 0 -> 2
    MovementCalculator.calculate_movement_vector(ship, target, "CHARGE", mock_grid, dt)
    assert ship.movement_comp.current_speed == 2.0
    
    # Tick 2: Speed 2 -> 4
    MovementCalculator.calculate_movement_vector(ship, target, "CHARGE", mock_grid, dt)
    assert ship.movement_comp.current_speed == 4.0

def test_ground_movement_instant_turn(mock_grid):
    # Ground units should NOT use inertia
    tank = Regiment("Test Tank", "Imperium")
    # Even if they have physics stats (e.g. from a weird factory call), domain='ground' forces instant logic
    tank.movement_comp = MovementComponent(movement_points=10, turn_rate=5.0, acceleration=1.0)
    tank.grid_x, tank.grid_y = 0, 0
    tank.domain = "ground"
    
    target = Regiment("Target", "Rebels")
    target.grid_x, target.grid_y = 0, 100 # Far away to force movement
    
    # Calculate Movement
    dx, dy = MovementCalculator.calculate_movement_vector(tank, target, "CHARGE", mock_grid)
    
    # Should move instantly towards 0,10 (dx=0, dy=1)
    # Ground logic returns step_x, step_y (integers mostly)
    assert dx == 0
    assert dy == 1
    
    # Physics stats shouldn't change
    assert tank.movement_comp.facing == 0.0 # Default
    assert tank.movement_comp.current_speed == 0.0 # Default
