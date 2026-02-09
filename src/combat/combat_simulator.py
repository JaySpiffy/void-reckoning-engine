"""
Combat Simulator Component (Facade)
===================================
This module now serves as a facade for the decomposed combat system.
It re-exports key functions and classes from specialized sub-modules.

Modules:
- combat_utils: Data loading and math helpers
- combat_tracker: Logging and telemetry
- combat_phases: Specific phase logic (Psychic, Boarding, Melee)
- tactical_engine: New Grid-based Combat Engine
- combat_legacy: Old-style simulation runner and CLI

Legacy support:
re-exports `resolve_fleet_engagement` (New) and `resolve_fleet_engagement_OLD` (Legacy).
"""

import sys
import os
import random
import argparse
import copy

# Re-export Models (Crucial for external dependencies)
from src.models.unit import Unit, Ship, Regiment, Component
from src.factories.unit_factory import UnitFactory

# Re-export Data Loading & Utils
from src.combat.combat_utils import (
    load_traits, 
    find_unit_by_name, 
    check_keywords_attack, 
    calculate_mitigation_v4,
    POINTS_DB
)
from src.utils.unit_parser import load_all_units, parse_unit_file

# Re-export Tracker
from src.combat.combat_tracker import CombatTracker

# Re-export Core Engines
from src.combat.tactical_engine import (
    resolve_fleet_engagement, 
    initialize_battle_state, 
    execute_battle_round,
    process_battle_salvage
)
from src.combat.rust_tactical_engine import RustTacticalEngine

from src.core.config import get_universe_config, REPORTS_DIR
from typing import Optional, Dict, List, Any, Set

from src.combat.cross_universe_handler import CrossUniverseCombatHandler

def resolve_fleet_engagement_rust(armies_dict: Dict[str, List[Any]], silent=False) -> (str, int, int, Any):
    """
    Resolves combat using the Rust Tactical Engine.
    """
    engine = RustTacticalEngine()
    if not engine.rust_engine:
        print("Rust Engine unavailable, falling back to Python...")
        return resolve_fleet_engagement(armies_dict, silent=silent, use_rust=False)
        
    engine.initialize_battle(armies_dict)
    
    from src.core.constants import MAX_COMBAT_ROUNDS
    
    rounds = 0
    max_rounds = MAX_COMBAT_ROUNDS
    
    while rounds < max_rounds:
        cont = engine.resolve_round()
        rounds += 1
        if not cont: break
        
    # Final Sync
    engine.sync_back_to_python(armies_dict)
    
    # Check Winner
    alive_counts = {f: sum(1 for u in units if not getattr(u, 'is_destroyed', False)) for f, units in armies_dict.items()}
    survivors = sum(alive_counts.values())
    alive_factions = [f for f, count in alive_counts.items() if count > 0]
    
    winner = alive_factions[0] if len(alive_factions) == 1 else "Draw"
    
    if not silent:
        print(f"[Rust] Battle Result: {winner} Wins in {rounds} rounds. Survivors: {survivors}")
        
    return winner, survivors, rounds, {}

def detect_universe_mix(armies_dict: Dict[str, List[Unit]]) -> Dict[str, Any]:
    """Delegates to CrossUniverseCombatHandler."""
    return CrossUniverseCombatHandler.detect_universe_mix(armies_dict)

def translate_army_to_universe(army: List[Unit], target_universe: str) -> List[Unit]:
    """Delegates to CrossUniverseCombatHandler."""
    return CrossUniverseCombatHandler.translate_army_to_universe(army, target_universe)

def load_universe_combat_rules(universe_name: str = "void_reckoning"):
    """Delegates to CrossUniverseCombatHandler."""
    return CrossUniverseCombatHandler.load_universe_combat_rules(universe_name)

def resolve_fleet_engagement_with_universe(armies_dict, universe_name=None, 
                                          cross_universe=False, profile_memory=False, use_rust=False, **kwargs):
    """Delegates to CrossUniverseCombatHandler."""
    if use_rust:
        return resolve_fleet_engagement_rust(armies_dict, silent=kwargs.get('silent', False))
        
    return CrossUniverseCombatHandler.resolve_fleet_engagement_with_universe(
        armies_dict, universe_name, cross_universe, profile_memory, **kwargs
    )

def run_cross_universe_duel(unit1_path: str, unit2_path: str, battle_universe: str = None):
    """Delegates to CrossUniverseCombatHandler."""
    return CrossUniverseCombatHandler.run_cross_universe_duel(unit1_path, unit2_path, battle_universe)

def run_cross_universe_battle(config_path: str, profile_memory: bool = False):
    """Delegates to CrossUniverseCombatHandler."""
    return CrossUniverseCombatHandler.run_cross_universe_battle(config_path, profile_memory)

def run_grand_royale(points_limit=20000, batch_size=1):
    """
    Runs the Grand Royale mode using the Atomic/Tactical Engine.
    Replaces legacy combat logic with grid-based resolution.
    """
    total_loaded = load_all_units()
    valid_factions = {f: units for f, units in total_loaded.items() if len(units) > 0}
    
    if len(valid_factions) < 2: return

    print(f"\n=== PREPARING GRAND ROYALE (Max {points_limit} Pts) [ATOMIC ENGINE] ===")
    global_stats = {f: {"wins": 0} for f in valid_factions}
    
    # Ensure reports dir exists
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        
    log_path = os.path.join(REPORTS_DIR, "grand_royale_stats.csv")
    
    with open(log_path, "w") as f: f.write("Iteration,Winner,Survivors,Rounds,StartUnits\n")
            
    for i in range(batch_size):
        if i % 1 == 0: print(f"Processing Battle {i+1}/{batch_size}...")
        
        armies_dict = {}
        for faction, pool in valid_factions.items():
            if len(pool) < 2: continue
            army = []
            current_points = 0
            attempts = 0
            while current_points < points_limit and attempts < 1000:
                base = random.choice(pool)
                # Filter expensive units if close to calc
                if base.cost > (points_limit - current_points): 
                     attempts += 1
                     continue

                if current_points + base.cost <= points_limit:
                    new_u = base.clone() if hasattr(base, 'clone') else None
                    if not new_u:
                         # Manual Clone if method missing (Backup)
                         if base.is_ship():
                              new_u = Ship(base.name, base.base_ma, base.base_md, base.base_hp, base.armor, base.base_damage, base.abilities, faction=faction, authentic_weapons=base.authentic_weapons, shield=getattr(base, 'shield_max',0), traits=base.traits, cost=base.cost)
                         else:
                              new_u = UnitFactory.create_from_blueprint(base, faction)
                         new_u.components = [] # Reset components to rebrand
                    
                    new_u.name = f"{base.name}"
                    c_roll = random.random()
                    new_u.cover = "None"
                    if c_roll < 0.20: new_u.cover = "Heavy"
                    elif c_roll < 0.50: new_u.cover = "Light"
                    
                    army.append(new_u)
                    current_points += base.cost
                    attempts = 0
                else: attempts += 1
            armies_dict[faction] = army
        
        is_silent = (batch_size > 1)
        detailed_log_file = None
        if i == 0:
            detailed_log_file = os.path.join(REPORTS_DIR, "combat_log_detailed.txt")
            with open(detailed_log_file, 'w') as f: f.write("")
        
        # USE ATOMIC ENGINE
        # We use standard void_reckoning rules for now as default foundation
        rules = load_universe_combat_rules("void_reckoning")
        winner, survivors, rounds, stats = resolve_fleet_engagement(
            armies_dict, 
            silent=is_silent, 
            detailed_log_file=detailed_log_file, 
            universe_rules=rules
        )
        
        with open(log_path, "a") as f:
             f.write(f"{i+1},{winner},{survivors},{rounds},{len(armies_dict.get(winner, [])) if winner!='Draw' else 0}\n")
        if winner in global_stats: global_stats[winner]["wins"] += 1

    if batch_size > 1:
        print("\n=== AGGREGATE RESULTS ===")
        for f, data in sorted(global_stats.items(), key=lambda x: x[1]['wins'], reverse=True):
            win_rate = (data['wins'] / batch_size) * 100
            print(f"{f}: {data['wins']} Wins ({win_rate:.1f}%)")

def run_fleet_battle(f1_name, f2_name, fleet_size=20, cross_universe=False, profile_memory=False):
    print(f"Loading Fleet Data for {f1_name} vs {f2_name} ({fleet_size} ships/side)...")
    total_loaded = load_all_units()

    def build_fleet(faction_name, count):
        if faction_name not in total_loaded:
            print(f"Error: Faction '{faction_name}' not found.")
            return []
        
        valid_units = [u for u in total_loaded[faction_name] if "Ship" in getattr(u, 'keywords', []) or "Vehicle" in getattr(u, 'tags', []) or getattr(u, 'hp', 0) > 500] 
        if not valid_units: valid_units = total_loaded[faction_name]
        if not valid_units: return []

        fleet = []
        for _ in range(count):
            bp = random.choice(valid_units)
            # Basic copy
            new_u = Ship(
                bp.name, bp.base_ma, bp.base_md, bp.base_hp, bp.armor, bp.base_damage, bp.abilities, 
                faction=faction_name, authentic_weapons=bp.authentic_weapons, 
                shield=getattr(bp, 'shield_max', 0), traits=bp.traits, cost=bp.cost, 
                transport_capacity=getattr(bp, 'transport_capacity', 0),
                source_universe=getattr(bp, 'source_universe', None)
            )
            if hasattr(bp, 'components') and bp.components:
                 new_u.components = copy.deepcopy(bp.components)
                 # Update stats from components?
                 # No, base_stats in blueprint should already include component bonuses if patched.
                 # But Ship constructor resets to base_stats passed in args.
                 # bp.base_damage SHOULD reflect the patched value.
            
            fleet.append(new_u)
        return fleet

    f1_army = build_fleet(f1_name, fleet_size)
    f2_army = build_fleet(f2_name, fleet_size)

    if not f1_army or not f2_army: return

    armies_dict = {f1_name: f1_army, f2_name: f2_army}
    
    resolve_fleet_engagement_with_universe(
        armies_dict, 
        detailed_log_file=os.path.join(REPORTS_DIR, "fleet_battle_log.txt"),
        cross_universe=cross_universe,
        profile_memory=profile_memory
    )

def run_duel(unit1_name, unit2_name):
    """
    Runs a duel using the new Atomic Engine.
    """
    output_log = os.path.join(REPORTS_DIR, "duel_log.txt")
    all_units = load_all_units()
    u1_base = find_unit_by_name(all_units, unit1_name)
    u2_base = find_unit_by_name(all_units, unit2_name)
    
    if not u1_base or not u2_base:
        print("Error: Could not find one of the units.")
        return None
        
    # Manual deepish copy for duel
    p1 = UnitFactory.create_from_blueprint(u1_base, u1_base.faction)
    p2 = UnitFactory.create_from_blueprint(u2_base, u2_base.faction)
    p1.name = p1.name + " (Duelist)"
    p2.name = p2.name + " (Duelist)"

    armies_dict = {u1_base.faction: [p1], "Challenger": [p2]}
    
    rules = load_universe_combat_rules("void_reckoning")
    return resolve_fleet_engagement(
        armies_dict, 
        silent=False, 
        detailed_log_file=output_log,
        universe_rules=rules
    )

def parse_args():
    parser = argparse.ArgumentParser(description="Multi-Universe Combat Simulator")
    parser.add_argument("--unit1", help="Name of Unit 1", default=None)
    parser.add_argument("--unit2", help="Name of Unit 2", default=None)
    parser.add_argument("--mode", help="Mode: duel, royale, fleet", default="duel")
    parser.add_argument("--faction1", help="Faction 1 for Fleet Battle", default="Hegemony")
    parser.add_argument("--faction2", help="Faction 2 for Fleet Battle", default="Chaos_Undivided")
    parser.add_argument("--size", help="Fleet Size per Faction", type=int, default=200)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.mode == "royale":
        run_grand_royale(batch_size=1)
    elif args.mode == "fleet":
        run_fleet_battle(args.faction1, args.faction2, args.size)
    elif args.unit1 and args.unit2:
        run_duel(args.unit1, args.unit2)
    else:
        run_grand_royale(points_limit=20000, batch_size=10)
