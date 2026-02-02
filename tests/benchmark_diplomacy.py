
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.managers.diplomacy_manager import DiplomacyManager
from src.managers.battle_manager import BattleManager

def run_diplomacy_benchmark():
    print("--- Diplomacy Optimization Benchmark ---")
    
    # Setup 40 factions
    factions = [f"Faction_{i}" for i in range(40)]
    
    # Mocking DiplomacyManager to bypass service discovery
    from unittest.mock import MagicMock
    dm = MagicMock(spec=DiplomacyManager)
    dm.factions = factions
    dm._war_cache = {}
    dm._war_matrix = {f: set() for f in factions}
    
    # Setup some wars for the matrix
    for i in range(0, 40, 4):
        f1 = f"Faction_{i}"
        f2 = f"Faction_{i+1}"
        dm._war_matrix[f1].add(f2)
        dm._war_matrix[f2].add(f1)
        dm._war_cache[tuple(sorted((f1, f2)))] = "War"

    # Use real logic for lookups
    def get_treaty(f1, f2):
        return dm._war_cache.get(tuple(sorted((f1, f2))), "Peace")
    def get_enemies(f):
        return dm._war_matrix.get(f, set())
    
    dm.get_treaty = get_treaty
    dm.get_enemies = get_enemies

    # Put 20 factions at a location
    factions_present = [f"Faction_{i}" for i in range(0, 40, 2)] # 20 factions
    
    # 1. Legacy Approach (Triangular Loop with Cache)
    # Note: Modern get_treaty is already cached, but the loop is O(F^2)
    start = time.time()
    active_combatants_legacy = set()
    factions_list = list(factions_present)
    for _ in range(1000): # Repeat 1000 times for stability
        active_combatants_legacy.clear()
        for i in range(len(factions_list)):
            f1 = factions_list[i]
            for j in range(i + 1, len(factions_list)):
                f2 = factions_list[j]
                if dm.get_treaty(f1, f2) == "War":
                    active_combatants_legacy.add(f1)
                    active_combatants_legacy.add(f2)
    end = time.time()
    dur_legacy = end - start
    print(f"Legacy O(F^2) Loop (1000 iterations): {dur_legacy:.6f}s")
    
    # 2. Optimized Approach (O(F) with War Matrix)
    start = time.time()
    active_combatants_opt = set()
    factions_present_set = set(factions_present)
    for _ in range(1000):
        active_combatants_opt.clear()
        for f in factions_present:
            enemies = dm.get_enemies(f)
            if any(enemy in factions_present_set for enemy in enemies):
                active_combatants_opt.add(f)
    end = time.time()
    dur_opt = end - start
    print(f"Optimized O(F) Matrix (1000 iterations): {dur_opt:.6f}s")
    
    if dur_opt > 0:
        print(f"Speedup: {dur_legacy / dur_opt:.2f}x")

if __name__ == "__main__":
    run_diplomacy_benchmark()
