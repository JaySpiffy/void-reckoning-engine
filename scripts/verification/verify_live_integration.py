import sys
import os
import time
sys.path.append(os.getcwd())

from src.managers.battle_manager import BattleManager
from src.combat.combat_state import CombatState
from src.combat.rust_tactical_engine import RustTacticalEngine

class MockContext:
    def __init__(self):
        self.game_config = {
            "combat": {
                "use_rust_combat": True,
                "real_time_headless": True
            }
        }
        self.logger = self
        self.telemetry = None
        self.turn_counter = 1
        
    def combat(self, msg):
        print(f"[LOG] {msg}")

    def get_all_fleets(self):
        return []

    def get_faction(self, name):
        return None

    def log_battle_result(self, location, winner, loser, rounds, survivors, battle_stats=None):
        print(f"[MOCK] Battle Result Logged: {winner} won at {location}")

class MockUnit:
    def __init__(self, name, faction, hp=100.0, damage=10.0):
        self.name = name
        self.faction = faction
        self.max_hp = hp
        self.base_hp = hp
        self.current_hp = hp
        self.is_destroyed = False
        self.damage = damage
        self.weapon_comps = []
        self._fleet_id = "f1"
        self.health_comp = None # Fix for Rust sync
        self.components = [] # Fix for Legacy fallback
        self.is_ship = lambda: True

        self.is_alive = lambda: self.current_hp > 0
        
    def add_weapon(self, name, damage, cooldown):
        w = type('obj', (object,), {
            "name": name, 
            "weapon_stats": {"damage": damage, "cooldown": cooldown, "type": "Kinetic"}
        })
        self.weapon_comps.append(w)

class MockTracker:
    def finalize(self, *args, **kwargs):
        print("[MOCK] Tracker finalized.")

class MockBattle:
    def __init__(self):
        self.state = type('obj', (object,), {
            "armies_dict": {},
            "round_num": 0,
            "battle_stats": {},
            "universe_rules": None,
            "tracker": MockTracker() # Fix for finalization
        })()
        self.is_finished = False
        self.participating_fleets = set()
        self.pre_battle_counts = {} # Fix for telemetry
        self.participating_armies = set()
        self.json_file = None
        self.log_file = None

print("--- Verifying Live Integration ---")
ctx = MockContext()
bm = BattleManager(context=ctx)

# Creates Armies
u1 = MockUnit("Empire Ship", "Empire")
u1.add_weapon("Laser", 20.0, 1.0)
u2 = MockUnit("Rebel Ship", "Rebels")
u2.add_weapon("Blaster", 15.0, 1.0)

battle = MockBattle()
battle.state.armies_dict = {
    "Empire": [u1],
    "Rebels": [u2]
}

bm.active_battles["TestLoc"] = battle

print("Processing Active Battles...")
bm.process_active_battles()

if battle.is_finished:
    print("SUCCESS: Battle resolved.")
    # Check if Rust log appeared (MockContext prints it)
else:
    print("FAILURE: Battle did not finish.")
