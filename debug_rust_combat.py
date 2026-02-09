
import sys
import os
import time

# Add src to path
sys.path.append(os.getcwd())

from src.combat.rust_tactical_engine import RustTacticalEngine
from src.models.unit import Ship, Component

def debug_combat():
    print("=== DEBUGGING RUST COMBAT ===")
    
    # 1. Initialize Engine
    engine = RustTacticalEngine(width=1000.0, height=1000.0)
    if not engine.rust_engine:
        print("CRITICAL: Rust Engine not loaded!")
        return

    # 2. Create Mock Units with explicit stats
    u1 = Ship("TestShip_A", "Faction_A", hp=1000, armor=10, speed=20, agility=10)
    u1.base_movement_points = 20
    # Add a weapon
    u1.weapon_comps = [
        Component("Laser", 10, "Weapon", weapon_stats={"type": "Energy", "range": 500.0, "damage": 50.0, "cooldown": 2.0, "accuracy": 0.9})
    ]
    u1.max_hp = 1000
    
    u2 = Ship("TestShip_B", "Faction_B", hp=1000, armor=10, speed=20, agility=10)
    u2.base_movement_points = 20
    u2.weapon_comps = [
        Component("Missile", 10, "Weapon", weapon_stats={"type": "Missile", "range": 500.0, "damage": 50.0, "cooldown": 3.0, "accuracy": 0.8})
    ]
    u2.max_hp = 1000

    # 3. Setup Battle
    armies = {
        "Faction_A": [u1],
        "Faction_B": [u2]
    }
    
    print("Initializing Battle...")
    engine.initialize_battle(armies)
    
    # 4. Run Steps and Monitor
    print("\nRunning Simulation Steps...")
    for i in range(1, 251): # 250 ticks
        cont = engine.resolve_round()
        
        # Snapshot state
        state = engine.get_state()
        # state format: [(id, x, y, hp, alive), ...]
        
        # Find units
        s1 = next((s for s in state if s[0] == 1), None) # ID 1 (Faction A)
        s2 = next((s for s in state if s[0] == 2), None) # ID 2 (Faction B)
        
        if i % 10 == 0:
            print(f"Tick {i}:")
            if s1: print(f"  Unit A: Pos=({s1[1]:.1f}, {s1[2]:.1f}) HP={s1[3]:.1f} Alive={s1[4]}")
            if s2: print(f"  Unit B: Pos=({s2[1]:.1f}, {s2[2]:.1f}) HP={s2[3]:.1f} Alive={s2[4]}")
            
            # Distance
            if s1 and s2:
                dx = s1[1] - s2[1]
                dy = s1[2] - s2[2]
                dist = (dx*dx + dy*dy)**0.5
                print(f"  Distance: {dist:.1f}")

        if not cont:
            print(f"\nBattle Ended at Tick {i}!")
            break
            
    print("\nFinal State:")
    state = engine.get_state()
    for s in state:
        print(s)

if __name__ == "__main__":
    debug_combat()
