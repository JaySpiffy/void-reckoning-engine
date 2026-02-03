import pickle
from unittest.mock import MagicMock
from src.models.star_system import StarSystem
from src.models.planet import Planet
from src.core.simulation_topology import GraphNode
from src.managers.galaxy_generator import _generate_topology_worker

def test_node_restoration_with_modified_names():
    # 1. Setup - Create a system with a planet
    system = StarSystem("RestorationTest", 0, 0)
    # Mock planet classes for recalc_stats
    mock_udm = MagicMock()
    mock_udm.get_planet_classes.return_value = {
        "Terran": {"req_mod": 1.0, "def_mod": 1.0, "slots_mod": 1.0, "garrison_mod": 1.0, "naval_mod": 1.0, "slots": 3, "max_tier": 3}
    }
    from src.core.universe_data import UniverseDataManager
    UniverseDataManager.get_instance = MagicMock(return_value=mock_udm)
    
    p1 = Planet("Planet1", system, orbit_index=1)
    p1.id = "Planet1_ID" # Ensure it has an ID
    system.add_planet(p1)
    
    # Generate topology
    system.generate_topology(force=True)
    
    # 2. Simulate Worker behavior (Breaking references)
    processed = _generate_topology_worker((system, False))
    
    # 3. Simulate Hub naming modification (Modifies name but NOT id)
    # In StarSystem.generate_topology, node.id is the original name/id
    for n in processed.nodes:
        if n.id == "Planet1":
             n.name += " [HUB]"
    
    # 4. Perform Restoration Logic (Ported from GalaxyGenerator.generate_all_topologies)
    new_sys_map = {processed.name: processed}
    connection_map = {} # No connections for this simple test
    
    s = processed
    # 1. Restore System Connections (Skipped)
    
    # 2. Restore Planet-System and Node-System references
    node_map = {n.id: n for n in s.nodes}
    for p in s.planets:
        p.system = s
        p_id = p.id if hasattr(p, 'id') else p.name
        if p_id in node_map:
            node = node_map[p_id]
            p.node_reference = node
            node.metadata["object"] = p
            
    for n in s.nodes:
        n.metadata["system"] = s
        if n.type == "Planet" and "object" not in n.metadata:
            match = next((p for p in s.planets if (hasattr(p, 'id') and p.id == n.id) or p.name == n.id or p.name == n.name), None)
            if match:
                 n.metadata["object"] = match
                 match.node_reference = n

    # 5. Verification
    # Find the planet node
    p_node = next(n for n in s.nodes if n.type == "Planet")
    assert " [HUB]" in p_node.name
    assert p_node.id == "Planet1" # Original ID preserved
    
    # Verify references are restored
    assert p1.node_reference == p_node
    assert p_node.metadata.get("object") == p1
    assert p_node.metadata.get("system") == s
    assert p1.system == s

if __name__ == "__main__":
    test_node_restoration_with_modified_names()
