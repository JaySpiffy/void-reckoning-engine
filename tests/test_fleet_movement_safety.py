from unittest.mock import MagicMock
import pytest
from src.models.fleet import Fleet
from src.core.simulation_topology import GraphNode

def test_fleet_move_to_node_recovery():
    # Setup - Planet with node reference
    planet = MagicMock()
    planet.name = "Terra"
    node = GraphNode("N1", "Planet", "TerraNode")
    planet.node_reference = node
    
    # Create fleet with location but NO current_node
    fleet = Fleet("F1", "Empire", planet)
    fleet.current_node = None # Force it to be None
    
    # Target
    target_planet = MagicMock()
    target_planet.name = "Mars"
    target_node = GraphNode("N2", "Planet", "MarsNode")
    target_planet.node_reference = target_node
    
    # Mock engine find_cached_path
    engine = MagicMock()
    engine.find_cached_path.return_value = ([node, target_node], 1, {"cache_hit": True})
    engine.pathfinder.log_path_failure.return_value = True
    
    # Call move_to
    fleet.move_to(target_planet, engine=engine)
    
    # Verify auto-recovery
    assert fleet.current_node == node
    assert fleet.route == [target_node]
    assert fleet.destination == target_planet

def test_fleet_move_to_safe_logging_on_failure():
    # Setup - Planet without node reference
    # We use a simple object instead of MagicMock to avoid hasattr returning True for everything
    class SimplePlanet:
        def __init__(self, name):
            self.name = name
    
    planet = SimplePlanet("Terra")
    
    # Create fleet with NO current_node and NO way to recover it
    fleet = Fleet("F1", "Empire", planet)
    fleet.current_node = None
    
    # Target
    target_planet = SimplePlanet("Mars")
    target_node = GraphNode("N2", "Planet", "MarsNode")
    target_planet.node_reference = target_node
    
    # Mock engine
    engine = MagicMock()
    engine.logger = MagicMock()
    
    # Call move_to - Should log "cannot recover" and return safely
    fleet.move_to(target_planet, engine=engine)
    
    # Verify error was logged
    assert engine.logger.error.called
    assert fleet.route == []

def test_fleet_move_to_path_failure_robust_logging():
    # Setup
    node1 = GraphNode("N1", "Planet", "Terra")
    node2 = GraphNode("N2", "Planet", "Mars")
    
    planet1 = MagicMock()
    planet1.node_reference = node1
    planet2 = MagicMock()
    planet2.name = "MarsPlanet"
    planet2.node_reference = node2
    
    fleet = Fleet("F1", "Empire", planet1)
    
    # Mock engine pathfinding FAILURE
    engine = MagicMock()
    engine.logger = MagicMock()
    engine.find_cached_path.return_value = (None, float('inf'), {})
    engine.pathfinder.log_path_failure.return_value = True
    
    # Call move_to
    fleet.move_to(planet2, engine=engine)
    
    # Verify the specific error log format (using getattr)
    engine.logger.error.assert_any_call("Fleet F1 cannot find path to MarsPlanet (Disconnected Graph from N1 to N2)")
