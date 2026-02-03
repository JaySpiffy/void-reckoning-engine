import pytest
from unittest.mock import MagicMock
from src.models.army import ArmyGroup
from src.ai.strategies.standard import StandardStrategy

class MockNode:
    def __init__(self, node_id, node_type="Plains"):
        self.id = node_id
        self.type = node_type
        self.terrain_type = "Plains"
        self.edges = []
        self.armies = []
        self.position = (0, 0)

class MockPlanet:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner
        self.provinces = []
        self.armies = []

def test_ai_embarkation_movement():
    # Setup
    n_army = MockNode("N_Army", node_type="Plains")
    n_port = MockNode("N_Spaceport", node_type="Spaceport")
    
    planet = MockPlanet("Terra", "Empire")
    planet.provinces = [n_army, n_port]
    
    army = ArmyGroup("Army1", "Empire", [], n_army)
    planet.armies = [army]
    n_army.armies = [army]
    
    fleet = MagicMock()
    fleet.id = "Fleet1"
    fleet.faction = "Empire"
    fleet.location = planet
    fleet.used_capacity = 0
    fleet.transport_capacity = 10
    fleet.is_destroyed = False
    
    engine = MagicMock()
    engine.fleets = [fleet]
    engine.planets_by_faction = {"Empire": [planet]}
    engine.intel_manager.calculate_distance.return_value = 5.0
    
    # Pathfinding mock
    engine.pathfinder = MagicMock()
    engine.pathfinder.find_path.return_value = ([n_army, n_port], 5.0, {})
    
    strategy = StandardStrategy()
    
    # Run reinforcement logic
    strategy.process_reinforcements("Empire", engine)
    
    # Assert
    assert army.location == n_port
    assert army.state == "IDLE"

def test_ai_search_and_destroy():
    # Setup
    n_friendly = MockNode("N_Friendly")
    n_enemy = MockNode("N_Enemy")
    
    planet = MockPlanet("HostileWorld", "Empire")
    planet.provinces = [n_friendly, n_enemy]
    
    army_f = ArmyGroup("FriendlyArmy", "Empire", [], n_friendly)
    army_e = ArmyGroup("EnemyArmy", "Chaos", [], n_enemy)
    
    planet.armies = [army_f, army_e]
    n_friendly.armies = [army_f]
    n_enemy.armies = [army_e]
    
    engine = MagicMock()
    engine.fleets = []
    engine.planets_by_faction = {"Empire": [planet]}
    engine.intel_manager.calculate_distance.return_value = 1.0
    
    # Pathfinding mock
    engine.pathfinder = MagicMock()
    engine.pathfinder.find_path.return_value = ([n_friendly, n_enemy], 1.0, {})
    
    strategy = StandardStrategy()
    
    # Run logic
    strategy.process_reinforcements("Empire", engine)
    
    # Assert
    assert army_f.location == n_enemy
    assert army_f.state == "IDLE"
