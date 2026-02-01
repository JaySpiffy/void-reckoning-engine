import pytest
import sys
import os

# Add src to path if used directly (though run_command usually sets pythonpath or pytest handles it)
from src.combat.tactical_grid import TacticalGrid
from src.models.unit import Ship

class MockUnit:
    def __init__(self, name):
        self.name = name
        self.grid_x = 0
        self.grid_y = 0
        self.is_deployed = False

class TestTacticalGrid:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.grid = TacticalGrid(10, 10) # Small grid for testing

    def test_placement(self):
        u = MockUnit("Ship A")
        res = self.grid.place_unit(u, 5, 5)
        assert res
        assert u.grid_x == 5
        assert self.grid.is_occupied(5, 5)

    def test_collision(self):
        u1 = MockUnit("Ship A")
        u2 = MockUnit("Ship B")
        self.grid.place_unit(u1, 2, 2)
        res = self.grid.place_unit(u2, 2, 2) # Same spot
        assert not res

    def test_movement(self):
        u = MockUnit("Speedster")
        self.grid.place_unit(u, 0, 0)
        
        # Valid Move
        res = self.grid.move_unit(u, 1, 1)
        assert res
        assert u.grid_x == 1
        assert not self.grid.is_occupied(0, 0)
        assert self.grid.is_occupied(1, 1)
        
        # OOB Move
        res = self.grid.move_unit(u, 11, 11)
        assert not res
        assert u.grid_x == 1 # Still at 1,1

    def test_distance(self):
        u1 = MockUnit("A")
        u2 = MockUnit("B")
        self.grid.place_unit(u1, 0, 0)
        self.grid.place_unit(u2, 3, 4)
        
        # Euclidean: sqrt(3^2 + 4^2) = 5.0
        dist = self.grid.get_distance(u1, u2)
        assert dist == 5.0
