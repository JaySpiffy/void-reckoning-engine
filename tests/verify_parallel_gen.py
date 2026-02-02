
import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.managers.galaxy_generator import GalaxyGenerator, init_galaxy_rng
from src.core.universe_data import UniverseDataManager

# Mock Data
MOCK_PLANET_CLASSES = {
    "Terran": {"req_mod": 1.0, "def_mod": 1, "slots": 5},
    "Arid": {"req_mod": 0.8, "def_mod": 0, "slots": 4},
    "Ocean": {"req_mod": 1.1, "def_mod": 1, "slots": 6}
}

# Monkeypatch
def mock_get_classes(self):
    return MOCK_PLANET_CLASSES

# Apply Patch
UniverseDataManager.get_planet_classes = mock_get_classes

# Mock Config
class MockConfig:
    def __init__(self):
        self.universe_root = "test"
        self.factions_dir = "test/factions"

def verify_parallel():
    print("Verifying Parallel Galaxy Generation...")
    
    # Init Singleton manually if needed (UniverseDataManager)
    # But GalaxyGenerator relies on it loosely. 
    # We might need to mock get_instance result or ensure it doesn't crash.
    
    gen = GalaxyGenerator()
    init_galaxy_rng(42)
    
    # Generate Small Galaxy (Sequential vs Parallel is hard to toggle explicitly without mocking)
    # But since we replaced the code, it runs Parallel by default.
    # We just want to ensure it works and produces valid output (topology).
    
    start_time = time.time()
    systems, planets = gen.generate_galaxy(num_systems=20, min_planets=1, max_planets=2)
    duration = time.time() - start_time
    
    print(f"  - Generated {len(systems)} systems in {duration:.4f}s")
    
    # Check Topology
    nodes_count = 0
    edges_count = 0
    for s in systems:
        nodes_count += len(s.nodes)
        for n in s.nodes:
            edges_count += len(n.edges)
            
    print(f"  - Total Nodes: {nodes_count}")
    print(f"  - Total Edges: {edges_count}")
    
    # Basic Validity Checks
    assert len(systems) == 20
    assert nodes_count > 0, "No nodes generated!"
    assert edges_count > 0, "No edges generated!"
    
    # Check Referential Integrity (Planets -> System)
    for p in planets:
        assert p.system in systems, "Planet system reference points to unknown system"
        # Check reverse
        assert p in p.system.planets, "System does not contain its planet"

    print("Parallel Generation Verification: PASS")

if __name__ == "__main__":
    # Ensure entry point protection for multiprocessing
    multiprocessing_check = True 
    verify_parallel()
