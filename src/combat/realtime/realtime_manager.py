import math
import random
from typing import Any, List, Optional

# [PERF R18] Module-level imports (avoid per-tick import overhead)
from src.combat.real_time.steering_manager import SteeringManager
from src.combat.real_time.morale_manager import MoraleManager
from src.managers.combat.suppression_manager import SuppressionManager
from src.combat.tactical.target_selector import TargetSelector
from src.combat.combat_phases import AbilityPhase, OrbitalSupportPhase
from src.models.unit import Component
from src.core.balance import UNIT_XP_AWARD_SURVIVAL_SEC, UNIT_XP_AWARD_DAMAGE_RATIO, UNIT_XP_AWARD_KILL

# [PERF R19] Cached singleton instances
_suppression_manager = SuppressionManager()
_ability_phase = AbilityPhase()
_orbital_support_phase = OrbitalSupportPhase()

class RealTimeManager:
    """
    Manages real-time combat updates (Phase 4).
    Extracted from CombatState.
    """
    def __init__(self):
        pass
        
    def update(self, battle_state, dt: float):
        """
        Orchestrates real-time updates for all units.
        """
        battle_state.total_sim_time += dt
        
        # [PHASE 18] Periodic Snapshots
        if battle_state.total_sim_time - battle_state.last_snapshot_time >= 2.0:
             battle_state._take_snapshot()
             battle_state.last_snapshot_time = battle_state.total_sim_time

        grid = battle_state.grid
        armies_dict = battle_state.armies_dict
        grid = battle_state.grid
        armies_dict = battle_state.armies_dict
        
        # 0. Pre-calc Formation Map
        unit_formation_map = {}
        if hasattr(battle_state, 'formations'):
            for form in battle_state.formations:
                 for e in form.entities:
                     unit_formation_map[e] = form

        # [PERF R20] Pre-calculate enemy data once per tick (O(N) instead of O(N^2))
        active_factions = battle_state.active_factions
        enemies_by_faction = {f: [] for f in armies_dict}
        for f in active_factions:
            for ef in active_factions:
                if ef != f:
                    enemies_by_faction[f].extend([e for e in armies_dict.get(ef, []) if e.is_alive()])
        
        # [PERF R20] Calculate faction centroids (motion targets) once per tick
        faction_centroids = {}
        for f in active_factions:
            enemies = enemies_by_faction[f]
            if enemies:
                active_enemies = [e for e in enemies if getattr(e, 'morale_state', 'Steady') != "Routing"]
                motion_targets = active_enemies if active_enemies else enemies
                if motion_targets:
                    tx = sum(e.grid_x for e in motion_targets) / len(motion_targets)
                    ty = sum(e.grid_y for e in motion_targets) / len(motion_targets)
                    faction_centroids[f] = (tx, ty)

        # 2. Context Preparation (Moved up to support XP awards)
        ab_context = {
            "active_units": [(u, f_name) for f_name, units in armies_dict.items() for u in units if u.is_alive()],
            "enemies_by_faction": enemies_by_faction, 
            "faction_doctrines": battle_state.faction_doctrines,
            "grid": grid,
            "mechanics_engine": battle_state.mechanics_engine,
            "battle_state": battle_state,
            "manager": battle_state,
            "tracker": battle_state.tracker,
            "detailed_log_file": None,
            "ability_manager": getattr(battle_state, 'ability_manager', None)
        }
        
        # 1. Update Positions via Steering
        for f_name, units in armies_dict.items():
            if not units: continue
            
            # [PERF R19] Suppression Decay (once per faction per tick)
            _suppression_manager.process_decay(units)
            
            centroid = faction_centroids.get(f_name)

            for u in units:
                if not u.is_alive(): continue
                
                # Query neighbors (Boids)
                neighbors = []
                if grid and hasattr(grid, 'spatial_index') and grid.spatial_index:
                    near = grid.query_units_in_range(u.grid_x, u.grid_y, radius=10) # 10 is arbitrary neighbor radius
                    neighbors = [n for n in near if n is not u]
                
                prev_morale = getattr(u, 'morale_state', 'Steady')
                MoraleManager.update_unit_morale(u, dt, units, grid)
                if getattr(u, 'morale_state', 'Steady') != prev_morale:
                    battle_state.log_event("morale", u.name, "Unit", f"State changed to {u.morale_state}")
                
                if getattr(u, 'is_pinned', False): continue

                # Formation & Target Logic
                target_pos = None
                doctrine = getattr(u, 'tactical_directive', "STANDARD")
                if doctrine == "STANDARD":
                    doctrine = battle_state.faction_doctrines.get(f_name, "CHARGE")
                
                # Victory Point / Objective Logic
                enemy_factions = [ef for ef in active_factions if ef != f_name]
                my_vps = battle_state.victory_points.get(f_name, 0.0)
                other_vps = [battle_state.victory_points.get(ef, 0.0) for ef in enemy_factions]
                is_losing = any(my_vps < (ovp - 5) for ovp in other_vps)
                
                capture_target = None
                if (doctrine == "CAPTURE_AND_HOLD" or is_losing) and hasattr(grid, 'objectives'):
                     obj_candidates = [obj for obj in grid.objectives if obj.owner != f_name]
                     if obj_candidates:
                         capture_target = min(obj_candidates, key=lambda o: grid.get_distance_coords(u.grid_x, u.grid_y, o.x, o.y))
                
                if capture_target:
                    target_pos = (capture_target.x, capture_target.y)
                else:
                    target_pos = centroid

                obstacles = getattr(grid, 'obstacles', [])
                dx, dy = SteeringManager.calculate_combined_steering(u, neighbors, target_pos, obstacles, doctrine=doctrine)
                
                # Apply Speed & Modifiers
                speed_mult = 1.0
                env_mods = grid.get_modifiers_at(u.grid_x, u.grid_y)
                speed_mult *= env_mods.get("speed_mult", 1.0)
                
                # [PERF R19] Cached Suppression mods
                supp_mods = _suppression_manager.get_suppression_modifiers(u)
                speed_mult *= supp_mods.get("speed_mult", 1.0)
                
                # Formation Speed Modifiers
                if u in unit_formation_map:
                    f_mods = unit_formation_map[u].get_modifiers()
                    speed_mult *= f_mods.get("movement_speed_mult", 1.0)
                
                if getattr(u, 'morale_state', 'Steady') == "Routing":
                    speed_mult = 1.2
                
                speed = getattr(u, 'movement_points', 5) * dt * speed_mult
                u.grid_x += dx * speed
                u.grid_y += dy * speed
                
                if abs(dx) > 0.01 or abs(dy) > 0.01:
                    u.facing = math.degrees(math.atan2(dy, dx))
                    
                if hasattr(grid, 'update_unit_position'):
                    grid.update_unit_position(u, u.grid_x, u.grid_y)
                
                # Award survival XP (approx 1 XP per second of active combat)
                u.gain_xp(UNIT_XP_AWARD_SURVIVAL_SEC * dt, ab_context)

        # 2. Abilities
        ab_context["enemies_by_faction"] = enemies_by_faction
        _ability_phase.execute(ab_context)

        # 3. Shooting
        for f_name, units in armies_dict.items():
            enemies = enemies_by_faction.get(f_name, [])
            if not enemies: continue

            for u in units:
                if not u.is_alive(): continue
                if getattr(u, 'morale_state', 'Steady') == "Routing": continue
                
                if not hasattr(u, '_shooting_cooldown'): u._shooting_cooldown = 0
                if u._shooting_cooldown > 0:
                    u._shooting_cooldown -= dt
                    continue
                
                doctrine = getattr(u, 'tactical_directive', "STANDARD")
                if doctrine == "STANDARD": doctrine = battle_state.faction_doctrines.get(f_name, "CHARGE")
                
                target_unit, target_comp = TargetSelector.select_target_by_doctrine(u, enemies, doctrine, grid)
                
                if target_unit:
                    dist = grid.get_distance(u, target_unit)
                    if dist <= 1000:
                        weapons = [c for c in u.components if c.type == "Weapon" and not c.is_destroyed]
                        if not weapons and getattr(u, 'damage', 0) > 0:
                             dummy_stats = {"Range": getattr(u, 'weapon_range_default', 24), "S": getattr(u, 'damage', 1), "AP": 0, "D": 1}
                             weapons = [Component("Base Attack", 1, "Weapon", weapon_stats=dummy_stats)]
                        
                        damage_dealt_total = 0.0
                        for wpn in weapons:
                            # Shooting Logic (Simplified Port)
                            stats = wpn.weapon_stats
                            if dist > stats.get("Range", 24): continue
                            
                            raw_dmg = stats.get("S", 4) * 10 * stats.get("D", 1)
                            
                            # Mitigation
                            t_armor = getattr(target_unit, 'armor', 0)
                            ap = stats.get("AP", 0)
                            sv = 7.0 - (t_armor/10.0) + (ap/10.0)
                            
                            # Cover (Directional)
                            cover = grid.get_cover_at(target_unit.grid_x, target_unit.grid_y)
                            if cover != "None":
                                # Only apply cover if attack is from Front (approx 90 deg arc)
                                bearing = grid.get_relative_bearing(target_unit, u)
                                is_flanked = not (bearing <= 45 or bearing >= 315)
                                
                                if not is_flanked:
                                    sv -= (0.5 if cover == "Heavy" else 0.25)
                            
                            sv = max(2.0, min(7.0, sv))
                            pass_chance = max(0.0, min(1.0, (7.0 - sv)/6.0))
                            inv = (7.0 - target_unit.abilities.get("Invuln", 7))/6.0
                            mit = min(0.95, max(pass_chance, inv))
                            
                            final_dmg = raw_dmg * (1.0 - mit)
                            
                            # Formation Defense (Post-Mitigation reduction)
                            if target_unit in unit_formation_map:
                                f_mods = unit_formation_map[target_unit].get_modifiers()
                                def_mult = f_mods.get("defense_mult", 1.0)
                                if def_mult > 0:
                                    final_dmg /= def_mult
                            
                            # Accuracy
                            hit_prob = getattr(u, 'bs', 50) / 100.0
                            if random.random() > hit_prob: continue
                            
                            dmg_s, dmg_h, is_destroyed, _ = target_unit.take_damage(final_dmg, target_component=target_comp)
                            damage_dealt_total += (dmg_s + dmg_h)
                            
                            # [PERF R18] Award XP using module-level constants
                            u.gain_xp((dmg_s + dmg_h) * UNIT_XP_AWARD_DAMAGE_RATIO, ab_context)
                            if is_destroyed:
                                u.gain_xp(UNIT_XP_AWARD_KILL, ab_context)
                            
                        if damage_dealt_total > 0:
                            u._shooting_cooldown = 1.0
                            if f_name in battle_state.battle_stats:
                                battle_state.battle_stats[f_name]["total_damage_dealt"] += damage_dealt_total
                            battle_state.log_event("shooting", u.name, target_unit.name, f"Salvo hit for {int(damage_dealt_total)} DMG")
                            
                            # [PERF R19] Cached Suppression
                            _suppression_manager.apply_suppression(target_unit, damage_dealt_total * 0.5)

        # 4. Ability Cooldowns
        for f_name, units in armies_dict.items():
            for u in units:
                if u.is_alive() and hasattr(u, 'ability_cooldowns'):
                    for ab, cd in u.ability_cooldowns.items():
                        if cd > 0: u.ability_cooldowns[ab] = max(0, cd - dt)
        
        # 5. Shields
        for units in armies_dict.values():
            for u in units:
                if u.is_alive() and hasattr(u, 'regenerate_shields'): u.regenerate_shields()

        # 6. Objectives
        if hasattr(grid, 'objectives'):
            for obj in grid.objectives:
                present = []
                for f, units in armies_dict.items():
                    if any(u.is_alive() and obj.is_inside(u.grid_x, u.grid_y) for u in units):
                        present.append(f)
                old = obj.owner
                obj.update_capture(present, dt)
                if obj.owner != old and obj.owner:
                    battle_state.log_event("capture", obj.owner, obj.name, f"Owned by {obj.owner}")
                if obj.owner:
                    battle_state.victory_points[obj.owner] += obj.vp_per_sec * dt
                    # Victory check handled by VictoryChecker in loop
        
        # 7. Orbital
        if not hasattr(battle_state, '_orbital_cooldown'): battle_state._orbital_cooldown = 0
        if battle_state._orbital_cooldown > 0:
            battle_state._orbital_cooldown -= dt
        else:
            battle_state._orbital_cooldown = 10.0
            _orbital_support_phase.execute({"manager": battle_state, "detailed_log_file": None})
