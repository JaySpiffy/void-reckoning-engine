from typing import List, Dict, Optional, Any
from src.core import balance as bal
from src.utils.rng_manager import get_stream
from src.combat.calculators.combat_calculator import CombatCalculator

class WeaponExecutor:
    """Handles weapon firing and ability execution logic."""

    @staticmethod
    def execute_weapon_fire(attacker, defender, weapon_component, distance, grid, doctrine, attacker_mods, defender_mods, round_num, tracker=None, battle_stats=None):
        """
        Handles individual weapon firing logic.
        """
        w_stats = getattr(weapon_component, 'weapon_stats', None) or {"Range": 24, "Str": 4, "AP": 0}
        w_range = w_stats.get("Range", 24)
        
        # Doctrine Range Bonus
        if doctrine == "KITE":
            w_range += 5
            
        # Check Range
        if distance > w_range:
            print(f"DEBUG: Out of Range: Dist {distance} > Range {w_range}")
            return None
            
        # Check Arc
        w_arc = getattr(attacker, 'weapon_arcs', {}).get(weapon_component.name, "Dorsal")
        if not grid.check_weapon_arc(attacker, defender, w_arc):
            print(f"DEBUG: Bad Arc: {w_arc}")
            return None
            
        # Determine Armor Facing
        armor_hit = grid.get_armor_facing(attacker, defender)
        
        # Calculate Hit Chance
        bs = getattr(attacker, 'bs', 50) + attacker_mods.get("bs_mod", 0)
        if distance > bal.UNIT_BASE_RANGE:
            bs += bal.MOD_LONG_RANGE_PENALTY
        if getattr(attacker, 'is_suppressed', False):
            bs += bal.MOD_SUPPRESSION_BS_PENALTY
            
        # Phase 250: Accuracy Floor
        bs = max(5, bs)
            
        # Roll to Hit
        roll = get_stream("combat").randint(1, 100)
        hit_result = roll <= bs
        
        # Calculate detailed damage regardless of hit for logging purposes
        s_val = (w_stats.get("S", w_stats.get("Str", 4))) * 10 * w_stats.get("D", 1)
        ap_val = w_stats.get("AP", 0)
        w_type = w_stats.get("Type", "Kinetic")
        
        # Mitigation Breakdown
        mitigation_factors = {}
        
        # Base Mitigation
        base_mit = CombatCalculator.calculate_mitigation_v4(defender, ap_val, armor_override=armor_hit)
        mitigation_factors["armor_save"] = base_mit
        
        # Modifiers
        def_bonus = defender_mods.get("defense_mod", 0) / 100.0
        if def_bonus != 0:
            mitigation_factors["defense_mod"] = def_bonus
            
        if "Cover" in getattr(defender, 'abilities', {}):
            mitigation_factors["cover"] = bal.COVER_SAVE_IMPROVEMENT
        
        # Advanced Defense Modules
        def_tags = []
        if hasattr(defender, 'components'):
             for comp in defender.components:
                 if hasattr(comp, 'tags'):
                     def_tags.extend(comp.tags)
                 elif isinstance(comp, dict) and "tags" in comp:
                     def_tags.extend(comp["tags"])

        if "anti_energy" in def_tags and w_type in ["Energy", "Laser", "Plasma"]:
            base_mit = min(0.95, base_mit + 0.30)
            mitigation_factors["reflective_shield"] = "+30%"

        if "anti_kinetic" in def_tags and w_type in ["Kinetic", "Projectile", "Missile"]:
            base_mit = min(0.95, base_mit + 0.30)
            mitigation_factors["reactive_armor"] = "+30%"

        if "anti_exotic" in def_tags and w_type == "Exotic":
            base_mit = min(0.95, base_mit + 0.40)
            mitigation_factors["void_shield"] = "+40%"
        
        # Check for Shield Piercing
        w_tags = getattr(weapon_component, 'tags', [])
        if any(t in w_tags for t in ["shield_piercing", "polaron", "phaser"]):
             base_mit *= 0.5 
             mitigation_factors["shield_pierce"] = "50% ignored"
             
        # Melta Range Bonus
        if "melta" in w_tags and distance <= (w_range / 2.0):
             base_mit = max(0, base_mit - 0.2)
             s_val *= 1.5
             mitigation_factors["melta_bonus"] = "active"

        mit = min(0.95, base_mit + def_bonus)
        
        raw_dmg = s_val * (1.0 - mit) * bal.GLOBAL_DAMAGE_MULTIPLIER
        
        damage_breakdown = {
            "raw": s_val,
            "mitigated_pct": mit,
            "mitigated_amount": s_val * mit,
            "final": 0,
            "type": w_type,
            w_type.lower(): s_val,
            "mitigation_factors": mitigation_factors
        }

        if hit_result:
            final_dmg = max(1, raw_dmg * attacker_mods.get("dmg_mult", 1.0))
            damage_breakdown["final"] = final_dmg
            
            if battle_stats and attacker.faction in battle_stats:
                battle_stats[attacker.faction]["total_damage_dealt"] += final_dmg
            
            # Apply Damage
            s_dmg, h_dmg, _, dest_comp = defender.take_damage(final_dmg)
            
            # Exotic Side Effects
            w_tags = w_stats.get("tags", [])
            if not w_tags and hasattr(weapon_component, 'tags'): w_tags = weapon_component.tags
            
            if "ion" in w_tags or "emp" in w_tags:
                 if getattr(defender, 'current_shield', 0) > 0:
                     defender.take_damage(final_dmg * 1.5)
                 else:
                     defender.current_suppression = getattr(defender, 'current_suppression', 0) + 10
                     
            if "tesla" in w_tags:
                 if get_stream("combat").random() < 0.33:
                      defender.take_damage(final_dmg * 0.5)
                      
            if "radiation" in w_tags or "poison" in w_tags:
                 if hasattr(defender, 'current_morale'):
                      defender.current_morale = max(0, defender.current_morale - 5)
                 defender.current_suppression = getattr(defender, 'current_suppression', 0) + 5
                 
            if "nanite" in w_tags:
                 defender.base_armor = max(0, getattr(defender, 'base_armor', 0) - 1)

            is_kill = not defender.is_alive()
            
            if tracker:
                tracker.log_event(
                    "weapon_fire_detailed", attacker, defender, 
                    weapon=weapon_component,
                    hit_roll=roll,
                    hit_threshold=bs,
                    hit_result=True,
                    damage_breakdown=damage_breakdown,
                    armor_facing=armor_hit,
                    range=distance,
                    weapon_arc=w_arc,
                    killed=is_kill,
                    component_destroyed=dest_comp,
                    doctrine=doctrine
                )
                
                # [CINEMATIC LOGGING] Explicitly log hardpoint destruction for the text log narrative
                if dest_comp and hasattr(manager, 'log_event'):
                    manager.log_event("HARDPOINT_DESTROYED", attacker.name, defender.name, description=dest_comp.name)
                
            return {
                "damage": final_dmg,
                "is_kill": is_kill,
                "comp_destroyed": dest_comp
            }
        else:
            if tracker:
                 tracker.log_event(
                    "weapon_fire_detailed", attacker, defender, 
                    weapon=weapon_component,
                    hit_roll=roll,
                    hit_threshold=bs,
                    hit_result=False,
                    damage_breakdown=damage_breakdown,
                    armor_facing=armor_hit,
                    range=distance,
                    weapon_arc=w_arc
                )
        
        return None

    @staticmethod
    def execute_atomic_ability(source, target, ability_name, detailed_log=None, tracker=None) -> Dict[str, Any]:
        """
        Executes an ability using the Atomic Synthesis System.
        """
        if not hasattr(source, 'atomic_abilities') or ability_name not in source.atomic_abilities:
            return {"success": False, "reason": "No atomic data for ability"}
            
        power = source.atomic_abilities[ability_name]
        
        from src.core.payload_registry import PayloadRegistry
        registry = PayloadRegistry.get_instance()
        
        # We need the universe name, usually on source or faction
        uni = getattr(source, 'source_universe', 'base')
        
        payload_res = registry.execute_payload(ability_name, source, target, {"power": power}, universe=uni)
        
        cooldown = getattr(source, 'ability_cooldowns', {}).get(ability_name, 0)
        resources = {} 
        reason = "Standard Doctrine"
        
        if tracker:
            trace_data = {
                "source": source.name,
                "target": target.name,
                "ability": ability_name,
                "power_input": power,
                "universe": uni,
                "cooldown_remaining": cooldown,
                "resource_cost": resources,
                "selection_reason": reason,
                "intermediate_calculations": payload_res.get("debug_math", {})
            }
            tracker.log_atomic_trace(trace_data)

        if payload_res.get("effect_type") != "none":
            payload_res["success"] = True
            payload_res["applied"] = True
            desc = payload_res.get("description", "Effect applied")
            if detailed_log:
                detailed_log.write(f"[ABILITY] {source.name} {ability_name.upper()} -> {target.name}: {desc}\n")
            
            if tracker:
                tracker.log_event(
                    "ability_activation", source, target, 
                    ability_name=ability_name,
                    success=True,
                    power_level=power,
                    description=desc,
                    effect_type=payload_res.get("effect_type"),
                    cooldown_remaining=cooldown,
                    resource_cost=resources,
                    target_selection_reason=reason
                )
                
            return payload_res

        # Fallback Logic (Legacy)
        from src.core.universe_data import UniverseDataManager
        ability_db = UniverseDataManager.get_instance().get_ability_database()
        ability_def = ability_db.get(ability_name, {})
        
        effect_type = ability_def.get("effect_type", "unknown")
        result = {"success": True, "effect": effect_type, "power": power}
        applied = False
        description = ""
        
        # Simplified DNA access for legacy fallback
        atom_mass = getattr(source, 'atom_mass', 0)
        atom_energy = getattr(source, 'atom_energy', 0)
        atom_stability = getattr(source, 'atom_stability', 0)
        atom_information = getattr(source, 'atom_information', 0)
        atom_cohesion = getattr(source, 'atom_cohesion', 0)
        atom_will = getattr(source, 'atom_will', 0)

        if effect_type == "mobility_suppression":
            target_resistance = (atom_mass * 50) + (atom_energy * 10)
            if power > target_resistance:
                target.is_suppressed = True
                applied = True
                description = f"Suppressed (Pow {power:.0f} > Res {target_resistance:.0f})"
            else:
                applied = False
                description = "Resisted"

        elif effect_type == "system_disruption":
            target_res = (atom_stability * 15) + (atom_information * 5)
            if power > target_res:
                 target.is_suppressed = True
                 applied = True
                 description = "Systems Disabled"
            else:
                 applied = False
                 
        elif effect_type == "life_suppression":
            target_res = (atom_cohesion * 20) + (atom_will * 10)
            if power > target_res:
                 damage = power * 0.1
                 target.take_damage(damage)
                 applied = True
                 description = "Critical Damage"
            else:
                 applied = False
                 
        elif effect_type == "flux_interaction":
            target_res = (atom_will * 15)
            if power > target_res:
                target.base_leadership = getattr(target, 'base_leadership', 50) - 10
                applied = True
                description = "Mental Disruption"
            else:
                 applied = False
        
        result["applied"] = applied
        result["description"] = description
        
        if tracker:
            tracker.log_event(
                "ability_activation", source, target, 
                ability_name=ability_name,
                success=applied,
                power_level=power,
                description=description,
                effect_type=effect_type
            )
            
        return result
