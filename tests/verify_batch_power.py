
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.fleet import Fleet
from src.models.unit import Unit

class MockHealth:
    def __init__(self, hp=100):
        self.current_hp = hp
        self.max_hp = 100
        
    def is_alive(self):
        return self.current_hp > 0

class MockUnit(Unit):
    def __init__(self, name, power=10):
        self.name = name
        self.cost = power * 10
        self.power_rating = power
        self.health_comp = MockHealth()
        self.faction = "Test"
        # self._cached_strength = None # REMOVED: standard behavior is attribute missing
        
    # Override init to skip component injection complexity for test
    # But we need _calculate_strength
    
def verify_batch_power():
    print("Verifying Batch Power Calculation...")
    
    # 1. Setup Fleet
    f = Fleet("F1", "Test", None)
    
    # 2. Add Units
    u1 = MockUnit("U1", power=100) # Str 100
    u2 = MockUnit("U2", power=50)  # Str 50
    f.units = [u1, u2]
    
    # 3. Test Initial Calculation
    # Should calculate, cache, and clean dirty flag
    print("  Testing Initial Calculation...")
    power = f.power
    assert power == 150, f"Expected 150, got {power}"
    assert f._power_dirty == False, "Fleet power dirty flag should be False"
    assert hasattr(u1, '_cached_strength'), "Unit 1 shoud have cached strength"
    
    # 4. Test Caching (Should not recalculate if not dirty)
    # Manually modify cached value to prove it's used
    f._cached_power = 999
    assert f.power == 999, "Should use cached value"
    
    # 5. Test Invalidation (Dirty Flag)
    # Dirty the fleet manually (normally done by unit.invalidate_strength_cache -> fleet.invalidate_caches)
    print("  Testing Invalidation...")
    f._power_dirty = True
    # Invalidate unit 1
    if hasattr(u1, '_cached_strength'): del u1._cached_strength
    
    # Recalculate - should re-compute U1, use cached (if any/none) U2? 
    # Our batch logic checks `hasattr(u, '_cached_strength')`.
    # U2 still has it. U1 does not.
    power = f.power
    assert power == 150, f"Expected 150 after invalidation, got {power}"
    assert hasattr(u1, '_cached_strength'), "Unit 1 should have re-cached"
    
    # 6. Test Damage Scaling
    print("  Testing Damage Scaling...")
    u1.health_comp.current_hp = 50 # 50% health -> 50 strength
    # Invalidate
    if hasattr(u1, '_cached_strength'): del u1._cached_strength
    f._power_dirty = True
    
    power = f.power
    # U1: 50, U2: 50 -> Total 100
    assert power == 100, f"Expected 100 (50+50), got {power}"
    
    print("Batch Power Calculation Verification: PASS")

if __name__ == "__main__":
    verify_batch_power()
