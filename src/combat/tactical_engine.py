import random
import hashlib
import math
import os
from src.core import balance as bal
from src.combat.tactical_grid import TacticalGrid
from src.combat.combat_tracker import CombatTracker
from src.combat.combat_utils import calculate_mitigation_v4, apply_doctrine_modifiers
from src.combat.phase_executor import execute_phase_sequence, build_phase_context
from src.utils.profiler import profile_method
from typing import Optional

from src.utils.rng_manager import get_stream, RNGManager
from src.combat.combat_state import CombatState
from src.combat.tactical.gpu_tracker import GPUTracker
from src.core import gpu_utils


# Extracted Components
from src.combat.tactical.target_selector import TargetSelector
from src.combat.tactical.movement_calculator import MovementCalculator
from src.combat.tactical.salvage_processor import SalvageProcessor

# Legacy compatibility
def init_tactical_rng(seed: Optional[int] = None):
    RNGManager.get_instance().set_seed("tactical", seed)

@profile_method
def select_target_by_doctrine(attacker, enemies, doctrine, grid):
    """
    Selects the best target based on combat doctrine and tactical roles (Phase 7).
    Delegates to TargetSelector.
    """
    return TargetSelector.select_target_by_doctrine(attacker, enemies, doctrine, grid)

def calculate_movement_vector(unit, target, doctrine, grid):
    """
    Calculates movement delta (dx, dy) based on doctrine.
    Delegates to MovementCalculator.
    """
    return MovementCalculator.calculate_movement_vector(unit, target, doctrine, grid)

@profile_method
def initialize_battle_state(armies_dict, json_log_file=None, faction_doctrines=None, faction_metadata=None, location_name: Optional[str] = None, universe_rules=None, mechanics_engine=None, telemetry_collector=None, defender_factions: Optional[set] = None, combat_domain=None):
    """
    Initializes the persistent state for a multi-faction fleet engagement.
    Delegates to CombatState (Item 3.2).
    """
    from src.combat.combat_state import CombatState
    
    state = CombatState(armies_dict, faction_doctrines or {}, faction_metadata or {}, universe_rules=universe_rules, defender_factions=defender_factions)
    
    # [GPU ACCELERATION INITIALIZATION]
    # Check for GPU availability and initialize tracker if possible
    # [GPU ACCELERATION INITIALIZATION]
    # Check for GPU/Vectorization availability and initialize tracker if possible
    if gpu_utils.is_vectorization_enabled():
        all_units = []
        for units in armies_dict.values():
            all_units.extend(units)
        
        # Attach tracker to state (monkey-patching or ideally state should handle it)
        # For now, we attach it as an attribute
        state.gpu_tracker = GPUTracker()
        state.gpu_tracker.initialize(all_units)
        
        # Link to Grid if it exists in state
        if hasattr(state, 'grid') and state.grid:
            state.grid.gpu_tracker = state.gpu_tracker
            
        # log
        # print(f" > [GPU] Accelerated Combat Enabled: {gpu_utils.get_xp().__name__}")

    state.initialize_battle(
        json_log_file=json_log_file,
        location_name=location_name,
        telemetry_collector=telemetry_collector,
        mechanics_engine=mechanics_engine,
        combat_domain=combat_domain
    )
    
    # Re-link grid just in case initialize_battle created a new one
    if hasattr(state, 'gpu_tracker') and hasattr(state, 'grid') and state.grid:
         state.grid.gpu_tracker = state.gpu_tracker
    
    return state

@profile_method
def execute_battle_round(battle_state, detailed_log_file=None):
    """
    Executes a SINGLE round of combat for a protracted battle state.
    Orchestrates phases via the PhaseExecutor.
    """
    manager = battle_state
    tracker = manager.tracker
    
    manager.round_num += 1
    round_num = manager.round_num
    
    # [FIX] Update simulation time to allow cooldowns to function
    # Assuming 1 Round = ~5-10 seconds of "simulated" time for Ability Cooldowns
    time_per_round = 5.0 
    if hasattr(manager, "total_sim_time"):
        manager.total_sim_time += time_per_round
        
    tracker.start_round(round_num)
    
    # 1. Collect Active Units & Snapshot
    active_units_list = []
    for f, units in manager.armies_dict.items():
        for u in units:
            if u.is_alive() and getattr(u, 'is_deployed', True):
                tracker.log_snapshot(u)
                active_units_list.append(u)
                
    # [GPU Update Hook]
    if hasattr(manager, 'gpu_tracker') and manager.gpu_tracker:
        manager.gpu_tracker.update_positions(active_units_list)

    # 2. Build Context
    context = build_phase_context(manager, round_num, detailed_log_file)
    context["manager"] = manager
    # [GPU Acceleration] Inject GPU Tracker into phase context
    context["gpu_tracker"] = getattr(manager, 'gpu_tracker', None)
    
    # 3. Dynamic Phase Execution
    if manager.universe_rules:
        phases = manager.universe_rules.register_phases()
        phase_order = manager.universe_rules.get_phase_order()
        context["universe_rules"] = manager.universe_rules
    else:
        # Default Fallback Phase Order
        # Default Fallback Phase Order
        from src.combat.combat_phases import (
            MovementPhase, ShootingPhase, AbilityPhase, MeleePhase, MoralePhase, OrbitalSupportPhase
        )
        phases = [
            OrbitalSupportPhase(),
            AbilityPhase(),
            MovementPhase(),
            ShootingPhase(),
            MeleePhase(),
            MoralePhase()
        ]
        phase_order = ['orbital_support', 'ability', 'movement', 'shooting', 'melee', 'morale']
        
    # Phase 250: Track damage delta for stalemate detection
    damage_before = sum(stats.get("total_damage_dealt", 0) for stats in manager.battle_stats.values())
    alive_before = sum(1 for units in manager.armies_dict.values() for u in units if u.is_alive())
    
    execute_phase_sequence(phases, phase_order, context)

    damage_after = sum(stats.get("total_damage_dealt", 0) for stats in manager.battle_stats.values())
    alive_after = sum(1 for units in manager.armies_dict.values() for u in units if u.is_alive())
    
    if damage_after > damage_before:
        manager.rounds_since_last_damage = 0
    else:
        manager.rounds_since_last_damage += 1
        
    if alive_after < alive_before:
        manager.rounds_since_last_kill = 0
    else:
        if hasattr(manager, 'rounds_since_last_kill'):
             manager.rounds_since_last_kill += 1

    # 4. Post-Round Cleanup
    _cleanup_round(manager, context.get("active_units", []), detailed_log_file)
    
    # [ATOMIC_COMBAT] Remove units that successfully retreated
    manager.remove_retreating_units()
    
    return manager.check_victory_conditions()

def _cleanup_round(manager, active_units_at_start, detailed_log_file=None):
    """
    Handles unit destruction tracking, reanimation hooks, and salvage registration.
    """
    armies_dict = manager.armies_dict
    
    # Award survival XP (approx 1 XP per second of active combat)
    from src.combat.ability_manager import AbilityManager
    ab_manager = getattr(manager, 'ability_manager', None)
    if not ab_manager:
        # Fallback to UniverseDataManager if manager doesn't have it yet
        from src.core.universe_data import UniverseDataManager
        registry = UniverseDataManager.get_instance().get_ability_database()
        ab_manager = AbilityManager(registry)
    
    context = {"ability_manager": ab_manager, "battle_state": manager}
    
    # Collect all living units from all armies
    living_units = [u for units in armies_dict.values() for u in units if u.is_alive()]

    from src.core.balance import UNIT_XP_AWARD_SURVIVAL_ROUND
    for u in living_units:
        u.gain_xp(UNIT_XP_AWARD_SURVIVAL_ROUND, context) # Survival XP per round

    for u, f in active_units_at_start:
        if not u.is_alive():
            # Unit died this round!
            killer = getattr(u, 'last_attacker_faction', None)
            if not killer:
                 enemy_factions = [ef for ef in armies_dict if ef != f]
                 if enemy_factions: killer = enemy_factions[0]
            
            if killer:
                manager.track_unit_destruction(f, u, killer)
                
                # MECHANICS HOOK: Unit Death
                if hasattr(manager, 'mechanics_engine') and manager.mechanics_engine:
                     death_context = {
                         "unit": u,
                         "killer": killer,
                         "faction": manager.mechanics_engine.engine.factions.get(f),
                         "battle_state": manager
                     }
                     manager.mechanics_engine.apply_mechanics(f, "on_unit_death", death_context)
                     
                     # Check for Reanimation
                     if death_context.get("revived", False):
                          u.is_destroyed = False
                          if u.current_hp <= 0: u.current_hp = 1
                          if detailed_log_file:
                               msg = f"  [MECHANIC] {u.name} REANIMATED protocols active!\n"
                               try:
                                   if isinstance(detailed_log_file, str):
                                        with open(detailed_log_file, "a", encoding='utf-8') as log:
                                             log.write(msg)
                                   else:
                                        detailed_log_file.write(msg)
                               except: pass
                      
                     # Trigger for Killer's faction (e.g. Conviction)
                     killer_faction_obj = manager.mechanics_engine.engine.factions.get(killer)
                     if killer_faction_obj:
                          killer_context = {
                              "unit": u,
                              "killer": killer,
                              "faction": killer_faction_obj,
                              "victim_faction": f,
                              "battle_state": manager
                          }
                          manager.mechanics_engine.apply_mechanics(killer, "on_unit_death", killer_context)

    
    return manager.check_victory_conditions()

def resolve_fleet_engagement(armies_dict, silent=False, detailed_log_file=None, max_rounds=5000, json_log_file=None, universe_rules=None, factions_dict=None, mechanics_engine=None, generate_replay=False, replay_output_path=None):
    """
    Executes a multi-faction fleet engagement on a 100x100 Tactical Grid.
    """
    if not silent:
        print(f"\n--- FLEET ENGAGEMENT STARTED (Tactical Grid) ---")
        total_units = sum(len(u) for u in armies_dict.values())
        print(f"Total Ships: {total_units} across {len(armies_dict)} Factions")
    
    if universe_rules is None:
        try:
            from universes.void_reckoning.combat_phases import EternalCrusadeCombatRules
            universe_rules = EternalCrusadeCombatRules()
        except ImportError:
            pass

    state = initialize_battle_state(armies_dict, json_log_file, universe_rules=universe_rules, mechanics_engine=mechanics_engine)
    winner = "Draw"
    survivors = 0
    rounds = 0
    
    while True:
        winner, survivors, is_finished = execute_battle_round(state, detailed_log_file)
        rounds = state.round_num
        
        if not silent and (rounds % 10 == 0):
             active_count = sum(1 for f, units in armies_dict.items() for u in units if u.is_alive())
             print(f"Round {rounds}: {active_count} units active")
        
        if is_finished:
            break
            
        if rounds >= max_rounds:
            if not silent: print(f"Max rounds ({max_rounds}) reached. Forcing decision...")
            is_finished = True
            
            # Force Victory Check
            winner, survivors, is_finished = state.check_victory_conditions(force_result=True)
            # If check_victory_conditions STILL returns Draw (e.g. 0 damage), force random or defender?
            # check_victory_conditions has Pyrrhic logic for Draw, so it should handle it.
            break
            
    # Calculate total intel points earned post-battle
    for faction in armies_dict:
        tech_count = len(state.battle_stats[faction]["enemy_tech_encountered"])
        unit_count = len(state.battle_stats[faction]["enemy_units_analyzed"])
        intel_earned = (tech_count * 100) + (unit_count * 10)
        state.battle_stats[faction]["intel_points_earned"] = intel_earned
        
        # Award intel to faction state if provided
        if factions_dict and faction in factions_dict:
            f_obj = factions_dict[faction]
            if hasattr(f_obj, 'earn_intel') and intel_earned > 0:
                f_obj.earn_intel(intel_earned, source="combat")

        # Process Wreckage / Salvage
        process_battle_salvage(state, factions_dict)

    state.tracker.finalize(winner, rounds, armies_dict, battle_stats=state.battle_stats)
    
    # [PHASE 18.2] Generate Replay & Human-Readable Log
    if json_log_file:
        try:
            from src.combat.reporting.real_time_replay import RealTimeReplayGenerator
            gen = RealTimeReplayGenerator(state, winner_override=winner)
            gen.export_json(json_log_file)
            
            # Also auto-generate HTML summary
            html_path = json_log_file.replace(".json", "_par.html")
            gen.export_html_summary(html_path)
            
            # Generate Human-Readable TXT Log
            txt_path = json_log_file.replace(".json", ".txt")
            gen.export_text_log(txt_path)
            
            if not silent: print(f"PAR Generated: {html_path}, Log: {txt_path}")
        except Exception as e:
            print(f"Failed to generate combat replay logs: {e}")

    if hasattr(state, 'tracker') and state.tracker:
        state.tracker.cleanup()

    return (winner, survivors, rounds, state.battle_stats)

def process_battle_salvage(state, factions_dict=None):
    """
    Hook to capture destroyed units (wreckage), compute salvage quality,
    and register salvaged blueprints via BlueprintRegistry.
    Delegates to SalvageProcessor.
    """
    SalvageProcessor.process_battle_salvage(state, factions_dict)

def resolve_real_time_combat(armies_dict, silent=False, max_time=60.0, dt=0.2, 
                             json_log_file=None, universe_rules=None, 
                             factions_dict=None, mechanics_engine=None, combat_domain=None):
    """
    Executes a real-time combat simulation until a victory condition is met or max_time is reached.
    """
    if not silent:
        print(f"\n--- REAL-TIME COMBAT STARTED ---")
        total_units = sum(len(u) for u in armies_dict.values())
        print(f"Total Units: {total_units} across {len(armies_dict)} Factions")

    state = initialize_battle_state(armies_dict, json_log_file, universe_rules=universe_rules, mechanics_engine=mechanics_engine, combat_domain=combat_domain)
    
    # [PHASE 18.1] Ensure replay buffers are clear
    state.snapshots = []
    state.event_log = []
    
    winner = "Draw"
    survivors = 0
    sim_time = 0.0
    
    while True:
        state.real_time_update(dt)
        sim_time += dt
        
        # Check victory every tick (or optimized interval)
        winner, survivors, is_finished = state.check_victory_conditions()
        
        if is_finished or sim_time >= max_time:
            if sim_time >= max_time and not is_finished:
                if not silent: print(f"Combat timed out after {max_time}s")
                winner, survivors, is_finished = state.check_victory_conditions(force_result=True)
            break
            
        if not silent and (int(sim_time) % 60 == 0 and (sim_time % 1.0 < dt)):
             active_count = sum(1 for f, units in armies_dict.items() for u in units if u.is_alive())
             print(f"T+{int(sim_time)}s: {active_count} units active")

    # Generate PAR and Replay
    if json_log_file:
        from src.combat.reporting.real_time_replay import RealTimeReplayGenerator
        gen = RealTimeReplayGenerator(state, winner_override=winner)
        gen.export_json(json_log_file)
        
        # Also auto-generate HTML summary
        html_path = json_log_file.replace(".json", "_par.html")
        gen.export_html_summary(html_path)
        
        # [REDESIGN PHASE 3] Generate Human-Readable TXT Log
        txt_path = json_log_file.replace(".json", ".txt")
        gen.export_text_log(txt_path)
        
        if not silent: print(f"PAR Generated: {html_path}, Log: {txt_path}")

    # Process Wreckage / Salvage (Reuse existing logic)
    process_battle_salvage(state, factions_dict)

    return (winner, survivors, int(sim_time), state.battle_stats)
