
import time
import sys
import os
import random
import numpy as np
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.managers.battle_manager import BattleManager
from src.combat.tactical_engine import initialize_battle_state, execute_battle_round
from src.core import gpu_utils
from src.combat.combat_phases import ShootingPhase

class MockWeapon:
    def __init__(self):
        self.type = "Weapon"
        self.is_destroyed = False
        self.name = "Bolter"
        self.weapon_stats = {"Range": 50, "S": 4, "AP": 0, "D": 1, "Attacks": 2}
    def to_dict(self): return {"name": self.name}
    def __lt__(self, other): return self.name < other.name

class MockUnit:
    def __init__(self, uid, faction, x, y):
        self.id = uid
        self.name = f"{faction}_{uid}"
        self.faction = faction
        self.grid_x = x
        self.grid_y = y
        self.is_destroyed = False
        self.current_hp = 100
        self.max_hp = 100
        self.base_hp = 100
        self.bs = 50
        self.armor = 30
        self.armor_front = 40
        self.armor_side = 30
        self.armor_rear = 10
        self.components = [MockWeapon()]
        self.movement_points = 5
        self.abilities = {}
        self.active_mods = {}
        self.is_suppressed = False
        self.formation = None
        
    def is_alive(self):
        return not self.is_destroyed and self.current_hp > 0
    
    def is_ship(self): return False

    def take_damage(self, dmg, **kwargs):
        self.current_hp -= dmg
        if self.current_hp <= 0:
            self.is_destroyed = True
        return 0, dmg, 0, None
        
    def recover_suppression(self): pass
    def regenerate_shields(self): pass
    
    # Legacy loop sorting requirement
    def __lt__(self, other):
        return self.id < other.id

class MockRules:
    def register_phases(self):
        return [ShootingPhase()]
    def get_phase_order(self):
        return ['shooting']
    def apply_doctrine_modifiers(self, *args):
        return {"dmg_mult": 1.0, "bs_mod": 0}

def run_benchmark():
    print("Preparing Benchmark...")
    
    N = 1000 # Increase load to see difference
    
    # 0. Warmup
    print("Warming up JIT/Caches...")
    units_a = [MockUnit(i, "Imperium", random.randint(0, 50), random.randint(0, 50)) for i in range(50)]
    units_b = [MockUnit(i+1000, "Orks", random.randint(0, 50), random.randint(0, 50)) for i in range(50)]
    state_warm = initialize_battle_state({"A":units_a, "B":units_b}, universe_rules=MockRules())
    execute_battle_round(state_warm)
    
    # --- Run 1: Vectorized ---
    print(f"\n--- Running Vectorized Battle (NumPy) N={N} per side ---")
    
    units_a = [MockUnit(i, "Imperium", random.randint(0, 50), random.randint(0, 50)) for i in range(N)]
    units_b = [MockUnit(i+10000, "Orks", random.randint(0, 50), random.randint(0, 50)) for i in range(N)]
    armies = {"Imperium": units_a, "Orks": units_b}
    
    state_vec = initialize_battle_state(armies, universe_rules=MockRules())
    
    if not hasattr(state_vec, 'gpu_tracker') or not state_vec.gpu_tracker:
        print("ERROR: Tracker missing!")
        return
        
    start_time = time.time()
    execute_battle_round(state_vec)
    dur_vec = time.time() - start_time
    print(f"Vectorized Duration: {dur_vec:.4f}s")
    
    # --- Run 2: Legacy ---
    print(f"\n--- Running Legacy Loop N={N} per side ---")
    
    units_a = [MockUnit(i, "Imperium", random.randint(0, 50), random.randint(0, 50)) for i in range(N)]
    units_b = [MockUnit(i+10000, "Orks", random.randint(0, 50), random.randint(0, 50)) for i in range(N)]
    armies = {"Imperium": units_a, "Orks": units_b}
    
    state_legacy = initialize_battle_state(armies, universe_rules=MockRules())
    
    # Disable Tracker
    if hasattr(state_legacy, 'gpu_tracker'):
         state_legacy.gpu_tracker = None
         
    start_time = time.time()
    execute_battle_round(state_legacy)
    dur_legacy = time.time() - start_time
    print(f"Legacy Duration: {dur_legacy:.4f}s")
    
    if dur_vec > 0:
        print(f"\nSpeedup: {dur_legacy / dur_vec:.2f}x")

if __name__ == "__main__":
    run_benchmark()
