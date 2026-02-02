
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.fleet import Fleet
from src.models.unit import Unit

class MockHealth:
    def __init__(self, is_alive_val=True):
        self._alive = is_alive_val
        self.max_hp = 100
        self.current_hp = 100 if is_alive_val else 0
        
    def is_alive(self):
        return self._alive

class MockUnit(Unit):
    def __init__(self, name, alive=True, ship_class="Escort"):
        self.name = name
        self.cost = 100
        self.power_rating = 10
        self.health_comp = MockHealth(alive)
        self.faction = "Test"
        self.ship_class = ship_class
        # Standard behavior: attribute missing initially
    
    def _calculate_strength(self):
        return 10 if self.health_comp.is_alive() else 0

def verify_generators():
    print("Verifying Generator Views...")
    
    # 1. Setup
    f = Fleet("F1", "Test", None)
    
    u1 = MockUnit("U1", alive=True, ship_class="Escort")
    u2 = MockUnit("U2", alive=False, ship_class="Battleship")
    u3 = MockUnit("U3", alive=True, ship_class="Cruiser")
    
    f.units = [u1, u2, u3]
    
    # 2. Verify alive_units generator
    print("  Testing alive_units generator...")
    alive = list(f.alive_units)
    assert len(alive) == 2, f"Expected 2 alive units, got {len(alive)}"
    assert u1 in alive
    assert u3 in alive
    assert u2 not in alive
    
    # 3. Verify Integration with Batch Power
    print("  Testing Batch Power Integration...")
    # Should sum U1 (10) + U3 (10) = 20. U2 is dead.
    power = f.batch_calculate_power()
    assert power == 20, f"Expected power 20, got {power}"
    
    # 4. Verify Integration with Capability Matrix
    print("  Testing Capability Matrix Integration...")
    matrix = f.get_capability_matrix()
    # U2 is a Battleship but dead, so should not count
    assert matrix["Battleship"] == 0, "Dead Battleship should not be counted"
    assert matrix["Escort"] == 1
    assert matrix["Cruiser"] == 1
    
    print("Generator View Verification: PASS")

if __name__ == "__main__":
    verify_generators()
