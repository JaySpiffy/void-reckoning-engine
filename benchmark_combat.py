import sys
import os
import time
sys.path.append(os.getcwd())

from src.combat.rust_tactical_engine import RustTacticalEngine
from src.combat.tactical_engine import initialize_battle_state, execute_battle_round

class MockUnit:
    def __init__(self, name, faction, hp=100.0, damage=10.0, bid=0):
        self.name = name
        self.faction = faction
        self.max_hp = hp
        self.base_hp = hp # For legacy tracker
        self.current_hp = hp
        self.damage = damage
        self.weapon_comps = []
        self.health_comp = self
        self.is_destroyed = False
        self.battle_id = bid
        self.components = [] # For legacy engine
        self.is_alive = lambda: self.current_hp > 0
        self.grid_x = 0
        self.grid_y = 0
        self.speed = 10
        self.evasion = 0
        self.shield_comp = None
        self.armor_comp = None
        
    def add_weapon(self, name, damage, cooldown):
        w = type('obj', (object,), {
            "name": name, 
            "weapon_stats": {"damage": damage, "cooldown": cooldown, "type": "Kinetic"},
            "to_dict": lambda: {"name": name, "type": "Kinetic"}
        })
        self.weapon_comps.append(w)
        # For Legacy
        self.components.append(w)

    def gain_xp(self, amount, context=None):
        pass

def create_army(faction, count, start_id):
    army = []
    for i in range(count):
        u = MockUnit(f"{faction}_{i}", faction, hp=100.0, bid=start_id+i)
        u.add_weapon("Laser", 20.0, 1.0)
        army.append(u)
    return army

def run_python_benchmark(count):
    print(f"--- Python Benchmark ({count} vs {count}) ---")
    u1 = create_army("Empire", count, 1)
    u2 = create_army("Rebels", count, count+1)
    armies = {"Empire": u1, "Rebels": u2}
    
    start_time = time.time()
    # Initialize Legacy State
    state = initialize_battle_state(armies)
    
    rounds = 0
    # Run 10 rounds
    for _ in range(10):
        execute_battle_round(state)
        rounds += 1
        
    end_time = time.time()
    duration = end_time - start_time
    print(f"Python: {rounds} rounds in {duration:.4f}s")
    return duration

def run_rust_benchmark(count):
    print(f"--- Rust Benchmark ({count} vs {count}) ---")
    u1 = create_army("Empire", count, 1)
    u2 = create_army("Rebels", count, count+1)
    armies = {"Empire": u1, "Rebels": u2}
    
    start_time = time.time()
    engine = RustTacticalEngine()
    engine.initialize_battle(armies)
    
    rounds = 0
    for _ in range(10):
        engine.resolve_round()
        rounds += 1
        
    end_time = time.time()
    duration = end_time - start_time
    print(f"Rust: {rounds} rounds in {duration:.4f}s")
    return duration

if __name__ == "__main__":
    count = 100
    py_time = run_python_benchmark(count)
    rust_time = run_rust_benchmark(count)
    
    print(f"\nSpeedup: {py_time / rust_time:.2f}x")
