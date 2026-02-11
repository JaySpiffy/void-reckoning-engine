import math
import random
from typing import Any, List, Optional

# [PERF R18] Module-level imports (avoid per-tick import overhead)
from src.combat.real_time.steering_manager import SteeringManager
from src.combat.real_time.morale_manager import MoraleManager
from src.managers.combat.suppression_manager import SuppressionManager
from src.combat.tactical.target_selector import TargetSelector
from src.combat.tactical.movement_calculator import MovementCalculator
from src.combat.combat_phases import AbilityPhase, OrbitalSupportPhase
from src.combat.ground_combat import resolve_melee_phase
from src.models.unit import Component
from src.combat.realtime.projectile_manager import ProjectileManager
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
        self.projectile_manager = None
        
    def update(self, battle_state, dt: float):
        """
        Orchestrates real-time updates for all units.
        """
        if self.projectile_manager is None:
            self.projectile_manager = ProjectileManager(battle_state.grid)

        battle_state.total_sim_time += dt
        
        # [PHASE 18] Periodic Snapshots (Throttled if enabled)
        snap_interval = 2.0
        if getattr(battle_state, 'mechanics_engine', None) and hasattr(battle_state.mechanics_engine, 'config'):
            if getattr(battle_state.mechanics_engine.config, 'throttle_snapshots', False):
                # Throttle by 2.5x in campaign runs
                snap_interval = 5.0
        
        if battle_state.total_sim_time - battle_state.last_snapshot_time >= snap_interval:
             battle_state._take_snapshot()
             battle_state.last_snapshot_time = battle_state.total_sim_time

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
                    
                # [FEATURE] Fatigue Update
                # Increase if moving
                is_moving = abs(dx) > 0.01 or abs(dy) > 0.01
                fatigue_change = 0.0
                if is_moving:
                    fatigue_change += 1.0 * dt
                elif getattr(u, 'is_pinned', False): # Fighting in melee
                    fatigue_change += 2.0 * dt
                else:
                    fatigue_change -= 2.0 * dt # Recover
                    
                u.fatigue = max(0.0, min(100.0, getattr(u, 'fatigue', 0.0) + fatigue_change))
                
                # Award survival XP (approx 1 XP per second of active combat)
                u.gain_xp(UNIT_XP_AWARD_SURVIVAL_SEC * dt, ab_context)

        # 2. Abilities
        ab_context["enemies_by_faction"] = enemies_by_faction
        _ability_phase.execute(ab_context)

        # 3. Projectiles Physics Update
        self.projectile_manager.update(dt, battle_state)

        # 4. Shooting
        for f_name, units in armies_dict.items():
            enemies = enemies_by_faction.get(f_name, [])
            if not enemies: continue

            for u in units:
                if not u.is_alive(): continue
                if getattr(u, 'morale_state', 'Steady') == "Routing": continue
                
                doctrine = getattr(u, 'tactical_directive', "STANDARD")
                if doctrine == "STANDARD": doctrine = battle_state.faction_doctrines.get(f_name, "CHARGE")
                
                target_unit, target_comp = TargetSelector.select_target_by_doctrine(u, enemies, doctrine, grid, sim_time=battle_state.total_sim_time)
                
                dx, dy = 0, 0
                if target_unit:
                    dx, dy = MovementCalculator.calculate_movement_vector(u, target_unit, doctrine, grid, dt)

                    dist = grid.get_distance(u, target_unit)
                    
                    # [PHASE 5] Melee Integration (Total War Style contact combat)
                    if dist <= 5.0 and not u.is_ship() and not target_unit.is_ship():
                         melee_context = {
                             "manager": battle_state,
                             "tracker": battle_state.tracker
                         }
                         resolve_melee_phase([u], [target_unit], int(battle_state.total_sim_time), **melee_context)
                         continue

                    # [RANGE ENFORCEMENT] Use unit-specific detection range with domain fallbacks
                    # Ground battles are much smaller than space engagements.
                    max_detect_range = getattr(u, 'detection_range', 800 if u.is_ship() else 200)
                    
                    if dist <= max_detect_range:
                        # Improved Weapon Selection
                        weapons = [c for c in u.weapon_comps if not getattr(c, 'is_destroyed', False)]
                        if not weapons:
                            weapons = [c for c in u.components if getattr(c, 'type', None) == "Weapon" and not getattr(c, 'is_destroyed', False)]
                        
                        if not weapons and getattr(u, 'damage', 0) > 0:
                             dummy_stats = {"Range": getattr(u, 'weapon_range_default', 24), "S": getattr(u, 'damage', 1), "AP": 0, "D": 1, "attacks": 1.0}
                             weapons = [Component("Base Attack", 1, "Weapon", weapon_stats=dummy_stats)]
                        
                        for wpn in weapons:
                            if getattr(wpn, "type", "") != "Weapon": continue
                            stats = wpn.weapon_stats
                            if isinstance(stats, dict):
                                rng = stats.get("Range", 24)
                            else:
                                rng = 24 # Fallback if stats is Mock
                            
                            if dist > rng: continue
                            
                            
                            # [ARC ENFORCEMENT] Check if target is within weapon firing arc
                            arc = getattr(wpn, 'arc', "Front")
                            if arc != "Turret":
                                # Calculate relative angle
                                # 0 degrees is "Forward" relative to the ship (math.atan2 based)
                                target_angle = math.degrees(math.atan2(target_unit.grid_y - u.grid_y, target_unit.grid_x - u.grid_x))
                                facing = getattr(u, 'facing', 0.0)
                                rel_angle = (target_angle - facing + 180) % 360 - 180
                                
                                # Check arc coverage (90 degree cones)
                                if arc == "Front":
                                    if not (-45 <= rel_angle <= 45): continue
                                elif arc == "Left": # Port
                                    if not (45 < rel_angle <= 135): continue
                                elif arc == "Right": # Starboard
                                    if not (-135 <= rel_angle < -45): continue
                                elif arc == "Rear":
                                    if not (abs(rel_angle) > 135): continue
                            
                            # Per-weapon cooldown handling
                            if not hasattr(wpn, 'cooldown'): wpn.cooldown = 0.0
                            if wpn.cooldown > 0:
                                wpn.cooldown -= dt
                                continue
                            
                            # Calculate reload time from 'attacks' (e.g. 2 attacks/round = 2.5s reload if 1 round=5s)
                            # Or more simply: reload = 1.0 / attacks
                            attacks = stats.get("attacks", 1.0)
                            
                            # [FEATURE] Squadron Logic: Scale attacks by member count
                            member_count = getattr(u, 'member_count', 1)
                            attacks *= member_count
                            
                            wpn.cooldown = 1.0 / max(0.1, attacks)

                            # Determine Weapon Attributes for Projectile
                            cat = stats.get("category", "KINETIC").upper()
                            speed = 120.0 # Default Kinetic
                            proj_type = "KINETIC"
                            
                            if "ENERGY" in cat or "LASER" in cat:
                                speed = 800.0
                                proj_type = "LASER"
                            elif "MISSILE" in cat or "TORPEDO" in cat:
                                speed = 60.0
                                proj_type = "MISSILE"
                            
                            # Base Damage calculation (applied on impact by ProjectileManager)
                            raw_dmg = stats.get("S", 4) * 10 * stats.get("D", 1)
                            
                            # Accuracy Roll at point of fire
                            base_hit_prob = getattr(u, 'bs', 50) / 100.0
                            
                            # [FEATURE] Height Advantage
                            attacker_z = getattr(u, 'grid_z', 0)
                            target_z = getattr(target_unit, 'grid_z', 0)
                            z_diff = attacker_z - target_z
                            
                            if z_diff > 10:
                                base_hit_prob *= 1.15 # High Ground
                            elif z_diff < -10:
                                base_hit_prob *= 0.85 # Low Ground
                                
                            hit_prob = min(0.95, max(0.05, base_hit_prob))
                            if random.random() > hit_prob:
                                # Spawn with deviation for missed shot
                                deviation = random.uniform(-0.1, 0.1)
                            else:
                                deviation = 0.0

                            # [RANGE ENFORCEMENT] Calculate lifetime based on weapon range
                            # lifetime = distance / speed. We add a 20% buffer.
                            wpn_range = stats.get("Range", 24)
                            if dist > wpn_range: continue
                            
                            lifetime = (wpn_range / speed) * 1.2

                            # [FEATURE] Shield Flare & Ion Logic
                            shield_mult = stats.get("shield_damage_multiplier", 1.0)
                            hull_mult = stats.get("hull_damage_multiplier", 1.0)
                            
                            # Auto-detect Ion weapons if multipliers missing
                            if "ION" in cat and shield_mult == 1.0:
                                shield_mult = 3.0
                                hull_mult = 0.1

                            self.projectile_manager.spawn_projectile(
                                u, target_unit,
                                damage=raw_dmg,
                                ap=stats.get("AP", 0),
                                speed=speed,
                                projectile_type=proj_type,
                                target_comp=target_comp,
                                deviation=deviation,
                                lifetime=lifetime,
                                shield_mult=shield_mult,
                                hull_mult=hull_mult
                            )
                            
                            battle_state.log_event("shooting_fire", u.name, target_unit.name, f"Fired {wpn.name} ({proj_type})")

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
