
import json
import os
import sys
import random
import copy

# Add project root to path
sys.path.append(os.getcwd())

from src.combat.tactical_engine import resolve_fleet_engagement, initialize_battle_state, execute_battle_round
from src.utils.unit_parser import load_all_units
from src.factories.unit_factory import UnitFactory
from src.core.config import REPORTS_DIR

def build_space_army(pool, count, faction_name):
    army = []
    ship_keywords = ["Ship", "Cruiser", "Battleship", "Escort", "Frigate", "Destroyer", "Titan"]
    valid_bps = [bp for bp in pool if getattr(bp, "is_ship", lambda: False)() or any(k in getattr(bp, 'name', '') for k in ship_keywords)]
    
    if not valid_bps:
        print(f"Warning: No space units found for {faction_name}")
        return []

    distinct_classes = sorted(list(set(getattr(bp, 'type', 'unknown') for bp in valid_bps)))
    print(f"  - Found {len(distinct_classes)} space classes for {faction_name}: {distinct_classes}")
    
    for i in range(count):
        bp = valid_bps[i % len(valid_bps)]
        unit = UnitFactory.create_from_blueprint(bp, faction_name)
        unit.name = f"{bp.name} #{i+1}"
        army.append(unit)
    return army

def build_ground_army(count, faction_name):
    """Explicitly builds army from unit_classes.json to ensure variety."""
    classes_path = "data/ground/unit_classes.json"
    with open(classes_path, 'r') as f:
        data = json.load(f)
    
    ground_classes = data["classes"]
    army = []
    
    print(f"  - Generating ground army from {len(ground_classes)} classes: {[c['name'] for c in ground_classes]}")
    
    for i in range(count):
        c_data = ground_classes[i % len(ground_classes)]
        stats = c_data["stats"]
        
        # Create a mock blueprint that UnitFactory can understand
        class MockBP:
            def __init__(self, name, stats, id):
                self.name = name
                self.base_ma = stats.get("melee_attack", 50)
                self.base_md = stats.get("melee_defense", 50)
                self.base_hp = stats.get("hp", 100)
                self.armor = stats.get("armor", 0)
                self.base_damage = stats.get("weapon_strength", 10)
                self.abilities = {"Tags": c_data.get("attributes", ["infantry"])}
                self.authentic_weapons = []
                self.traits = [c_data["id"]]
                self.cost = 100
                self.type = c_data["id"] # Use id as type for diagnostic
                self.unit_class = c_data["id"]
                
        bp = MockBP(c_data["name"], stats, c_data["id"])
        unit = UnitFactory.create_from_blueprint(bp, faction_name)
        unit.domain = "ground"
        unit.name = f"{c_data['name']} #{i+1}"
        army.append(unit)
        
    return army

def run_stress_test(domain="space", unit_count=1000):
    print(f"\n>>> Starting MASS COMBAT STRESS TEST: {domain.upper()} ({unit_count} vs {unit_count})")
    
    # 1. Load Data
    total_loaded = load_all_units()
    factions = sorted(list(total_loaded.keys()))
    if len(factions) < 2:
        print("Error: Not enough factions loaded.")
        return
        
    f1_name = factions[0]
    f2_name = factions[1]
    
    print(f"Generating Armies for {f1_name} and {f2_name}...")
    if domain == "space":
        army1 = build_space_army(total_loaded[f1_name], unit_count, f1_name)
        army2 = build_space_army(total_loaded[f2_name], unit_count, f2_name)
    else:
        army1 = build_ground_army(unit_count, f1_name)
        army2 = build_ground_army(unit_count, f2_name)
    
    if len(army1) == 0 or len(army2) == 0:
        print(f"Error: Could not generate enough {domain} units.")
        return

    # Diagnostic: Check Scaling for each class
    print("\n--- Scaling Diagnostics (Sample Units) ---")
    seen_classes = set()
    for u in army1:
        u_class = getattr(u, 'unit_type', 'unknown') if domain == "space" else getattr(u, 'unit_class', 'unknown')
        if u_class not in seen_classes:
            weapon_str = "None"
            if len(u.components) > 0 and u.components[0].type == "Weapon":
                weapon_str = f"{u.components[0].stats.get('S', u.components[0].stats.get('strength', u.components[0].stats.get('damage', 0)))}"
            print(f"  - [{u.faction}] {u.name}: HP={u.max_hp}, Str={weapon_str}")
            seen_classes.add(u_class)
    print("-------------------------------------------\n")

    print(f"Total Units Generated: {len(army1) + len(army2)}")
    armies_dict = {f1_name: army1, f2_name: army2}
    
    # 2. Setup Battle
    log_file = os.path.join(REPORTS_DIR, f"stress_test_{domain}.txt")
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
    
    # Clear old log file
    with open(log_file, "w", encoding='utf-8') as f:
        f.write(f"--- Stress Test: {domain.upper()} ---\n")
        
    print(f"Initializing {domain} Battle State...")
    combat_domain = "space" if domain == "space" else "ground"
    from src.combat.cross_universe_handler import CrossUniverseCombatHandler
    rules = CrossUniverseCombatHandler.load_universe_combat_rules("void_reckoning")
    
    state = initialize_battle_state(armies_dict, universe_rules=rules, combat_domain=combat_domain)
    
    from src.combat.tactical_engine import execute_real_time_battle
    
    print(f"Starting Real-Time Simulation (Max Duration: 90s)...")
    total_duration = 90.0
    current_sim_time = 0.0
    winner = "Ongoing"
    survivors = unit_count * 2
    is_finished = False

    while current_sim_time < total_duration:
        winner, survivors, is_finished = execute_real_time_battle(state, duration=1.0, dt=0.1, detailed_log_file=log_file)
        current_sim_time += 1.0
        
        active_count = sum(1 for f, units in armies_dict.items() for u in units if u.is_alive())
        projectiles_count = len(state.realtime_manager.projectile_manager.projectiles) if hasattr(state.realtime_manager, 'projectile_manager') else 0
        
        # Log status every second for "live run" feel
        print(f"  T+{int(current_sim_time):02}s | Units: {active_count:4} | Projectiles: {projectiles_count:3} | F1: {sum(1 for u in army1 if u.is_alive()):4} vs F2: {sum(1 for u in army2 if u.is_alive()):4}")
        
        if is_finished:
            break

    rounds = int(current_sim_time) # Map sim time to "rounds" for reporting

    # 3. Report Results
    print(f"\n--- {domain.upper()} Results ---")
    print(f"Winner: {winner}")
    print(f"Rounds: {rounds}")
    print(f"Survivors: {survivors}")
    
    total_start = len(army1) + len(army2)
    total_lost = total_start - survivors
    print(f"Casualties: {total_lost} / {total_start} ({(total_lost/total_start)*100:.1f}%)")
    
    if total_lost > 0:
        print(">>> CONFIRMED: Units are dying.")
    else:
        print(">>> WARNING: Zero casualties! Check range/accuracy.")

if __name__ == "__main__":
    # Test Space
    try:
        run_stress_test(domain="space", unit_count=100)
    except Exception as e:
        print(f"Space Test Failed: {e}")
        import traceback
        traceback.print_exc()
        
    # Test Ground
    try:
        run_stress_test(domain="ground", unit_count=100)
    except Exception as e:
        print(f"Ground Test Failed: {e}")
        import traceback
        traceback.print_exc()
