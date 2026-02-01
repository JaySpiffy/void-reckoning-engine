import pytest
from src.combat import batch_shooting
from src.combat.tactical.gpu_tracker import GPUTracker

pytestmark = pytest.mark.skip(reason="CuPy compatibility issue")

class MockUnit:
    def __init__(self, name, x=0, y=0, factions="A", bs=50):
        self.name = name
        self.grid_x = x
        self.grid_y = y
        self.faction = factions
        self.bs = bs
        self.armor = 10
        self.abilities = {}
        self.components = []
        
        # Add 2 Weapons
        class MockWpn:
             def __init__(self, n, r):
                 self.name = n
                 self.type = "Weapon"
                 self.is_destroyed = False
                 self.weapon_stats = {"Range": r, "Str": 4, "AP": 0}
                 
        self.components.append(MockWpn("Bolter", 24))
        self.components.append(MockWpn("Plasma", 24))
        
    def is_alive(self): return True
    def take_damage(self, amount): pass 

class TestGPUProductionHardening:
    
    @pytest.mark.gpu
    @pytest.mark.integration
    def test_multi_weapon_firing(self):
        print(f"\nTesting Multi-Weapon Volleys...")
        u1 = MockUnit("Shooter", bs=100)
        u2 = MockUnit("Target")
        
        target_map = {id(u1): id(u2)}
        dist_map = {id(u1): 10.0}
        active_units = {id(u1): u1, id(u2): u2}
        
        # Expectation: 2 results (1 per weapon)
        results = batch_shooting.resolve_shooting_batch([u1], target_map, dist_map, active_units)
        
        print(f"Results Count: {len(results)}")
        assert len(results) == 2, "Should fire both weapons"
        
        wpn_names = [r["weapon"].name for r in results]
        assert "Bolter" in wpn_names
        assert "Plasma" in wpn_names
        print("Multi-Weapon Test Passed.")
        
    @pytest.mark.gpu
    @pytest.mark.integration
    def test_memory_cleanup(self):
        print(f"\nTesting Memory Cleanup...")
        tracker = GPUTracker()
        u1 = MockUnit("U1", 10, 10, "A")
        u2 = MockUnit("U2", 20, 20, "B")
        tracker.initialize([u1, u2])
        
        # Ensure data allocated
        if hasattr(tracker.positions, 'device'):
             print(f"Allocated on {tracker.positions.device}")
             
        # Cleanup
        tracker.cleanup()
        
        assert tracker.positions is None
        assert tracker.active_count == 0
        print("Memory Cleanup Test Passed.")
        
    @pytest.mark.gpu
    @pytest.mark.integration
    def test_synchronization_call(self):
        # We can't easily assert that sync was called without mocking,
        # but we can call a method that uses it and ensure no crash.
        print(f"\nTesting Sync Integration via Tracker...")
        tracker = GPUTracker()
        u1 = MockUnit("U1", 10, 10, "A")
        u2 = MockUnit("U2", 20, 20, "B")
        tracker.initialize([u1, u2])
        
        # compute_flow_field calls synchronize()
        res = tracker.compute_flow_field()
        assert len(res) > 0
        print("Sync Integration Test Passed (No Crash).")
