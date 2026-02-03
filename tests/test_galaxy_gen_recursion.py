import pickle
import sys
import pytest
from unittest.mock import MagicMock
from src.models.star_system import StarSystem
from src.models.planet import Planet
from src.core.universe_data import UniverseDataManager
from src.core.simulation_topology import GraphNode
from src.managers.galaxy_generator import _generate_topology_worker

# Mock planet classes for initialization
mock_udm = MagicMock()
mock_udm.get_planet_classes.return_value = {
    "Terran": {
        "req_mod": 1.0, 
        "def_mod": 1.0, 
        "slots_mod": 1.0,
        "garrison_mod": 1.0,
        "naval_mod": 1.0,
        "slots": 3,
        "max_tier": 3
    }
}
# Inject the mock into the singleton if possible or just mock the method
UniverseDataManager.get_instance = MagicMock(return_value=mock_udm)

def test_repro_recursion_error():
    # Increase recursion limit to see if it's just deep or infinite
    # Note: pickle often hits this on complex graphs
    
    # Create a system
    system = StarSystem("ReproSystem", 0, 0)
    
    # Add planets
    p1 = Planet("Planet1", "Neutral", orbit_index=1)
    p1.system = system
    system.add_planet(p1)
    
    # Generate nodes
    n1 = GraphNode("Node1", "Planet", "Node1")
    n1.metadata["system"] = system
    n1.metadata["object"] = p1
    p1.node_reference = n1
    system.nodes.append(n1)
    
    # Add connections (circular)
    s2 = StarSystem("OtherSystem", 1, 1)
    system.connections.append(s2)
    s2.connections.append(system)
    
    # Try to pickle
    # On very complex graphs with hundreds of nodes (like the 300 in StarSystem),
    # this can easily hit the recursion limit of 1000 if there are many back-pointers.
    try:
        pickle.dumps(system)
    except RecursionError:
        pytest.fail("RecursionError during pickling of StarSystem structure")

def test_pickling_cleanup_safety():
    # This test verifies that we can safely pickle AFTER breaking references
    system = StarSystem("SafetySystem", 0, 0)
    p1 = Planet("Planet1", "Neutral", orbit_index=1)
    p1.system = system
    system.add_planet(p1)
    
    n1 = GraphNode("Node1", "Planet", "Node1")
    n1.metadata["system"] = system
    n1.metadata["object"] = p1
    p1.node_reference = n1
    system.nodes.append(n1)
    
    # Break references
    system.connections = []
    p1.system = None
    n1.metadata["system"] = None
    n1.metadata["object"] = None
    p1.node_reference = None
    
    # Should definitely pickle now
    data = pickle.dumps(system)
    assert data is not None
    
    # Restore and verify
    restored = pickle.loads(data)
    assert restored.name == "SafetySystem"

def test_worker_reference_breaking():
    # Create a system with back-references
    system = StarSystem("WorkerTest", 0, 0)
    p1 = Planet("Planet1", system, orbit_index=1)
    system.add_planet(p1)
    
    # Generate nodes
    system.generate_topology(force=True)
    
    # Verify nodes have back-references initially
    assert any("system" in n.metadata for n in system.nodes)
    assert any("object" in n.metadata for n in system.nodes)
    
    # Run worker
    processed = _generate_topology_worker((system, False))
    
    # Verify references are broken in the returned object
    assert all("system" not in n.metadata for n in processed.nodes)
    assert all("object" not in n.metadata for n in processed.nodes)
    assert all(p.system is None for p in processed.planets)
    assert all(p.node_reference is None for p in processed.planets)
    
    # Verify it can be pickled
    data = pickle.dumps(processed)
    assert data is not None
