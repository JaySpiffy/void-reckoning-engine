import math
import random
import os
from typing import Dict, Any, List, Optional
from src.core.interfaces import ICombatPhase
from src.utils.profiler import profile_method
from src.combat.combat_utils import calculate_mitigation_v4, apply_doctrine_modifiers
from src.combat.execution.weapon_executor import WeaponExecutor
from src.utils.rng_manager import get_stream
from src.combat.space_combat import resolve_boarding_phase
from src.combat.ground_combat import resolve_melee_phase as resolve_ground_melee
import logging
from src.core.gpu_utils import log_backend_usage, HAS_GPU

logger = logging.getLogger(__name__)

# Base Class
class CombatPhase(ICombatPhase):
    name: str = "generic"
    
    def execute(self, context: Dict[str, Any]) -> None:
        raise NotImplementedError

# --- specific phases ---

class MovementPhase(CombatPhase):
    name: str = "movement"
    
    @profile_method
    def execute(self, context: Dict[str, Any]) -> None:
        active_units = context.get("active_units", [])
        enemies_by_faction = context.get("enemies_by_faction", {})
        grid = context.get("grid")
        faction_doctrines = context.get("faction_doctrines", {})
        faction_metadata = context.get("faction_metadata", {})
        round_num = context.get("round_num", 1)
        detailed_log_file = context.get("detailed_log_file")
        manager = context.get("manager")
        universe_rules = context.get("universe_rules")
        
        # Lazy import to avoid circular dependency if tactical_engine imports this
        from src.combat.tactical_engine import select_target_by_doctrine, calculate_movement_vector

        indices = list(range(len(active_units)))
        get_stream("phases").shuffle(indices)
        shuffled_units = [active_units[i] for i in indices]
        
        # [GPU Acceleration] Batched Flow Field
        flow_field = {}
        tracker_ref = context.get("gpu_tracker") or context.get("tracker")
        if tracker_ref and hasattr(tracker_ref, "compute_flow_field"):
             # Compute for ALL units at start of phase (Snapshot Targeting)
             flow_field = tracker_ref.compute_flow_field()
             log_backend_usage("MovementPhase:FlowField", logger)
        else:
             logger.info("MovementPhase: Executing Legacy CPU Pathfinding")
        
        for u, f_name in shuffled_units:

            enemies = enemies_by_faction.get(f_name, [])
            if not enemies: continue
            
            doctrine = faction_doctrines.get(f_name, "CHARGE")
            f_meta = faction_metadata.get(f_name, {})
            f_doctrine = f_meta.get("faction_doctrine", "STANDARD")
            f_intensity = f_meta.get("intensity", 1.0)
            
            if hasattr(u, "recalc_stats"): u.recalc_stats()
            
            if manager and hasattr(manager, 'mechanics_engine') and manager.mechanics_engine:
                 manager.mechanics_engine.apply_mechanic_modifiers(f_name, [u])
            
            if universe_rules and hasattr(universe_rules, "apply_doctrine_modifiers"):
                f_mods = universe_rules.apply_doctrine_modifiers(u, doctrine, "MOVEMENT", f_doctrine, f_intensity)
            else:
                f_mods = apply_doctrine_modifiers(u, doctrine, "MOVEMENT", f_doctrine, f_intensity)
                
            if hasattr(u, "apply_temporary_modifiers"):
                u.apply_temporary_modifiers(f_mods)
                
            # [PHASE 30] Formation Speed Modifiers
            if hasattr(u, 'formations') and u.formations:
                form_speed_mult = u.formations[0].get_modifiers().get("movement_speed_mult", 1.0)
                # Apply as a multiplier to the current points for this turn
                u.movement_points *= form_speed_mult

            target, _ = select_target_by_doctrine(u, enemies, doctrine, grid)
            
            # [ADVANCED AI] Escort Logic
            # If no enemy target and unit is in DEFEND mode or is an Interdictor Escort
            if not target and (doctrine == "DEFEND" or "Interdictor" in getattr(u, 'tags', [])):
                 # Find friendly interdictors
                 for friend, faction in active_units:
                      if faction == f_name and friend != u:
                           if "Interdictor" in friend.tags or "Gravity_Well" in friend.abilities:
                                target = friend
                                break
            
            if not target: continue
            
            nearest = target 
            # Check Flow Field first
            dx, dy = 0, 0
            
            # [PHASE 6] Unit Directive Override
            # We must apply this BEFORE deciding between GPU/CPU logic so outcome is consistent
            if hasattr(u, 'tactical_directive') and u.tactical_directive and u.tactical_directive != "HOLD_GROUND":
                 directive = u.tactical_directive
                 if directive == "KITE": doctrine = "KITE"
                 elif directive == "CLOSE_QUARTERS": doctrine = "CHARGE"
            
            # [GPU Path]
            u_id = id(u)
            if u_id in flow_field:
                 gpu_dx, gpu_dy, gpu_dist = flow_field[u_id]
                 dist = gpu_dist # Update dist for logging/logic
                 
                 # Apply Doctrine Logic on CPU using GPU-derived data
                 if doctrine == "CHARGE":
                        dx, dy = gpu_dx, gpu_dy
                        # Check KITE preference override
                        if getattr(u, 'ranged_preference', False):
                             # Calculate dynamic max range
                             weapons = [c for c in u.components if c.type == "Weapon"]
                             max_range = max([c.weapon_stats.get("Range", 0) for c in weapons], default=0)
                             
                             if max_range > 5: 
                                  stop_dist = max_range * 0.9
                                  # Don't back up if charging, just stop at optimal range
                                  if dist <= stop_dist: dx, dy = 0, 0
                                  
                 elif doctrine == "KITE":
                        weapons = [c for c in u.components if c.type == "Weapon"]
                        max_range = max([c.weapon_stats.get("Range", 0) for c in weapons], default=0)
                        
                        if max_range <= 5: 
                            dx, dy = gpu_dx, gpu_dy
                        else:
                            stop_dist = max_range * 0.9
                            min_dist = max_range * 0.5
                            
                            if dist < min_dist: 
                                dx, dy = -gpu_dx, -gpu_dy
                            elif dist <= stop_dist: 
                                dx, dy = 0, 0
                            else:
                                dx, dy = gpu_dx, gpu_dy
                            
                 elif doctrine == "DEFEND":
                        if dist > 20: dx, dy = 0, 0
                        else: dx, dy = gpu_dx, gpu_dy
                 else:
                        dx, dy = gpu_dx, gpu_dy
                        
            else:
                 # [CPU Fallback Path]
                 dist = grid.get_distance(u, nearest)
                 dx, dy = calculate_movement_vector(u, nearest, doctrine, grid)
            
            move_speed = u.movement_points
            start_pos = (u.grid_x, u.grid_y)
            
            # Rotation (approximate based on move delta if using GPU, or target if not)
            if dx != 0 or dy != 0:
                 target_angle_rad = math.atan2(dy, dx)
                 target_angle_deg = (math.degrees(target_angle_rad) + 90) % 360
                 grid.rotate_unit(u, target_angle_deg)
            else:
                 # Face target even if not moving
                 # Fallback to manual calculation if we have target obj
                 dx_t = nearest.grid_x - u.grid_x
                 dy_t = nearest.grid_y - u.grid_y
                 target_angle_rad = math.atan2(dy_t, dx_t)
                 target_angle_deg = (math.degrees(target_angle_rad) + 90) % 360
                 grid.rotate_unit(u, target_angle_deg)
            
            if doctrine == "DEFEND":
                move_speed = max(0, move_speed - 1) 
                
            for _ in range(int(move_speed)):
                # If we used GPU flow field, 'dx, dy' is the vector for the whole turn.
                # However, calculate_movement_vector might return 1-step logic?
                # Actually calculate_movement_vector returns step (-1, 0, 1).
                # GPU flow field returns step (-1, 0, 1).
                # So we can just re-use dx, dy.
                
                # Verify we aren't stuck? 
                # Flow field is static snapshot, so dx/dy is constant for this unit this turn.
                
                if dx == 0 and dy == 0: break
                if not grid.move_unit(u, u.grid_x + dx, u.grid_y + dy):
                     if not grid.move_unit(u, u.grid_x + dx, u.grid_y):
                          grid.move_unit(u, u.grid_x, u.grid_y + dy)
            
            if detailed_log_file:
                with open(detailed_log_file, "a", encoding='utf-8') as f:
                    f.write(f"MOVE: {u.name} from {start_pos} to ({u.grid_x}, {u.grid_y}). Nearest Dist: {dist:.1f}\n")


class ShootingPhase(CombatPhase):
    name: str = "shooting"
    
    @profile_method
    def execute(self, context: Dict[str, Any]) -> None:
        active_units = context.get("active_units", [])
        enemies_by_faction = context.get("enemies_by_faction", {})
        grid = context.get("grid")
        faction_doctrines = context.get("faction_doctrines", {})
        faction_metadata = context.get("faction_metadata", {})
        round_num = context.get("round_num", 1)
        detailed_log_file = context.get("detailed_log_file")
        tracker = context.get("tracker")
        manager = context.get("manager")
        universe_rules = context.get("universe_rules")

        from src.combat.tactical_engine import select_target_by_doctrine

        indices = list(range(len(active_units)))
        get_stream("phases").shuffle(indices)
        active_units_shoot = [active_units[i] for i in indices]
        
        # [GPU Acceleration] Batch Shooting
        attackers_obj = [u for u, f in active_units_shoot if u.is_alive()]
        all_unit_lookup = {id(u): u for u, f in active_units if u.is_alive()}
        tracker_ref = context.get("gpu_tracker") or context.get("tracker")
        import src.combat.batch_shooting as batch_shooter
        
        # Check if we can use batch mode
        # Conditions: Tracker exists, and batch_shooter imported successfully
        use_batch = False
        if tracker_ref and hasattr(tracker_ref, 'compute_nearest_enemies'):
             use_batch = True
             
        if use_batch:
             logger.debug("ShootingPhase: Executing Accelerated Batch Shooting")
             
             # 2. Batch Execute (Staggered Waves to reduce overkill)
             # Optimization 2.5: Consolidate waves to minimize GPU synchronization overhead.
             wave_size = max(1000, len(attackers_obj) // 2)
             all_batch_results = []
             
             for i in range(0, len(attackers_obj), wave_size):
                 wave = attackers_obj[i:i+wave_size]
                 
                 # Re-compute nearest targets for this wave (accounts for previous wave's kills)
                 # [CRITICAL] We need to update the GPU tracker's internal state if units died
                 if i > 0:
                      tracker_ref.update_positions([u for u, f in active_units if u.is_alive()])
                 
                 target_map_wave = tracker_ref.compute_nearest_enemies()
                 batch_target_map = {att_id: tgt_id for att_id, (tgt_id, dist) in target_map_wave.items()}
                 batch_dist_map = {att_id: dist for att_id, (tgt_id, dist) in target_map_wave.items()}
                 
                 # Debug Loadout
                 if i == 0 and len(wave) > 0:
                       sample_u = wave[0]
                       wpns = []
                       for c in sample_u.components:
                           if c.type == "Weapon":
                               range_val = c.weapon_stats.get("Range", "N/A")
                               wpns.append(f"{c.name}(R:{range_val})")
                       for c in sample_u.components:
                           if c.type == "Weapon":
                               range_val = c.weapon_stats.get("Range", "N/A")
                               wpns.append(f"{c.name}(R:{range_val})")
                    # print(f"DEBUG LOADOUT: {sample_u.name} Faction: {sample_u.faction} Weapons: {wpns}")
                 
                 # [PHASE 30] Collect Formation Modifiers
                 formation_mods = {}
                 for att_u in wave:
                     if hasattr(att_u, 'formations') and att_u.formations:
                         formation_mods[id(att_u)] = att_u.formations[0].get_modifiers()

                 wave_results = batch_shooter.resolve_shooting_batch(
                      wave, 
                      batch_target_map, 
                      batch_dist_map, 
                      all_unit_lookup,
                      formation_modifiers=formation_mods
                 )
                 
                 # Apply immediately so next wave sees survivors
                 for res in wave_results:
                     att = res["attacker"]
                     tgt = res["target"]
                     if not tgt.is_alive(): continue # Don't fire at dead meat (from same wave or prev)
                     
                     # print(f"DEBUG_STDOUT: Processing shot {att.name} -> {tgt.name} Hit={res['is_hit']}")

                     dmg = res["damage"]
                     if res["is_hit"]:
                          # [Total War 40k] Dynamic Cover Destruction
                          if grid and dmg > 15: # High-impact weaponry damages terrain
                               cover_status = grid.damage_cover(tgt.grid_x, tgt.grid_y, 25)
                               if cover_status == "DESTROYED" and manager:
                                    manager.log_event("COVER_DESTROYED", att.name, "Terrain", f"Cover at ({tgt.grid_x},{tgt.grid_y}) obliterated!")
                               elif cover_status == "DOWNGRADE" and manager:
                                    pass

                          # [EaW Style] Select a hardpoint to damage (Simulating precision or lucky hits)
                          target_comp = None
                          if hasattr(tgt, 'components') and tgt.components:
                                # Try to hit a weapon first for cinematic effect
                                weapons = [c for c in tgt.components if getattr(c, 'type', 'Unknown') == "Weapon" and not getattr(c, 'is_destroyed', False)]
                                if weapons:
                                     # Filter out components without names
                                     weapons = [w for w in weapons if hasattr(w, 'name')]
                                     if weapons:
                                          import random
                                          target_comp = random.choice(weapons)
                           
                                # Fallback: Hit any named component (e.g. Engine, Bridge if implemented)
                                if not target_comp:
                                     valid_comps = [c for c in tgt.components if not getattr(c, 'is_destroyed', False) and hasattr(c, 'name')]
                                     if valid_comps: 
                                          import random
                                          target_comp = random.choice(valid_comps)
                           
                          # Only damage if we found a valid hardpoint
                          destroyed_comp = None
                          if target_comp:
                               s_dmg, h_dmg, _, destroyed_comp = tgt.take_damage(dmg, target_component=target_comp, ignore_mitigation=True)
                          else:
                               # Normal damage (Hull only)
                               s_dmg, h_dmg, _, destroyed_comp = tgt.take_damage(dmg)

                          if destroyed_comp and manager and hasattr(manager, 'log_event'):
                               comp_name = getattr(destroyed_comp, 'name', 'Vital System')
                               manager.log_event("HARDPOINT_DESTROYED", att.name, tgt.name, description=comp_name)
                           
                          if manager and hasattr(manager, 'battle_stats'):
                               if att.faction not in manager.battle_stats:
                                   manager.battle_stats[att.faction] = {"units_lost": 0, "total_damage_dealt": 0, "kills": 0}
                               manager.battle_stats[att.faction]["total_damage_dealt"] += dmg
                     
                     all_batch_results.append(res)
             
             batch_results = all_batch_results
             
             # 3. Apply & Log Results
             for res in batch_results:
                  attacker = res["attacker"]
                  target = res["target"]
                  final_dmg = res["damage"]
                  is_hit = res["is_hit"]
                  wpn = res["weapon"]
                  dist = res["dist"]
                  
                  if is_hit:
                       is_kill = not target.is_alive()
                       
                       # Report to battle_stats (Phase 250 Stalemate Detection)
                       if manager and hasattr(manager, 'battle_stats'):
                            if attacker.faction not in manager.battle_stats:
                                manager.battle_stats[attacker.faction] = {"units_lost": 0, "total_damage_dealt": 0, "kills": 0}
                            manager.battle_stats[attacker.faction]["total_damage_dealt"] += final_dmg

                       if detailed_log_file:
                             with open(detailed_log_file, "a", encoding='utf-8') as f:
                                  f.write(f"Round {round_num}: {attacker.name} fires {wpn.name} at {target.name} (Dist {dist:.1f}) -> {int(final_dmg)} dmg\n")
                                  
                       if tracker:
                            # Simplified event log for now
                             tracker.log_event(
                                "weapon_fire_batch", attacker, target, 
                                weapon=wpn,
                                damage=final_dmg,
                                killed=is_kill,
                                range=dist
                            )
                  else:
                       # Log Miss
                       pass # Batch misses usually not logged to save IO
                       
             return # Skip legacy loop
        
        # [Legacy Sequential Loop]
        for attacker, att_faction in active_units_shoot:
            if not attacker.is_alive(): continue
            attacker.recover_suppression()
            if attacker.is_ship(): attacker.regenerate_shields()

            if manager and hasattr(manager, 'mechanics_engine') and manager.mechanics_engine:
                 manager.mechanics_engine.apply_mechanic_modifiers(att_faction, [attacker])
            
            enemies = enemies_by_faction.get(att_faction, [])
            enemies = [e for e in enemies if e.is_alive()]
            if not enemies: continue
            
            doctrine = faction_doctrines.get(att_faction, "CHARGE")
            att_meta = faction_metadata.get(att_faction, {})
            att_f_doctrine = att_meta.get("faction_doctrine", "STANDARD")
            att_intensity = att_meta.get("intensity", 1.0)

            defender, _ = select_target_by_doctrine(attacker, enemies, doctrine, grid)
            if not defender: continue
            
            dist = grid.get_distance(attacker, defender)
            
            if universe_rules and hasattr(universe_rules, "apply_doctrine_modifiers"):
                 doc_mods = universe_rules.apply_doctrine_modifiers(attacker, doctrine, "SHOOTING", att_f_doctrine, att_intensity)
            else:
                 doc_mods = apply_doctrine_modifiers(attacker, doctrine, "SHOOTING", att_f_doctrine, att_intensity)
            
            active_mods = getattr(attacker, 'active_mods', {})
            doc_mods["dmg_mult"] *= active_mods.get("global_damage_mult", 1.0)
            doc_mods["bs_mod"] += active_mods.get("bs_mod", 0)
            
            def_faction = None
            for f_name, units in enemies_by_faction.items():
                if f_name == att_faction: continue
                if defender in units:
                    def_faction = f_name
                    break
            
            def_doctrine = faction_doctrines.get(def_faction, "CHARGE") if def_faction else "CHARGE"
            def_meta = faction_metadata.get(def_faction, {}) if def_faction else {}
            def_f_doctrine = def_meta.get("faction_doctrine", "STANDARD")
            def_intensity = def_meta.get("intensity", 1.0)

            if universe_rules and hasattr(universe_rules, "apply_doctrine_modifiers"):
                 def_mods = universe_rules.apply_doctrine_modifiers(defender, def_doctrine, "SHOOTING", def_f_doctrine, def_intensity)
            else:
                 def_mods = apply_doctrine_modifiers(defender, def_doctrine, "SHOOTING", def_f_doctrine, def_intensity)
            
            for comp in attacker.components:
                if comp.type == "Weapon" and not comp.is_destroyed:
                    result = WeaponExecutor.execute_weapon_fire(attacker, defender, comp, dist, grid, doctrine, 
                                               doc_mods, def_mods, round_num, tracker,
                                               battle_stats=manager.battle_stats if manager else None)
                    
                    if result and detailed_log_file:
                        with open(detailed_log_file, "a", encoding='utf-8') as f:
                            f.write(f"Round {round_num}: {attacker.name} fires {comp.name} at {defender.name} (Dist {dist:.1f}) -> {int(result['damage'])} dmg\n")


class AbilityPhase(CombatPhase):
    name: str = "ability"
    
    @profile_method
    def execute(self, context: Dict[str, Any]) -> None:
        from src.combat.tactical_engine import select_target_by_doctrine
        from src.combat.ability_manager import AbilityManager
        import json
        import os
        
        active_units = context.get("active_units", [])
        enemies_by_faction = context.get("enemies_by_faction", {})
        grid = context.get("grid")
        faction_doctrines = context.get("faction_doctrines", {})
        detailed_log_file = context.get("detailed_log_file")
        tracker = context.get("tracker")
        manager = context.get("manager")
        
        if not manager:
            return
        
        if not hasattr(manager, "ability_manager"):
             print("DEBUG: Initializing AbilityManager from registry")
             try:
                 registry_path = os.path.join("universes", "void_reckoning", "factions", "ability_registry.json")
                 if os.path.exists(registry_path):
                     with open(registry_path, 'r') as f:
                         registry = json.load(f)
                 else:
                     registry = {}
             except:
                 registry = {}
                 
             manager.ability_manager = AbilityManager(registry)

        ab_manager = manager.ability_manager
        
        # print("DEBUG: AbilityPhase Executing")
        # print(f"DEBUG: Registry Keys: {list(ab_manager.registry.keys())}")
        
        if not ab_manager:
            if detailed_log_file:
                 with open(detailed_log_file, "a", encoding='utf-8') as f: f.write("ABILITY PHASE: No Manager\n")
            print("DEBUG: No AbilityManager")
            return

        indices = list(range(len(active_units)))
        try:
            get_stream("phases").shuffle(indices)
        except Exception as e:
            pass
        str_indices = [active_units[i] for i in indices]

        for u, f_name in str_indices:
            if not u.is_alive():
                 continue
            
            # print(f"DEBUG: Checking unit {u.name}") # TOO NOISY if many units

            mech_engine = getattr(manager, 'mechanics_engine', None)
            if mech_engine:
                 mech_engine.apply_mechanic_modifiers(f_name, [u])

            abilities = getattr(u, "abilities", [])
            if not abilities and hasattr(u, "atomic_abilities"):
                 abilities = list(u.atomic_abilities.keys())
                 
            if not abilities:
                 # print(f"DEBUG: {u.name} has no abilities")
                 continue

            # print(f"DEBUG: {u.name} has abilities: {abilities}")

            enemies = enemies_by_faction.get(f_name, [])
            enemies = [e for e in enemies if e.is_alive()]
            if not enemies: continue
            
            doctrine = faction_doctrines.get(f_name, "CHARGE")
            
            cast_success = False
            for ab_id in abilities:
                 # print(f"DEBUG: {u.name} trying {ab_id}")
                 if cast_success: break
                 
                 ab_def = ab_manager.registry.get(ab_id, {})
                 if not ab_def:
                      # print(f"DEBUG: {ab_id} not in registry")
                      continue
                 
                 # Optimization: Check range/target before calling execute
                 target = None
                 payload = ab_def.get("payload_type", "damage")
                 
                 # Self-Target check
                 if payload in ["heal", "buff", "shield_regen", "charge", "guard_mode", "rally", "repair"]:
                      target = u
                 else:
                      # Find target
                      if not enemies: continue
                      target = enemies[0] # Simplest AI: Atttack first enemy
                      # TODO: Better targeting logic based on doctrine?
                 
                 if not target: continue
                 
                 ab_range = ab_def.get("range", 50)
                 dist = grid.get_distance(u, target)
                 if dist > ab_range: continue
                 
                 # Prepare Context
                 exec_context = {
                      "faction": None, # Could get from battle_state if needed
                      "grid": grid,
                      "enemies": enemies,
                      "battle_state": manager, # For stat tracking
                      "detailed_log_file": detailed_log_file # Pass log file
                 }
                 
                 result = ab_manager.execute_ability(u, target, ab_id, exec_context)
                 # print(f"DEBUG: Result for {ab_id}: {result}")
                  
                 if result["success"]:
                       cast_success = True
                       if detailed_log_file:
                            with open(detailed_log_file, "a", encoding='utf-8') as log:
                                log.write(f"ABILITY: {u.name} used {ab_id} on {target.name} -> {result.get('description', 'Success')}\n")
                       
                       if tracker:
                           tracker.log_event("ability_use", u, target, ability=ab_id, result=result)
                 else:
                       # Debug Failure
                       if detailed_log_file:
                            with open(detailed_log_file, "a", encoding='utf-8') as log:
                                log.write(f"ABILITY FAIL: {u.name} used {ab_id} -> {result.get('reason', 'Unknown')}\n")
                          
                       # Optional: Log to tracker as debug?
                       if tracker:
                           tracker.log_event("ability_fail", u, target, ability=ab_id, result=result)

class MeleePhase(CombatPhase):
    name: str = "melee"
    
    @profile_method
    def execute(self, context: Dict[str, Any]) -> None:
        active_units = context.get("active_units", [])
        enemies_by_faction = context.get("enemies_by_faction", {})
        faction_doctrines = context.get("faction_doctrines", {})
        
        for u, f_name in active_units:
            if not u.is_alive(): continue
            
            enemies = enemies_by_faction.get(f_name, [])
            enemies = [e for e in enemies if e.is_alive()]
            if not enemies: continue

            if not u.is_ship():
                enemy_army = [e for e in enemies if not e.is_ship()]
                if enemy_army:
                    # Filter context to avoid collision
                    safe_kwargs = {k:v for k,v in context.items() if k not in ['round_num', 'detailed_log_file', 'tracker', 'faction_metadata', 'faction_doctrines']}
                    
                    resolve_ground_melee(
                        [u], 
                        enemy_army, 
                        context.get("round_num"), 
                        detailed_log_file=context.get("detailed_log_file"), 
                        tracker=context.get("tracker"), 
                        doctrine=faction_doctrines.get(f_name, "CHARGE"), 
                        faction_doctrines=faction_doctrines, 
                        faction_metadata=context.get("faction_metadata"), 
                        **safe_kwargs
                    )
            
            
        if any(u.is_ship() for u, f in active_units):
            # Flatten lists for legacy resolve_boarding_phase signature
            # It expects (active_army_list, enemy_army_list, ...)
            
            # 1. Active Ships (Units only)
            active_ships = [u for u, f in active_units if u.is_ship()]
            
            # 2. All Enemy Ships (Units only)
            # enemies_by_faction is {f_name: [Unit, Unit...]}
            all_enemies = []
            for unit_list in enemies_by_faction.values():
                all_enemies.extend(unit_list)
            
            # Filter context to avoid collision
            safe_kwargs = {k:v for k,v in context.items() if k not in ['round_num', 'detailed_log_file', 'tracker']}
            
            resolve_boarding_phase(
                active_ships, 
                all_enemies, 
                context.get("round_num"), 
                detailed_log_file=context.get("detailed_log_file"), 
                tracker=context.get("tracker"), 
                **safe_kwargs
            )


class MoralePhase(CombatPhase):
    name: str = "morale"
    
    @profile_method
    @profile_method
    def execute(self, context: Dict[str, Any]) -> None:
        manager = context.get("manager")
        if not manager: return
        
        active_units = context.get("active_units", [])
        round_num = context.get("round_num", 1)
        tracker = context.get("tracker")
        detailed_log_file = context.get("detailed_log_file")
        
        for u, f_name in active_units:
            if not u.is_alive(): continue
            
            if getattr(u, 'is_routing', False):
                continue

            mechanic_context = {
                "unit": u,
                "faction_name": f_name,
                "faction": manager.mechanics_engine.engine.factions.get(f_name) if manager.mechanics_engine else None,
                "battle_state": manager,
                "round_num": round_num,
                "is_immune": False
            }
            
            if manager.mechanics_engine:
                manager.mechanics_engine.apply_mechanics(f_name, "on_morale_check", mechanic_context)
                
            if mechanic_context.get("is_immune"):
                 continue
                 
            # [TRAPPING MECHANIC] Interdiction Check
            # If an enemy interdictor is present, units cannot successfully route (flux escape is blocked)
            interdictor_present = context.get("interdictor_present", False)
            
            suppression = getattr(u, 'current_suppression', 0)
            ld = getattr(u, 'leadership', 7)
            hp_pct = (u.current_hp / u.max_hp) if u.max_hp > 0 else 1.0
            
            # [PHASE 23] Lethality Tuning: Steeper Morale Penalties
            # Old: <25% HP -> -2, <50% HP -> -1
            # New: Linear penalty based on HP lost (+ extra for low HP)
            
            # -1 LD per 20% HP lost
            hp_loss_pct = 1.0 - hp_pct
            ld_mod = -int(hp_loss_pct * 5) # e.g. 50% loss = -2, 80% loss = -4
            
            if hp_pct < 0.25: ld_mod -= 2 # Critical state panic
            elif hp_pct < 0.5: ld_mod -= 1
            
            # [Total War Style] Fatigue Mechanic
            # Fatigue grows with each round if the unit is fighting or moving
            fatigue = getattr(u, 'fatigue_level', 0.0)
            # Simplified: Fatigue increases slightly every round, more if they fought/moved (tracked elsewhere maybe)
            # For now, let's just make it a round-based increase for headless simulation feel
            fatigue = min(1.0, fatigue + (round_num * 0.005))
            u.fatigue_level = fatigue
            
            # Penalties based on fatigue
            fatigue_penalty = 0
            if fatigue > 0.8: fatigue_penalty = -2 # Exhausted
            elif fatigue > 0.5: fatigue_penalty = -1 # Tired
            
            ld_mod += fatigue_penalty

            # [Total War Style] Chain Routing Logic
            # If nearby friendly units are routing, this unit gets a penalty
            grid = context.get("grid") # Assuming grid is passed in context
            if not u.is_ship() and grid:
                nearby_friendlies = grid.query_units_in_range(u.grid_x, u.grid_y, radius=15, faction_filter=f_name)
                routing_nearby = sum(1 for f in nearby_friendlies if getattr(f, 'is_routing', False))
                if routing_nearby > 0:
                    # -1 LD per 2 routing units nearby (cap at -3)
                    chain_penalty = -min(3, routing_nearby // 2)
                    ld_mod += chain_penalty
                    if chain_penalty < 0 and detailed_log_file:
                         with open(detailed_log_file, "a", encoding='utf-8') as f:
                              f.write(f"  [MORALE] {u.name} is shaken by nearby routing allies! (LD: {chain_penalty})\n")
                
                    # [CINEMATIC LOGGING]
                    if chain_penalty <= -3 and hasattr(context.get("manager"), "log_event"):
                         context.get("manager").log_event("CHAIN_ROUTING", u.name, "Unit", description="Nearby allies routing")

            check_val = ld + ld_mod
            
            roll = get_stream("phases").randint(2, 12)
            if roll > check_val and suppression > 0:
                 if interdictor_present:
                      # Pin them or inflict critical damage instead of routing
                      u.current_hp = int(u.current_hp * 0.5) 
                      u.is_routing = False # Forced to stay and fight
                      if tracker:
                          tracker.log_event("interdiction_trap", u, None, details="Escape blocked by Gravity Well! Fleet is TRAPPED and taking critical damage.")
                      if detailed_log_file:
                          with open(detailed_log_file, "a", encoding='utf-8') as f:
                              f.write(f"  [INTERDICTION] {u.name} attempted escape but was TRAPPED by Gravity Well! (Forced to stay, HP halved)\n")
                 else:
                      u.is_routing = True
                      # [CINEMATIC LOGGING]
                      if hasattr(context.get("manager"), "log_event"):
                           context.get("manager").log_event("MORALE_FAILURE", u.name, "Unit", description="Resolve Broken")
                      
                      if tracker:
                           tracker.log_event("morale_failure", u, None, roll=roll, threshold=check_val, details="Unit is routing!")
                      if detailed_log_file:
                          with open(detailed_log_file, "a", encoding='utf-8') as f:
                              f.write(f"  [MORALE] {u.name} FAILED morale check (Roll: {roll} > {check_val}) -> ROUTING\n")


class OrbitalSupportPhase(CombatPhase):
    """
    [PHASE 23] Orbital Bombardment System.
    Ground units receive fire support if a friendly fleet is in orbit.
    """
    name: str = "orbital_support"
    
    @profile_method
    def execute(self, context: Dict[str, Any]) -> None:
        manager = context.get("manager")
        if not manager: return
        
        # 1. Identify context (Planet/Province)
        location = getattr(manager, 'location', None)
        if not location: return
        
        # Ground support only
        is_ground = hasattr(location, 'parent_planet') or getattr(location, 'is_province', False)
        if not is_ground: return
        
        parent_planet = getattr(location, 'parent_planet', location)
        
        # 2. Check for orbiting fleets (provided via manager or context)
        # We'll assume the manager has a list of 'orbiting_fleets' or we query the campaign engine
        campaign = getattr(manager, 'context', None)
        if not campaign: return
        
        all_fleets = campaign.get_all_fleets()
        orbit_fleets = [f for f in all_fleets if f.location == parent_planet and not f.is_destroyed]
        
        if not orbit_fleets: return
        
        # 3. Apply Bombardment
        armies_dict = manager.armies_dict
        factions_with_orbit = {f.faction for f in orbit_fleets}
        
        for f_name, units in armies_dict.items():
            # If this faction has a fleet in orbit, they get support!
            if f_name in factions_with_orbit:
                # Target enemies
                enemies = []
                for ef, e_units in armies_dict.items():
                    if ef != f_name:
                        enemies.extend([u for u in e_units if u.is_alive()])
                
                if not enemies: continue
                
                # Pick a random enemy cluster or target
                target = random.choice(enemies)
                
                # Apply high explosive damage (Morale shock + HP damage)
                dmg = 100 # Heavy bombardment
                sh, hl, _, comp = target.take_damage(dmg)
                
                # Suppression/Morale Impact
                from src.managers.combat.suppression_manager import SuppressionManager
                SuppressionManager().apply_suppression(target, 50.0)
                target.morale_current = max(0, target.morale_current - 20)
                
                msg = f"  [ORBITAL] {parent_planet.name} orbit fleet provides support! Hit {target.name} for {int(hl)} dmg."
                if context.get("detailed_log_file"):
                    with open(context["detailed_log_file"], "a") as f:
                        f.write(msg + "\n")
                print(msg)

# --- Compatibility Wrappers ---

def resolve_movement_phase(*args, **kwargs):
    # Map args/kwargs to context
    # Args are: active_units, enemies_by_faction, grid, spatial_index, faction_doctrines, faction_metadata, round_num, detailed_log_file
    context = kwargs.copy()
    if len(args) > 0: context["active_units"] = args[0]
    if len(args) > 1: context["enemies_by_faction"] = args[1]
    if len(args) > 2: context["grid"] = args[2]
    if len(args) > 3: context["spatial_index"] = args[3]
    if len(args) > 4: context["faction_doctrines"] = args[4]
    if len(args) > 5: context["faction_metadata"] = args[5]
    if len(args) > 6: context["round_num"] = args[6]
    if len(args) > 7: context["detailed_log_file"] = args[7]
    MovementPhase().execute(context)

def resolve_shooting_phase(*args, **kwargs):
    context = kwargs.copy()
    if len(args) > 0: context["active_units"] = args[0]
    if len(args) > 1: context["enemies_by_faction"] = args[1]
    if len(args) > 2: context["grid"] = args[2]
    if len(args) > 3: context["spatial_index"] = args[3]
    if len(args) > 4: context["faction_doctrines"] = args[4]
    if len(args) > 5: context["faction_metadata"] = args[5]
    if len(args) > 6: context["round_num"] = args[6]
    if len(args) > 7: context["detailed_log_file"] = args[7]
    if len(args) > 8: context["tracker"] = args[8]
    ShootingPhase().execute(context)

def resolve_ability_phase(*args, **kwargs):
    context = kwargs.copy()
    if len(args) > 0: context["active_units"] = args[0]
    if len(args) > 1: context["enemies_by_faction"] = args[1]
    if len(args) > 2: context["grid"] = args[2]
    if len(args) > 3: context["spatial_index"] = args[3]
    if len(args) > 4: context["faction_doctrines"] = args[4]
    if len(args) > 5: context["faction_metadata"] = args[5]
    if len(args) > 6: context["round_num"] = args[6]
    if len(args) > 7: context["detailed_log_file"] = args[7]
    if len(args) > 8: context["tracker"] = args[8]
    AbilityPhase().execute(context)

def resolve_melee_phase(*args, **kwargs):
    context = kwargs.copy()
    if len(args) > 0: context["active_units"] = args[0]
    if len(args) > 1: context["enemies_by_faction"] = args[1]
    if len(args) > 2: context["round_num"] = args[2]
    if len(args) > 3: context["detailed_log_file"] = args[3]
    if len(args) > 4: context["tracker"] = args[4]
    if len(args) > 5: context["faction_doctrines"] = args[5]
    if len(args) > 6: context["faction_metadata"] = args[6]
    MeleePhase().execute(context)

def resolve_morale_phase(*args, **kwargs):
    context = kwargs.copy()
    if len(args) > 0: context["active_units"] = args[0]
    MoralePhase().execute(context)

# Legacy
def init_phases_rng(seed: Optional[int] = None):
    pass
