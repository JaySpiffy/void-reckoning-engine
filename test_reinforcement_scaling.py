import sys
import os
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
        self.damage = 100.0 # High damage to trigger rapid casualties
        self.weapon_comps = []

def run_scaling_stress_test():
    engine = RustTacticalEngine()
    if not engine.rust_engine:
        print("Rust Engine unavailable.")
        return

    # 1. Create 2 Factions with 500 units each (Total 1000)
    # Goal: Verify cap (200) and reinforcements
    factions = ["Empire", "Rebels"]
    armies = {}
    for f in factions:
        armies[f] = [MockUnit(f"{f}_Ship_{i}", f) for i in range(500)]

    print(f"Initializing Battle: 1000 units total (2x500). Active Cap: {engine.unit_cap}")
    engine.initialize_battle(armies)
    
    # 2. Check Initial State
    state = engine.get_state()
    # Faction 1 should have 200, Faction 2 should have 200
    faction_counts = {}
    for row in state:
        bid, x, y, hp, alive = row
        f = engine.id_to_faction.get(bid)
        faction_counts[f] = faction_counts.get(f, 0) + 1
    
    print(f"\n--- Initial Deployment ---")
    for f, count in faction_counts.items():
        reserve_count = len(engine.reserves.get(f, []))
        print(f"  {f}: {count} Active, {reserve_count} in Reserve")
        if count > engine.unit_cap:
            print(f"  [FAILURE] {f} exceeded active cap!")

    # 3. Simulate rounds and watch reinforcements
    print(f"\n--- Simulating Attrition ---")
    for r in range(1, 11):
        engine.resolve_round()
        
        # Every round, units die due to 100 dmg vs 100 hp
        state = engine.get_state()
        alive_counts = {}
        for row in state:
            bid, x, y, hp, alive = row
            if alive:
                f = engine.id_to_faction.get(bid)
                alive_counts[f] = alive_counts.get(f, 0) + 1
        
        print(f"Round {r}:")
        for f in factions:
            active = alive_counts.get(f, 0)
            reserves = len(engine.reserves.get(f, []))
            print(f"  {f}: {active} Active, {reserves} Reserves")

    # 4. Final Verification
    print("\n--- Final Check ---")
    if all(count <= engine.unit_cap for count in alive_counts.values()):
        print("[SUCCESS] Active unit counts never exceeded cap.")
    else:
        print("[FAILURE] Active unit counts exceeded cap during battle.")

if __name__ == "__main__":
    run_scaling_stress_test()
