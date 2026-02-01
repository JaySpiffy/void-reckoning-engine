import sys
import os
import json

# Add source path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.combat.tactical_engine import resolve_real_time_combat
from src.combat.combat_state import CombatState
from src.models.unit import Unit, Ship
from src.combat.real_time.formation_manager import Formation
from src.core import balance as bal
from src.core.universe_data import UniverseDataManager

class MockFaction:
    def __init__(self, name):
        self.name = name

def run_verification():
    print("=== Advanced Combat Verification ===")
    
    # 1. Setup Units
    # Faction A: Space Fleet in Line of Battle
    # Faction B: Land Army using Charge/Rally
    
    # Inject Ability Definition
    udm = UniverseDataManager.get_instance()
    # Force load base database first
    ability_db = udm.get_ability_database()
    ability_db["Ability_Charge"] = {
        "name": "Charge",
        "payload_type": "charge", # Must match AbilityManager handler
        "cost": {},
        "duration": 5,
        "cooldown": 20
    }
    
    units_a = []
    for i in range(5):
        # name, ma, md, hp, armor, damage, abilities
        s = Ship(f"Battlecruiser A{i}", 50, 40, 5000, 10, 20, {}, faction="Imperium", cost=5000)
        s.grid_x = 10 + i * 5
        s.grid_y = 50
        # Add Formation
        s.formations = [] 
        units_a.append(s)
        
    # Create Formation Manually
    form_a = Formation(units_a, formation_type="Line of Battle")
    for u in units_a:
        u.formations = [form_a]
        # Add Broadside Ability (as list or dict logic, standard is dict now)
        u.abilities = {"Ability_Broadside_Barrage": True}
        u.ability_cooldowns = {"Ability_Broadside_Barrage": 0}

    units_b = []
    for i in range(10):
        # name, ma, md, hp, armor, damage, abilities
        u = Unit(f"Shock Trooper B{i}", 40, 30, 1000, 10, 10, {}, faction="Orks", cost=200)
        u.base_leadership = 100
        u.morale_current = 100
        u.grid_x = 30
        u.grid_y = 50 + i * 2
        u.movement_points = 5
        # Add Abilities
        u.abilities = {"Ability_Charge": True, "Ability_Rally": True}
        u.ability_cooldowns = {"Ability_Charge": 0, "Ability_Rally": 0}
        units_b.append(u)
        
    armies = {"Imperium": units_a, "Orks": units_b}
    
    # 2. Run Simulation
    log_file = "verify_combat.json"
    print("Running simulation...")
    
    # Inject Mechanics Engine Mock? Not strictly needed if we just test Phases.
    # We use resolve_real_time_combat which uses phases.
    
    winner, survivors, sim_time, stats = resolve_real_time_combat(
        armies, 
        silent=False, 
        max_time=20.0, # Short run
        json_log_file=log_file
    )
    
    print(f"Simulation ended. Winner: {winner}")
    
    # 3. Validation
    # Check if formation modifiers were applied? 
    # Hard to see internal state from outside, but we can check if abilities were used in logs?
    
    # Check ability usage in JSON log (snapshot or event log)
    # The combat state is not returned directly, but we can inspect the log file?
    # Or better, we can monkey-patch or inspect the objects since we have references!
    
    print("\n--- Validation Checks ---")
    
    # Check Formation modifiers on ship
    mods = units_a[0].formations[0].get_modifiers()
    print(f"Formation Type: {units_a[0].formations[0].formation_type}")
    print(f"Modifiers: {mods}")
    
    if mods.get("damage_mult") == 1.15:
        print("[PASS] Line of Battle damage bonus verified")
    else:
        print("[FAIL] Line of Battle damage bonus missing")
        
    # Check if Charge was cast by reading the JSON log
    has_charge = False
    
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            try:
                logs = json.load(f)
                # Parse logs for "Ability Activated" or similar events
                # Logs structure might be list of dicts or dict with "combat_log" list
                events = logs.get("events", logs.get("combat_log", [])) # Tracker uses 'events' key often
                for entry in events:
                    msg = entry.get("description", entry.get("message", ""))
                    if not msg and "result" in entry:
                         msg = entry["result"].get("description", "")
                    
                    # print(f"DEBUG SCAN: {msg}") 
                    if "ability" in str(entry).lower() or "charge" in msg.lower():
                        print(f"DEBUG_EVENT: {msg}")

                    if "Charge!" in msg or ("Charge" in msg and "Ability" in entry.get("event_type", "")):
                        has_charge = True
                        print(f"[PASS] Log Confirmation: {msg}")
                        break
            except Exception as e:
                print(f"[ERROR] Failed to parse log: {e}")

    if not has_charge:
         print("[FAIL] No 'Charge' event found in combat logs.")

    # Clean up
    # if os.path.exists(log_file):
    #    os.remove(log_file)
        
    # if os.path.exists(log_file.replace(".json", "_par.html")):
    #     os.remove(log_file.replace(".json", "_par.html"))

if __name__ == "__main__":
    run_verification()
