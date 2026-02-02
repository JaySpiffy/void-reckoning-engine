
import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.fleet_index import FleetIndex
from src.managers.fleet_manager import FleetManager
from src.models.unit import Unit
from src.models.fleet import Fleet

# Mocks
class MockLocation:
    def __init__(self, name):
        self.name = name
        self.id = name # Simplify
        
    def __repr__(self):
        return f"Loc({self.name})"

class MockStats:
    def __init__(self, ma, md, dmg):
        self.ma = ma
        self.md = md
        self.damage = dmg

class MockUnit(Unit):
    def __init__(self, name, power=100, stats=None):
        self.name = name
        self.power_rating = power
        self.cost = 1000
        self.health_comp = type('obj', (object,), {'max_hp': 100, 'current_hp': 100, 'is_alive': lambda: True})
        self.stats_comp = stats
        self.faction = "TestFaction"
        
class MockEngine:
    def __init__(self):
        self.logger = None

def verify_indexing():
    print("Verifying Fleet Location Indexing...")
    
    idx = FleetIndex()
    loc1 = MockLocation("SystemA")
    loc2 = MockLocation("SystemB")
    
    f1 = Fleet("F1", "FactionA", loc1)
    f2 = Fleet("F2", "FactionA", loc1)
    f3 = Fleet("F3", "FactionB", loc2)
    
    # Add
    idx.add(f1)
    idx.add(f2)
    idx.add(f3)
    
    # Verify Get
    res1 = idx.get_by_location(loc1)
    print(f"  - Loc1 Fleets: {len(res1)}")
    assert len(res1) == 2, f"Expected 2 fleets at loc1, got {len(res1)}"
    assert f1 in res1
    assert f2 in res1
    
    res2 = idx.get_by_location(loc2)
    print(f"  - Loc2 Fleets: {len(res2)}")
    assert len(res2) == 1, f"Expected 1 fleet at loc2"
    
    # Verify Remove
    idx.remove(f1)
    res1_updated = idx.get_by_location(loc1)
    assert len(res1_updated) == 1, "Failed to remove F1 from location index"
    assert f1 not in res1_updated
    
    print("Indexing Verification: PASS")

def verify_unit_strength():
    print("\nVerifying Unit Strength Caching...")
    
    stats = MockStats(50, 50, 50) # Average stats -> mult 1.0
    u = MockUnit("U1", power=100, stats=stats)
    
    # 1. Initial Calc
    s1 = u.strength
    print(f"  - Initial Strength: {s1}")
    assert s1 == 100, f"Expected 100, got {s1}"
    assert hasattr(u, '_cached_strength')
    
    # 2. Modify Stats (Should NOT change strength due to cache)
    u.stats_comp.damage = 200 # Significant boost
    s2 = u.strength
    print(f"  - Cached Strength: {s2}")
    assert s2 == 100, "Cache failed, value updated prematurely"
    
    # 3. Invalidate Cache
    u.invalidate_cache()
    print("  - Cache Invalidated")
    assert not hasattr(u, '_cached_strength')
    
    # 4. Recalculate
    s3 = u.strength
    print(f"  - Recalculated Strength: {s3}")
    # New mult: (50+50+200)/150 = 300/150 = 2.0
    # Expected: 100 * 2.0 = 200
    assert s3 == 200, f"Expected 200, got {s3}"
    
    print("Unit Strength Verification: PASS")

if __name__ == "__main__":
    verify_indexing()
    verify_unit_strength()
