
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.fleet import Fleet
from src.models.unit import Unit

class MockUnit(Unit):
    def __init__(self, uid):
        self.id = uid
        self.name = f"Unit_{uid}"
        self.id = uid
        self.name = f"Unit_{uid}"
        self._fleet_ref = None # Internal backing for property
        self.cost = 100
        self.cost = 100
        self.health_comp = type('obj', (object,), {'max_hp': 100, 'current_hp': 100, 'is_alive': lambda: True})
        self.faction = "Test"
        self._cached_strength = 100
        

    
    def to_dict(self): return {"id": self.id}

def verify_merging():
    print("Verifying Set-Based Fleet Merging...")
    
    f1 = Fleet("F1", "FactionA", None)
    f2 = Fleet("F2", "FactionA", None)
    
    # Populate F1
    for i in range(100):
        u = MockUnit(f"u1_{i}")
        f1.units.append(u)
        u.set_fleet(f1)
        
    # Populate F2
    for i in range(100):
        u = MockUnit(f"u2_{i}")
        f2.units.append(u)
        u.set_fleet(f2)
        
    # Duplicate Unit (Edge Case)
    dup = f1.units[0]
    f2.units.append(dup) # Manually inject duplicate
    
    print(f"  - F1 Size: {len(f1.units)}")
    print(f"  - F2 Size: {len(f2.units)}")
    
    # Merge
    print("  - Merging F2 into F1...")
    res = f1.merge_with(f2)
    
    print(f"  - Merge Result: {res}")
    print(f"  - F1 New Size: {len(f1.units)}")
    print(f"  - F2 New Size: {len(f2.units)}")
    print(f"  - F2 Destroyed: {f2.is_destroyed}")
    
    print(f"  - Dup ID: {dup.id}")
    print(f"  - F1 IDs Sample: {[u.id for u in f1.units[:5]]}")
    
    # Check if dup exists multiple times in F1
    dup_count = sum(1 for u in f1.units if u.id == dup.id)
    print(f"  - Dup Count in F1: {dup_count}")
    
    assert len(f1.units) == 200, f"Expected 200 units, got {len(f1.units)}. Dup count: {dup_count}"
    
    # Verify Unit Ownership
    for u in f1.units:
        assert u.fleet == f1, "Unit fleet reference not updated"
        
    print("Merging Verification: PASS")

if __name__ == "__main__":
    verify_merging()
