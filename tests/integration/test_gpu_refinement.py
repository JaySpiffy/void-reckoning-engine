import pytest
from src.core import gpu_utils
from src.combat import batch_shooting

pytestmark = pytest.mark.skip(reason="CuPy compatibility issue")

class MockUnit:
    def __init__(self, name, bs=50, armor=0, invuln=7, cover=False):
        self.name = name
        self.bs = bs
        self.armor = armor
        self.abilities = {}
        if cover: self.abilities["Cover"] = True
        if invuln < 7: self.abilities["Invuln"] = invuln
        self.components = []
        
        class MockWpn:
            name = "TestGun"
            type = "Weapon"
            is_destroyed = False
            weapon_stats = {"Range": 24, "Str": 1, "AP": 0} # 10 dmg (Str*10)
        self.components.append(MockWpn())
        
    def is_alive(self): return True

class TestGPURefinement:
    
    @pytest.mark.gpu
    @pytest.mark.integration
    def test_synchronization(self):
        """Just ensure it doesn't crash on either backend."""
        print(f"\nTesting GPU Synchronization...")
        try:
            gpu_utils.synchronize()
            print("Synchronize() called successfully.")
        except Exception as e:
            pytest.fail(f"Synchronize() failed: {e}")
            
    @pytest.mark.gpu
    @pytest.mark.integration
    def test_critical_hit_logic(self):
        print(f"Testing Batch Shooting Logic Improvements...")
        # Force backend check if needed, but we rely on fallback
        
        u1 = MockUnit("Shooter", bs=100) # Always hit
        u2 = MockUnit("Target", armor=0) # No armsave
        
        target_map = {id(u1): id(u2)}
        dist_map = {id(u1): 10.0}
        active_units = {id(u1): u1, id(u2): u2}
        
        # Warmup
        results = batch_shooting.resolve_shooting_batch([u1], target_map, dist_map, active_units)
        assert len(results) > 0
        res = results[0]
        
        # Base damage is Str 1 * 10 = 10.
        # If no crit, dmg = 10. If Crit, dmg = 15.
        
        print(f"Damage Sample: {res['damage']}")
        # We expect at least 10
        assert res['damage'] >= 10.0
