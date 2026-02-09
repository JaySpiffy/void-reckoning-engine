from src.combat.rust_tactical_engine import RustTacticalEngine
from unittest.mock import MagicMock

class MockUnit:
    def __init__(self, name, faction, hp=100):
        self.name = name
        self.faction = faction
        self.max_hp = hp
        self.current_hp = hp
        self.is_destroyed = False
        self.health_comp = MagicMock()
        self.damage = 10.0
        # No complex weapons for this test
        self.weapon_comps = []

def run_3way_test():
    engine = RustTacticalEngine()
    if not engine.rust_engine:
        print("Rust Engine unavailable. Skipping test.")
        return

    # Create 3 Factions
    # Faction A (Index 0) -> Should be at x=10
    # Faction B (Index 1) -> Should be at x=90
    # Faction C (Index 2) -> Should be at x=90 ???
    
    armies = {
        "FactionA": [MockUnit("A1", "FactionA"), MockUnit("A2", "FactionA")],
        "FactionB": [MockUnit("B1", "FactionB"), MockUnit("B2", "FactionB")],
        "FactionC": [MockUnit("C1", "FactionC"), MockUnit("C2", "FactionC")]
    }
    
    print("Initializing Battle...")
    engine.initialize_battle(armies)
    
    # Check initial state to confirm positions
    state = engine.get_state()
    # State format: (id, x, y, hp, is_alive)
    # We need to map IDs back to factions
    
    # We know the insertion order: A, B, C
    # IDs start at 1
    
    print("\n--- Initial Positions ---")
    for row in state:
        bid, x, y, hp, alive = row
        # Identify faction by ID range
        # A: 1-2, B: 3-4, C: 5-6
        faction = "Unknown"
        if bid <= 2: faction = "FactionA"
        elif bid <= 4: faction = "FactionB"
        elif bid <= 6: faction = "FactionC"
        
        print(f"Unit {bid} ({faction}): x={x:.1f}, y={y:.1f}")

    print("\n--- Simulating 5 Rounds ---")
    for _ in range(5):
        engine.resolve_round()

    # Check state after few rounds
    state = engine.get_state()
    print("\n--- State After 5 Rounds ---")
    for row in state:
        bid, x, y, hp, alive = row
        faction = "Unknown"
        if bid <= 2: faction = "FactionA"
        elif bid <= 4: faction = "FactionB"
        elif bid <= 6: faction = "FactionC"
        print(f"Unit {bid} ({faction}): HP={hp:.1f}, Alive={alive}")

if __name__ == "__main__":
    run_3way_test()
