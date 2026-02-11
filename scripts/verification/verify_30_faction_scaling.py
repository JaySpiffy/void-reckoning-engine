from src.combat.rust_tactical_engine import RustTacticalEngine
from unittest.mock import MagicMock
import collections

class MockUnit:
    def __init__(self, name, faction, hp=100):
        self.name = name
        self.faction = faction
        self.max_hp = hp
        self.current_hp = hp
        self.is_destroyed = False
        self.health_comp = MagicMock()
        self.damage = 10.0
        self.weapon_comps = []

def verify_scaling():
    engine = RustTacticalEngine()
    if not engine.rust_engine:
        print("Rust Engine unavailable.")
        return

    # Simulate 30 Factions
    num_factions = 30
    armies = {}
    for i in range(num_factions):
        f_name = f"Faction_{i}"
        armies[f_name] = [MockUnit(f"U_{i}_1", f_name)]

    print(f"Initializing Battle with {num_factions} factions...")
    engine.initialize_battle(armies)
    
    state = engine.get_state()
    # State format: (id, x, y, hp, is_alive)
    
    positions = []
    for row in state:
        bid, x, y, hp, alive = row
        positions.append((round(x, 2), round(y, 2)))
        # Print a few to check
        if bid <= 5:
            print(f"Faction {bid-1} center: ({x:.2f}, {y:.2f})")

    # Check for overlaps
    pos_counts = collections.Counter(positions)
    overlaps = [pos for pos, count in pos_counts.items() if count > 1]
    
    if overlaps:
        print(f"\n[FAILURE] Found {len(overlaps)} overlapping deployment positions!")
        for pos in overlaps:
            print(f"  Overlap at {pos}")
    else:
        print("\n[SUCCESS] No overlapping initial positions found for 30 factions!")

    # Check distance between some factions to ensure circle
    # Faction 0 at angle 0 -> should be (50+40, 50) = (90, 50)
    # Faction 15 (opposite) -> angle pi -> should be (50-40, 50) = (10, 50)
    
    f0_pos = positions[0]
    f15_pos = positions[15]
    
    print(f"\nFaction 0 pos: {f0_pos} (Target: ~90.0, 50.0)")
    print(f"Faction 15 pos: {f15_pos} (Target: ~10.0, 50.0)")

if __name__ == "__main__":
    verify_scaling()
