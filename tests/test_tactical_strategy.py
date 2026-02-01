import pytest
import sys
import os

# Mock Unit for testing
class MockShip:
    def __init__(self, name, x, y, facing, agility=45, armor=100, grid_size=None):
        self.name = name
        self.grid_x = x
        self.grid_y = y
        self.facing = facing
        self.agility = agility
        self.grid_size = grid_size or [1, 1]
        self.armor = armor
        self.armor_front = armor
        self.armor_side = int(armor * 0.75)
        self.armor_rear = int(armor * 0.5)

@pytest.fixture
def grid():
    from src.combat.tactical_grid import TacticalGrid
    return TacticalGrid(100, 100)

class TestTacticalStrategy:
    def test_rotation(self, grid):
        ship = MockShip("Cruiser", 50, 50, facing=0, agility=45)
        
        # Test 1: Small turn (within agility)
        # Target East (90). Current 0. Diff 90. Agility 45. Should turn 45.
        turned = grid.rotate_unit(ship, 90)
        assert turned == 45
        assert ship.facing == 45
        
        # Test 2: Next turn to complete
        turned = grid.rotate_unit(ship, 90)
        assert turned == 45
        assert ship.facing == 90
        
        # Test 3: Wrap around (North 0 to West 270/-90)
        ship.facing = 0
        # Target 270 (West). Diff is 270 (or -90). Shortest path is -90.
        # Agility 45. Should turn -45 (to 315).
        turned = grid.rotate_unit(ship, 270)
        assert turned == -45
        assert ship.facing == 315 # 360 - 45

    def test_bearing_calculation(self, grid):
        attacker = MockShip("Attacker", 50, 50, facing=0) # Facing North
        
        # Target directly East (51, 50)
        target = MockShip("Target", 51, 50, 0)
        # Grid: Y is down. 0=North.
        # Vector to target is (1, 0).
        # atan2(0, 1) = 0 rad = 0 deg.
        # Mapped: (0 + 90) % 360 = 90 (East). Correct.
        # Relative to facing 0: 90.
        bearing = grid.get_relative_bearing(attacker, target)
        assert bearing == 90
        
        # Target South (50, 51)
        target.grid_x = 50
        target.grid_y = 51
        # Vector (0, 1). atan2(1, 0) = 1.57 = 90 deg.
        # Mapped: 90+90 = 180.
        bearing = grid.get_relative_bearing(attacker, target)
        assert bearing == 180

    def test_weapon_arcs(self, grid):
        attacker = MockShip("Attacker", 50, 50, facing=0)
        target_front = MockShip("Front", 50, 40, 0) # North of attacker (Y=40 < 50)
        target_side = MockShip("Side", 60, 50, 0)   # East of attacker
        target_rear = MockShip("Rear", 50, 60, 0)   # South of attacker
        
        # Prow Arc (315-45)
        # Bearing to Front (North) should be 0 (or 360). 0 is in 315-45.
        assert grid.check_weapon_arc(attacker, target_front, "Prow")
        # Bearing to Side (East) is 90. 90 not in 315-45.
        assert not grid.check_weapon_arc(attacker, target_side, "Prow")
        
        # Broadside Arc (45-135 or 225-315)
        assert grid.check_weapon_arc(attacker, target_side, "Broadside")
        assert not grid.check_weapon_arc(attacker, target_front, "Broadside")

    def test_armor_facing(self, grid):
        attacker = MockShip("Attacker", 50, 60, facing=0) # South of defender
        defender = MockShip("Defender", 50, 50, facing=0) # Facing North
        
        # Attacker is at (50, 60). Defender at (50, 50).
        # Defender sees Attacker at 180 degrees (South).
        # 180 is in Rear Arc (135-225).
        # Should hit Rear Armor.
        
        armor = grid.get_armor_facing(attacker, defender)
        assert armor == defender.armor_rear

    def test_multitile_move(self, grid):
        # 2x1 Ship (Width 2, Height 1)
        # Occupies (10,10) and (11,10)
        ship = MockShip("Battleship", 10, 10, 0, grid_size=[2, 1])
        grid.place_unit(ship, 10, 10)
        
        assert grid.is_occupied(10, 10)
        assert grid.is_occupied(11, 10)
        
        # Move South to (10, 11)
        # New footprint: (10, 11), (11, 11)
        success = grid.move_unit(ship, 10, 11)
        assert success
        
        # Old tiles clear?
        assert not grid.is_occupied(10, 10)
        assert not grid.is_occupied(11, 10)
        
        # New tiles occupied?
        assert grid.is_occupied(10, 11)
        assert grid.is_occupied(11, 11)
