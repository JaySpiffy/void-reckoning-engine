
import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core import gpu_utils
from src.managers.battle_manager import BattleManager
from src.combat.combat_tracker import CombatTracker

class MockUnit:
    def __init__(self, faction, cost=100, alive=True, domain='space', ship_class='Cruiser', tier=2):
        self.faction = faction
        self.cost = cost
        self._alive = alive
        self.domain = domain
        self.ship_class = ship_class
        self.tier = tier
    def is_alive(self): return self._alive

class MockFleet:
    def __init__(self, id, faction, location):
        self.id = id
        self.faction = faction
        self.location = location
        self.is_destroyed = False
        self.units = []

class MockContext:
    def __init__(self):
        self.fleets = []
        self.armies = []
        self.planets = []
        self.starbases = []
    def get_all_fleets(self): return self.fleets
    def get_all_army_groups(self): return self.armies
    def get_all_planets(self): return self.planets
    def get_all_starbases(self): return self.starbases

def verify_presence_index():
    print("--- Verifying PresenceIndex ---")
    ctx = MockContext()
    bm = BattleManager(ctx)
    
    # Mock some fleets
    loc1 = "Terra"
    loc2 = "Mars"
    f1 = MockFleet(1, "Empire", loc1)
    f2 = MockFleet(2, "Chaos", loc1)
    f3 = MockFleet(3, "Empire", loc2)
    
    ctx.fleets = [f1, f2, f3]
    
    bm._update_presence_indices() # This should call the new logic
    
    print(f"Factions at {loc1}: {bm.get_factions_at(loc1)}")
    assert "Empire" in bm.get_factions_at(loc1)
    assert "Chaos" in bm.get_factions_at(loc1)
    assert bm.is_faction_at("Empire", loc1) == True
    assert bm.is_faction_at("Chaos", loc2) == False
    print("PresenceIndex: SUCCESS")

def verify_vectorized_finalization():
    print("\n--- Verifying Vectorized Finalization ---")
    tracker = CombatTracker()
    
    # Create 1000 units
    units = [MockUnit("Empire", cost=100, alive=(i % 2 == 0)) for i in range(1000)]
    pre_battle_counts = {"Empire": 1000}
    
    # Time the legacy vs vectorized (conceptually)
    start = time.time()
    perf_data = tracker._finalize_vectorized({"Empire": units}, pre_battle_counts)
    end = time.time()
    
    stats = perf_data["Empire"]
    print(f"Total: {stats['total']}, Alive: {stats['alive']}, Resources Lost: {stats['resources_lost']}")
    assert stats["alive"] == 500
    assert stats["resources_lost"] == 500 * 100
    print(f"Vectorized Finalization: SUCCESS (Duration: {end-start:.6f}s)")

def verify_gpu_cleanup():
    print("\n--- Verifying GPU Cleanup ---")
    try:
        gpu_utils.cleanup_gpu_resources()
        print("GPU Cleanup: SUCCESS (Executed without error)")
    except Exception as e:
        print(f"GPU Cleanup: FAILED ({e})")

if __name__ == "__main__":
    verify_presence_index()
    verify_vectorized_finalization()
    verify_gpu_cleanup()
