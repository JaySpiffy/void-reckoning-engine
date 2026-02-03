import random
from typing import Dict, Any, Optional, List
from src.utils.profiler import profile_method
from src.combat.execution.weapon_executor import WeaponExecutor

class AbilityManager:
    """
    Manages the execution of active abilities in combat.
    Handles payload processing (damage, buffs, debuffs, heals, etc.)
    and resource cost validation.
    """
    
    def __init__(self, registry: Dict[str, Any] = None):
        self.registry = registry or {}
        self._rng = random.Random()

    def set_registry(self, registry: Dict[str, Any]):
        self.registry = registry
        
    def set_rng_seed(self, seed: int):
        self._rng.seed(seed)

    def _check_cooldown(self, source, ability_id: str, context: Optional[Dict[str, Any]]) -> bool:
        """
        Checks if the ability is on cooldown.
        Returns True if ready, False if on cooldown.
        """
        if not hasattr(source, "cooldowns"):
            return True
            
        ready_at = source.cooldowns.get(ability_id, 0.0)
        
        current_time = 0.0
        if context and "battle_state" in context:
            state = context["battle_state"]
            if hasattr(state, "total_sim_time"):
                current_time = state.total_sim_time
                
        return current_time >= ready_at

    def _apply_cooldown(self, source, ability_id: str, ability_def: Dict[str, Any], context: Optional[Dict[str, Any]]) -> None:
        """Sets the cooldown timestamp for the ability."""
        if not hasattr(source, "cooldowns"):
            source.cooldowns = {}
            
        current_time = 0.0
        if context and "battle_state" in context:
            state = context["battle_state"]
            if hasattr(state, "total_sim_time"):
                current_time = state.total_sim_time
                
        # Get duration from def or default to 5s to prevent spam
        duration = ability_def.get("cooldown", 5.0)
        source.cooldowns[ability_id] = current_time + duration

    @profile_method
    def execute_ability(self, source, target, ability_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes a single ability from source to target.
        """
        if ability_id not in self.registry:
            return {"success": False, "reason": f"Ability {ability_id} not found in registry"}
            
        ability_def = self.registry[ability_id]
        payload_type = ability_def.get("payload_type", "damage")
        
        # Cooldown Check
        if not self._check_cooldown(source, ability_id, context):
             return {"success": False, "reason": "Ability on cooldown"}
        
        # Resource Check
        if not self._check_cost(source, ability_def, context):
             return {"success": False, "reason": "Insufficient resources"}

        result = {
            "success": True, 
            "ability_id": ability_id,
            "source": source.name,
            "target": target.name,
            "payload_type": payload_type,
            "applied": False
        }

        # Dispatch to handler
        if payload_type == "damage":
            self._handle_damage(source, target, ability_def, result, context)
        elif payload_type == "buff":
            self._handle_buff(source, target, ability_def, result, context)
        elif payload_type == "debuff":
            self._handle_debuff(source, target, ability_def, result)
        elif payload_type == "heal":
            self._handle_heal(source, target, ability_def, result, context)
        elif payload_type == "stun":
            self._handle_stun(source, target, ability_def, result)
        elif payload_type == "aoe_damage":
            self._handle_aoe_damage(source, target, ability_def, result, context)
        elif payload_type == "shield_regen":
             self._handle_shield_regen(source, target, ability_def, result)
        elif payload_type == "drain":
             self._handle_drain(source, target, ability_def, result)
        elif payload_type == "capture":
             self._handle_capture(source, target, ability_def, result)
        elif payload_type == "teleport":
             self._handle_teleport(source, target, ability_def, result, context)
        elif payload_type == "mind_control":
             self._handle_mind_control(source, target, ability_def, result, context)
        
        # --- Total War / EaW Specific Payloads (Phase 30) ---
        elif payload_type == "rally":
             self._handle_rally(source, target, ability_def, result)
        elif payload_type == "charge":
             self._handle_charge(source, target, ability_def, result)
        elif payload_type == "guard_mode":
             self._handle_guard_mode(source, target, ability_def, result)
        elif payload_type == "repair":
             self._handle_heal(source, target, ability_def, result) # Reuse heal logic

        else:
            result["success"] = False
            result["reason"] = f"Unknown payload type: {payload_type}"
            
        # Hook for Mechanics Engine if context is provided
        if result["success"]:
            # Apply Cooldown
            self._apply_cooldown(source, ability_id, ability_def, context)
            
            if context and "mechanics_engine" in context:
                 engine = context["mechanics_engine"]
                 if engine:
                      # Trigger 'on_ability_use' mechanic hook
                      mech_context = {
                          "caster": source,
                          "target": target,
                          "ability_id": ability_id,
                          "result": result
                      }
                      # We need the faction name of the caster
                      manager = context.get("battle_state")
                      faction_name = None
                      if manager:
                           for f, units in manager.armies_dict.items():
                                if source in units:
                                     faction_name = f
                                     break
                      
                      if faction_name:
                           engine.apply_mechanics(faction_name, "on_ability_use", mech_context)

        return result

    def get_random_applicable_ability(self, unit) -> Optional[str]:
        """
        Returns a random ability ID that is either a new Level 1 ability
        or an upgrade to an existing ability.
        """
        domain = getattr(unit, 'domain', 'ground')
        current_abilities = getattr(unit, 'abilities', {})
        
        # 1. Identify Upgradeable Abilities
        upgrade_candidates = []
        for ab_id in current_abilities:
            # Check if this is a tiered ability (ends in _vX)
            if "_v" in ab_id:
                try:
                    base, ver = ab_id.rsplit("_v", 1)
                    next_ver = int(ver) + 1
                    next_id = f"{base}_v{next_ver}"
                    if next_id in self.registry:
                        upgrade_candidates.append(next_id)
                except ValueError:
                    continue

        # 2. Identify Discoverable (Level 1) Abilities
        discovery_candidates = []
        for ab_id, ab_def in self.registry.items():
            # Only discover Level 1 versions
            if not ab_id.endswith("_v1"):
                continue
                
            # Strip _v1 to see if we already have any version of this base ability
            base = ab_id.rsplit("_v", 1)[0]
            already_owned = any(owned.startswith(base) for owned in current_abilities)
            if already_owned:
                continue
                
            ab_category = ab_def.get("category", "ground")
            if ab_category == domain:
                discovery_candidates.append(ab_id)
            elif domain == "space" and ab_category == "ship":
                discovery_candidates.append(ab_id)
            elif domain == "ground" and ab_category == "regiment":
                discovery_candidates.append(ab_id)
                
        # 3. Combine pools (Weighted: Use probability from balance)
        from src.core.balance import UNIT_LEVEL_UP_UPGRADE_PROBABILITY
        if upgrade_candidates and (not discovery_candidates or self._rng.random() < UNIT_LEVEL_UP_UPGRADE_PROBABILITY):
            return self._rng.choice(upgrade_candidates)
        elif discovery_candidates:
            return self._rng.choice(discovery_candidates)
        elif upgrade_candidates: # Fallback if no new discoveries left
            return self._rng.choice(upgrade_candidates)
            
        return None

    def _handle_damage(self, source, target, ability_def, result, context=None):
        """Standard direct damage payload."""
        # Base damage
        damage = ability_def.get("damage", 10) # Fallback to 10
        
        
        # Apply Logic:
        # Check source modifiers
        if hasattr(source, "temp_modifiers"):
             mult = source.temp_modifiers.get("ability_power_mult", 1.0)
             damage *= mult
              
        final_damage = max(1, int(damage))
        
        if hasattr(target, "take_damage"):
            damage_result = target.take_damage(final_damage)
            # Support both (s_dmg, h_dmg, is_destroyed, comp) tuple and simple boolean
            if isinstance(damage_result, tuple):
                killed = damage_result[2]
            else:
                killed = bool(damage_result)
                
            result["damage"] = final_damage
            result["killed"] = killed
            result["applied"] = True
            result["description"] = f"Dealt {final_damage} damage"
            
            # Award XP to source
            from src.core.balance import UNIT_XP_AWARD_DAMAGE_RATIO, UNIT_XP_AWARD_KILL
            if hasattr(source, "gain_xp"):
                source.gain_xp(final_damage * UNIT_XP_AWARD_DAMAGE_RATIO, context)
                if killed:
                    source.gain_xp(UNIT_XP_AWARD_KILL, context)
            
            # Phase 250: Update Battle Stats for stalemate detection
            manager = context.get("battle_state")
            if manager and hasattr(manager, 'battle_stats') and source.faction in manager.battle_stats:
                manager.battle_stats[source.faction]["total_damage_dealt"] += final_damage
        else:
            result["applied"] = False
            result["reason"] = "Target cannot take damage"

    def _handle_buff(self, source, target, ability_def, result, context=None):
        """Applies temporary stat modifiers."""
        # Define what to buff
        # e.g. "effects": {"armor_mult": 1.2, "duration": 2}
        effects = ability_def.get("effects", {}).copy() # Use copy to modify!
        if not effects:
             # Default fallback if registry incomplete
             effects = {"damage_mult": 1.1, "duration": 1}

                       
        if hasattr(target, "apply_temporary_modifiers"):
             target.apply_temporary_modifiers(effects)
             result["applied"] = True
             result["description"] = f"Applied buffs: {effects}"
        else:
             result["applied"] = False

    def _handle_debuff(self, source, target, ability_def, result):
        """Applies negative modifiers."""
        effects = ability_def.get("effects", {})
        if not effects:
             effects = {"speed_mult": 0.5, "duration": 1}
             
        if hasattr(target, "apply_temporary_modifiers"):
             target.apply_temporary_modifiers(effects)
             result["applied"] = True
             result["description"] = f"Applied debuffs: {effects}"
        else:
             result["applied"] = False

    def _handle_heal(self, source, target, ability_def, result, context=None):
        """Restores HP."""
        heal_amount = ability_def.get("heal", 20)
        if hasattr(target, "heal"):
             restored = target.heal(heal_amount)
             result["healed"] = restored
             result["applied"] = True
             result["description"] = f"Healed {restored} HP"
        elif hasattr(target, "current_hp"):
             old_hp = target.current_hp
             max_hp = getattr(target, "max_hp", target.current_hp)
             target.current_hp = min(max_hp, target.current_hp + heal_amount)
             restored = target.current_hp - old_hp
             result["healed"] = restored
             result["applied"] = True
             result["description"] = f"Healed {restored} HP"

        # Award XP to source
        from src.core.balance import UNIT_XP_AWARD_HEAL_RATIO
        if restored > 0 and hasattr(source, "gain_xp"):
            source.gain_xp(restored * UNIT_XP_AWARD_HEAL_RATIO, context)

    def _handle_stun(self, source, target, ability_def, result):
        """Skips target's turn or reduces action points."""
        # Implementation depends on unit state flags
        if hasattr(target, "stunned"):
             target.stunned = True
             result["applied"] = True
             result["description"] = "Target stunned"
        else:
             # Fallback: Reduced movement/actions
             if hasattr(target, "apply_temporary_modifiers"):
                  target.apply_temporary_modifiers({"stunned": True, "duration": 1})
                  result["applied"] = True
                  result["description"] = "Target stasis applied"

    def _handle_aoe_damage(self, source, target, ability_def, result, context):
        """Area of Effect damage."""
        damage = ability_def.get("damage", 10)
        radius = ability_def.get("radius", 2) # Grid cells radius
        
        # Requires grid access from context
        grid = context.get("grid") if context else None
        spatial_index = context.get("spatial_index") if context else None
        
        if not grid:
             # Fallback to single target if no grid context
             self._handle_damage(source, target, ability_def, result)
             result["description"] += " (AOE Failed - No Grid)"
             return

        # Find targets in radius
        # Simple distance check vs all or spatial index
        affected_units = []
        center_x, center_y = target.grid_x, target.grid_y
        
        # Optimization: Scan spatial buckets
        # For now, just simplistic scan if no spatial index
        # Assuming we can get 'all_units' from context or grid?
        # Grid usually doesn't store list of all units easily accessible without scan?
        # Actually tactical_grid has 'grid' array.
        
        affected_count = 0
        total_dmg = 0
        
        # Naive scan for MVP (Optimization later)
        # We need a list of potential targets. 'enemies' list from context?
        enemies = context.get("enemies", [])
        friendly_fire = ability_def.get("friendly_fire", False)
        
        potential_targets = enemies
        if friendly_fire:
             # Add allies?
             pass
             
        for unit in potential_targets:
             dist = grid.get_distance_coords(center_x, center_y, unit.grid_x, unit.grid_y)
             if dist <= radius:
                  # Apply damage
                  if hasattr(unit, "take_damage"):
                       unit.take_damage(damage)
                       affected_count += 1
                       total_dmg += damage
        
        # Phase 250: Update Battle Stats for stalemate detection
        manager = context.get("battle_state")
        if manager and hasattr(manager, 'battle_stats') and source.faction in manager.battle_stats:
            manager.battle_stats[source.faction]["total_damage_dealt"] += total_dmg

        result["applied"] = True
        result["affected_count"] = affected_count
        result["total_damage"] = total_dmg
        result["description"] = f"AOE Dealt {damage} to {affected_count} units"

    def _handle_shield_regen(self, source, target, ability_def, result):
        """Restores Shields."""
        amount = ability_def.get("amount", 50)
        if hasattr(target, "regenerate_shields"): # Existing method?
             # Or direct attribution
             if hasattr(target, "current_shields") and hasattr(target, "max_shields"):
                  target.current_shields = min(target.max_shields, target.current_shields + amount)
                  result["applied"] = True
                  result["description"] = f"Restored {amount} shields"
             else:
                  result["applied"] = False
        else:
             result["applied"] = False
             
    def _check_cost(self, source, ability_def, context):
        """Checks if the faction has enough resources and deducts them."""
        cost = ability_def.get("cost", {})
        if not cost: return True
        
        # We need the faction object
        faction = context.get("faction") if context else None
        
        # If no faction provided (mock test?), skip cost or fail?
        # For now, if no faction, assume free/pass for testing unless strict mode
        if not faction: 
            # Could check unit costs even if no faction?
            pass
            
        # Distinguish between Unit Resources (Energy, Fuel) and Faction Resources (CP, Conviction)
        unit_resources = ["energy", "fuel", "ammo"]
        
        for res, amount in cost.items():
            if res in unit_resources:
                # Check Unit
                u_res = getattr(source, "resources", {})
                current = u_res.get(res, 100) # Default to 100 for now if missing
                if current < amount:
                    return False
                # Deduct
                if not hasattr(source, "resources"): source.resources = {}
                source.resources[res] = current - amount
            else:
                # Check Faction
                if not faction or isinstance(faction, str):
                    # Cannot deduct from string or None
                    # If strict, fail. If loose (test), pass?
                    # Let's fail if cost exists but no faction object
                    print(f"DEBUG: Cannot pay {res} cost without valid faction object (got {type(faction)})")
                    return False
                    
                if not hasattr(faction, "custom_resources"):
                     faction.custom_resources = {}
                     
                current = faction.custom_resources.get(res, 0)
                if current < amount:
                     return False
                
                faction.custom_resources[res] -= amount
                
        return True

    def _handle_drain(self, source, target, ability_def, result):
        """Deals damage and heals source."""
        damage = ability_def.get("damage", 10)
        heal_ratio = ability_def.get("heal_ratio", 1.0)
        final_damage = max(1, int(damage))
        if hasattr(target, "take_damage"):
            killed = target.take_damage(final_damage)
            result["damage"] = final_damage
            result["killed"] = killed
            result["applied"] = True
            heal_amount = int(final_damage * heal_ratio)
            if hasattr(source, "heal"):
                healed = source.heal(heal_amount)
            elif hasattr(source, "current_hp"):
                old = source.current_hp
                mx = getattr(source, "max_hp", source.current_hp)
                source.current_hp = min(mx, source.current_hp + heal_amount)
                healed = source.current_hp - old
            result["healed"] = healed
            result["description"] = f"Drained {final_damage} HP, healed {healed}"
            
            # Phase 250: Update Battle Stats for stalemate detection
            manager = context.get("battle_state")
            if manager and hasattr(manager, 'battle_stats') and source.faction in manager.battle_stats:
                manager.battle_stats[source.faction]["total_damage_dealt"] += final_damage
        else:
            result["applied"] = False

    def _handle_capture(self, source, target, ability_def, result):
        """Attempts to capture target."""
        threshold = ability_def.get("capture_threshold", 0.2)
        hp_ratio = 1.0
        if hasattr(target, "current_hp") and hasattr(target, "max_hp"):
             hp_ratio = target.current_hp / target.max_hp
        if hp_ratio <= threshold:
             target.is_destroyed = True
             result["captured"] = True
             result["applied"] = True
             result["description"] = "Unit Boarded and Captured"
        else:
             result["applied"] = False
             result["reason"] = f"Target HP too high ({hp_ratio:.1%})"

    def _handle_teleport(self, source, target, ability_def, result, context):
        """Teleports unit."""
        grid = context.get("grid") if context else None
        if not grid:
             result["applied"] = False
             return
        range_val = ability_def.get("range", 10)
        import random
        subject = source
        new_x, new_y = -1, -1
        cx, cy = subject.grid_x, subject.grid_y
        for _ in range(10):
             dx = random.randint(-range_val, range_val)
             dy = random.randint(-range_val, range_val)
             tx, ty = cx + dx, cy + dy
             if grid.is_valid_tile(tx, ty) and not grid.get_unit_at(tx, ty):
                 new_x, new_y = tx, ty
                 break
        if new_x != -1:
             grid.move_unit(subject, new_x, new_y)
             result["applied"] = True
             result["description"] = f"Teleported to ({new_x}, {new_y})"
        else:
             result["applied"] = False

    def _handle_mind_control(self, source, target, ability_def, result, context):
        """Confusion/Mind Control."""
        grid = context.get("grid")
        if not grid:
             result["applied"] = False
             return
        potential_victims = context.get("enemies", [])
        friendly_fire_target = None
        min_dist = 999
        for ally in potential_victims:
             if ally == target: continue
             dist = grid.get_distance(target, ally)
             if dist < min_dist:
                  min_dist = dist
                  friendly_fire_target = ally
        if friendly_fire_target:
             weapon = next((c for c in target.components if c.type == "Weapon"), None)
             if weapon:
                  dmg_res = WeaponExecutor.execute_weapon_fire(target, friendly_fire_target, weapon, min_dist, grid, "Aggressive", {}, {}, 0, None)
                  result["applied"] = True
                  result["damage"] = dmg_res.get("damage", 0)
                  result["description"] = f"Confused! Attacked {friendly_fire_target.name}"
             else:
                  result["applied"] = False
                  result["reason"] = "No weapon"
        else:
             result["applied"] = False

    def _handle_rally(self, source, target, ability_def, result):
        """Active morale boost and regrouping."""
        boost = ability_def.get("morale_boost", 50.0)
        if hasattr(target, "morale_current"):
            target.morale_current = min(target.morale_max, target.morale_current + boost)
            if target.morale_state == "Routing" and target.morale_current > 30:
                target.morale_state = "Steady" # Regrouped!
            result["applied"] = True
            result["description"] = f"Rallied: +{boost} morale"
        else:
            result["applied"] = False


    def _handle_guard_mode(self, source, target, ability_def, result):
        """Locks unit in place with massive defense bonuses."""
        duration = ability_def.get("duration", 10)
        effects = {
            "movement_speed_mult": 0.0,
            "defense_mult": 2.5,
            "flank_immunity": True,
            "duration": duration
        }
        if hasattr(target, "apply_temporary_modifiers"):
            target.apply_temporary_modifiers(effects)
            result["applied"] = True
            result["description"] = "Guard Mode Active: Defense tripled, Movement halted."
        else:
            result["applied"] = False

    def _handle_charge(self, source, target, ability_def, result):
        """Applies charge bonus."""
        duration = ability_def.get("duration", 5)
        # Apply speed and damage mods
        mods = {
            "movement_speed_mult": 1.5,
            "damage_mult": 1.25,
            "impact_damage_mult": 2.0,
            "duration": duration,
            "ability_name": "Charge"
        }
        if hasattr(target, "apply_temporary_modifiers"):
             target.apply_temporary_modifiers(mods)
             result["applied"] = True
             result["description"] = f"Charge! Speed and Damage boosted for {duration}s"
        else:
             result["applied"] = False

