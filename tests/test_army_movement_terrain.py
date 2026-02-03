import pytest
from unittest.mock import MagicMock
from src.models.army import ArmyGroup
from src.services.pathfinding_service import PathfindingService

class MockNode:
    def __init__(self, node_id, terrain="Plains"):
        self.id = node_id
        self.terrain_type = terrain
        self.edges = []
        self.armies = []
        self.position = (0, 0)
        
    def is_traversable(self):
        return True

class MockEdge:
    def __init__(self, target, distance=1.0):
        self.target = target
        self.distance = distance
        self.blocked = False
    def is_traversable(self):
        return True

def test_army_terrain_costs():
    # Setup
    n1 = MockNode("Start")
    n2 = MockNode("Mountain", terrain="Mountain")
    n3 = MockNode("Plains", terrain="Plains")
    
    n1.edges = [MockEdge(n2), MockEdge(n3)]
    n2.edges = [MockEdge(n1)]
    n3.edges = [MockEdge(n1)]
    
    engine = MagicMock()
    engine.pathfinder = PathfindingService()
    
    army = ArmyGroup("TestArmy", "Empire", [], n1)
    army.movement_points = 5.0
    army.current_mp = 5.0
    
    # 1. Test Mountain Cost (2.0)
    army.move_to(n2, engine=engine)
    assert army.location == n2
    assert army.current_mp == 3.0 # 5.0 - 2.0
    
    # Reset
    army.location = n1
    army.current_mp = 1.0
    
    # 2. Test Mountain Blocked by MP
    army.move_to(n2, engine=engine)
    assert army.location == n1 # Not enough MP
    assert army.current_mp == 1.0
    
    # 3. Test multi-turn behavior
    army.destination = n2
    army.state = "MOVING"
    army.current_mp = 1.0 # Still can't move
    army.update_movement(engine)
    assert army.location == n1
    
    army.reset_turn() # current_mp = 5.0
    army.update_movement(engine)
    assert army.location == n2
    assert army.state == "IDLE"

def test_army_water_impassable():
    n1 = MockNode("Start")
    n2 = MockNode("Water", terrain="Water")
    n1.edges = [MockEdge(n2)]
    
    engine = MagicMock()
    engine.pathfinder = PathfindingService()
    
    army = ArmyGroup("TestArmy", "Empire", [], n1)
    army.move_to(n2, engine=engine)
    
    assert army.location == n1 # Should be blocked
    assert army.state == "IDLE" # Pathfinding returns None

def test_pathfinding_context():
    n1 = MockNode("Start")
    n2 = MockNode("Mountain", terrain="Mountain")
    n1.edges = [MockEdge(n2)]
    
    pf = PathfindingService()
    
    # Space context (should ignore terrain_type in neighbor)
    path, cost, _ = pf.find_path(n1, n2, is_ground=False)
    assert cost == 1.0
    
    # Ground context
    path, cost, _ = pf.find_path(n1, n2, is_ground=True)
    assert cost == 2.0
