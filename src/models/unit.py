from typing import List, Dict, Any, Optional, Tuple
import weakref
import math
from src.combat.components.health_component import HealthComponent
from src.combat.components.armor_component import ArmorComponent
from src.combat.components.weapon_component import WeaponComponent
from src.combat.components.morale_component import MoraleComponent
from src.combat.components.trait_component import TraitComponent
from src.combat.components.movement_component import MovementComponent
from src.combat.components.stats_component import StatsComponent
from src.combat.components.crew_component import CrewComponent

class Unit:
    """
    Lightweight Component-Based Unit Entity.
    """
    def __init__(
        self,
        name: str,
        faction: str,
        unit_class: Optional[str] = None,
        domain: Optional[str] = None,
        components: Optional[List[Any]] = None,
        **kwargs
    ):
        self.name = name
        self.faction = faction
        self.unit_class = unit_class or kwargs.get("unit_class")
        self.domain = domain or kwargs.get("domain")
        self.blueprint_id = kwargs.get("blueprint_id") or f"blueprint_{name.lower().replace(' ', '_')}"
        self.cost = kwargs.get("cost", 0)
        self.rank = kwargs.get("rank", "Regular")
        self.level = kwargs.get("level", 1)
        self.experience = kwargs.get("experience", 0.0)
        self.xp_gain_rate = kwargs.get("xp_gain_rate", 1.0)
        self.mass = kwargs.get("mass", 1.0) # [FEATURE] Unit Mass
        self.max_members = kwargs.get("max_members", 1) # [FEATURE] Squadrons
        self._abilities = kwargs.get("abilities", {})
        
        # Composition: Components are injected
        self.health_comp: Optional[HealthComponent] = None
        self._fleet_ref = None # Weakref to parent fleet
        self.armor_comp: Optional[ArmorComponent] = None
        self.weapon_comps: List[WeaponComponent] = []
        self.morale_comp: Optional[MoraleComponent] = None
        self.trait_comp: Optional[TraitComponent] = None
        self.movement_comp: Optional[MovementComponent] = None
        self.stats_comp: Optional[StatsComponent] = None
        self.crew_comp: Optional[CrewComponent] = None
        
        self.components = [] 
        self.current_stance = "STANCE_BALANCED"
        
        # Register components
        if components:
            for comp in components:
                self.add_component(comp)
                
        # Legacy Fallback: If components missing, try to build from kwargs
        if not self.health_comp and ("hp" in kwargs or "base_hp" in kwargs):
            hp = kwargs.get("hp", kwargs.get("base_hp", 100))
            self.add_component(HealthComponent(hp, regen=kwargs.get("regen", 0), max_shield=kwargs.get("shield", 0)))
            
        if not self.armor_comp and "armor" in kwargs:
            self.add_component(ArmorComponent(kwargs.get("armor", 0)))
            
        if not self.stats_comp and any(k in kwargs for k in ["ma", "md", "damage", "armor", "hp", "base_hp"]):
             self.add_component(StatsComponent(
                 ma=kwargs.get("ma", 50),
                 md=kwargs.get("md", 50),
                 damage=kwargs.get("damage", 10),
                 armor=kwargs.get("armor", 0),
                 hp=kwargs.get("hp", kwargs.get("base_hp", 100)),
                 leadership=kwargs.get("leadership", 50)
             ))
        self.cooldowns = {} # Map[ability_id] -> ready_at_timestamp
        
        # Crew Fallback for Ships
        if not self.crew_comp and self.domain == "space":
            from src.core.balance import HULL_BASE_STATS
            hull_stats = HULL_BASE_STATS.get(self.unit_class, {"hp": 100})
            max_crew = hull_stats.get("crew", 100)
            self.add_component(CrewComponent(max_crew, troop_value=hull_stats.get("troop_value", 10)))

        # Core Stats
        self.max_hp_base = kwargs.get("max_hp", 100.0)

    def add_component(self, component: Any) -> None:
        """Adds a component to unit."""
        component_type = type(component).__name__
        
        if component_type == 'HealthComponent':
            self.health_comp = component
        elif component_type == 'ArmorComponent':
            self.armor_comp = component
        elif component_type == 'WeaponComponent':
            self.weapon_comps.append(component)
        elif component_type == 'MoraleComponent':
            self.morale_comp = component
        elif component_type == 'TraitComponent':
            self.trait_comp = component
        elif component_type == 'MovementComponent':
            self.movement_comp = component
        elif component_type == 'StatsComponent':
            self.stats_comp = component
        elif component_type == 'CrewComponent':
            self.crew_comp = component
            
        self.components.append(component)

    def take_damage(self, amount: float, impact_angle: float = 0, target_component=None, ignore_mitigation=False, shield_mult: float = 1.0, hull_mult: float = 1.0):
        """
        Delegates damage handling to components.
        Returns: (shield_dmg, hull_dmg, is_unit_destroyed, destroyed_component)
        """
        # 1. Apply armor mitigation
        mitigated_amount = amount
        if self.armor_comp and not ignore_mitigation:
            armor_value = self.armor_comp.get_armor_for_facing(impact_angle)
            mitigation = max(0, armor_value / 5.0)
            mitigated_amount = max(0, amount - mitigation)
            
        # [PHASE 32] Fortress Tag Damage Reduction (50% reduction for super-heavy static targets)
        if "Fortress" in self.abilities.get("Tags", []):
            mitigated_amount *= 0.5
            
        # 2. Targeted Component Damage (EaW Style)
        destroyed_component = None
        if target_component and hasattr(target_component, 'take_damage'):
             # Redirect a portion of damage to the component? Or all?
             # For now, all damage goes to component AND hull (structural integrity).
             # Standard EaW: Component has its own HP. Hull has its own.
             c_destroyed = target_component.take_damage(mitigated_amount)
             if c_destroyed:
                  destroyed_component = target_component
        
        # 3. Apply hull/shield damage with Multipliers (Ion Cannon Logic)
        s_dmg, h_dmg, is_destroyed = 0.0, 0.0, False
        if self.health_comp:
            if shield_mult == 1.0 and hull_mult == 1.0:
                 # Standard path
                 s_dmg, h_dmg, is_destroyed = self.health_comp.take_damage(mitigated_amount)
            else:
                 # Complex path
                 current_shield = self.health_comp.current_shield
                 
                 # Calculate potential shield damage
                 s_potential = mitigated_amount * shield_mult
                 
                 # Amount actually absorbed by shield
                 s_absorbed = min(current_shield, s_potential)
                 
                 # Determine remaining "energy" ratio to pass to hull
                 # If shield took all damage, ratio is 0. If no shield, ratio is 1.
                 remainder_ratio = 1.0
                 if s_potential > 0:
                     remainder_ratio = (s_potential - s_absorbed) / s_potential
                 else:
                     remainder_ratio = 0.0
                     
                 # Remaining base damage
                 remaining_base = mitigated_amount * remainder_ratio
                 h_potential = remaining_base * hull_mult
                 
                 s_dmg, h_dmg, is_destroyed = self.health_comp.apply_specific_damage(s_absorbed, h_potential)

            # Update morale
            if self.morale_comp:
                self.morale_comp.take_damage(h_dmg)
                
        if h_dmg > 0 or s_dmg > 0:
            self.invalidate_cache()
                
        return s_dmg, h_dmg, is_destroyed, destroyed_component

    def is_ship(self) -> bool:
        """Returns True if the unit is a ship/voidcraft."""
        return self.domain == "space"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes unit state (Save V2 compatible)."""
        data = {
            "name": self.name,
            "faction": self.faction,
            "unit_type": self.__class__.__name__,
            "extra_data": {
                "unit_class": self.unit_class,
                "domain": self.domain,
                "blueprint_id": self.blueprint_id,
                "level": self.level,
                "experience": self.experience,
                "xp_gain_rate": self.xp_gain_rate
            }
        }
        
        if self.health_comp: data["health_comp"] = self.health_comp.to_dict()
        if self.armor_comp: data["armor_comp"] = self.armor_comp.to_dict()
        if self.morale_comp: data["morale_comp"] = self.morale_comp.to_dict()
        if self.trait_comp: data["trait_comp"] = self.trait_comp.to_dict()
        if self.movement_comp: data["movement_comp"] = self.movement_comp.to_dict()
        if self.stats_comp: data["stats_comp"] = self.stats_comp.to_dict()
        if self.weapon_comps:
            data["weapon_comps"] = [w.to_dict() for w in self.weapon_comps]
            
        return data

    def is_alive(self):
        if self.crew_comp and self.crew_comp.is_hulk:
            return False
        return self.health_comp.is_alive() if self.health_comp else False

    @property
    def troop_defense(self) -> int:
        """Returns the effective troop defense value including stance bonuses."""
        if not self.crew_comp:
            return 0
        base = self.crew_comp.troop_value
        if self.current_stance == "STANCE_CALL_TO_ARMS":
            from src.core import balance as bal
            base += bal.STANCE_CALL_TO_ARMS_TROOP_BONUS
        return int(base)

    def _calculate_strength(self) -> int:
        """Internal strength calculation logic."""
        # Base power from cost or power_rating
        base_power = getattr(self, "power_rating", self.cost * 0.1)
        
        # Scale by health
        health_ratio = 1.0
        if self.health_comp and self.health_comp.max_hp > 0:
            health_ratio = self.health_comp.current_hp / self.health_comp.max_hp
            
        # Combine with stats
        stats_mult = 1.0
        if self.stats_comp:
            # Average of offensive stats as a multiplier
            # Using __getattr__ for ma, md, damage
            # Note: Unit class might not expose ma/md directly if they are in stats_comp.
            # Safe access via stats_comp directly
            ma = self.stats_comp.ma
            md = self.stats_comp.md
            damage = self.stats_comp.damage
            stats_mult = (ma + md + damage) / 150.0 # Normalized around 50s
            
        return max(1, int(base_power * health_ratio * stats_mult))

    @property
    def strength(self) -> int:
        """Calculates effective combat power of this unit (Cached)."""
        if hasattr(self, '_cached_strength'):
            return self._cached_strength
            
        self._cached_strength = self._calculate_strength()
        return self._cached_strength

    def invalidate_cache(self):
        """Invalidates cached calculated values and notifies parent fleet."""
        if hasattr(self, '_cached_strength'):
            del self._cached_strength
        if self.fleet:
            self.fleet.invalidate_caches()

    def regenerate_infantry(self) -> Tuple[bool, int]:
        """Proxy for health regeneration. Returns (was_active, amount_restored)."""
        if not self.health_comp or self.health_comp.regen <= 0:
            return False, 0
            
        old_hp = self.health_comp.current_hp
        self.health_comp.regenerate()
        amount = int(self.health_comp.current_hp - old_hp)
        
        if amount > 0:
            self.invalidate_cache()
            return True, amount
        return False, 0

    def is_ship(self) -> bool:
        """Returns True if this unit is a naval/space vessel."""
        return False

    def regenerate_shields(self) -> float:
        """Regenerates shields via health component."""
        if self.health_comp:
            return self.health_comp.regenerate_shields()
        return 0.0

    # --- Legacy Property Proxies (For compatibility) ---
    @property
    def base_hp(self): return self.stats_comp.base_hp if self.stats_comp else (self.health_comp.max_hp if self.health_comp else 0)
    @base_hp.setter
    def base_hp(self, v): 
        if self.stats_comp: self.stats_comp.base_hp = v
        if self.health_comp: self.health_comp.max_hp = v

    @property
    def max_hp(self): return self.health_comp.max_hp if self.health_comp else 0
    @max_hp.setter
    def max_hp(self, v): 
        if self.health_comp: 
            self.health_comp.max_hp = v
            self.invalidate_cache()

    @property
    def current_hp(self): return self.health_comp.current_hp if self.health_comp else 0
    @current_hp.setter
    def current_hp(self, v): 
        if self.health_comp: 
            self.health_comp.current_hp = v
            self.invalidate_cache()

    @property
    def regen_hp_per_turn(self): return self.health_comp.regen if self.health_comp else 0
    @regen_hp_per_turn.setter
    def regen_hp_per_turn(self, v):
        if self.health_comp: self.health_comp.regen = v

    @property
    def base_armor(self): return self.stats_comp.base_armor if self.stats_comp else (self.armor_comp.base_armor if self.armor_comp else 0)
    @base_armor.setter
    def base_armor(self, v):
        if self.stats_comp: self.stats_comp.base_armor = v
        if self.armor_comp: self.armor_comp.base_armor = v

    @property
    def armor(self): return self.base_armor
    @armor.setter
    def armor(self, v): 
        self.base_armor = v
        self.invalidate_cache()

    @property
    def traits(self): return self.trait_comp.traits if self.trait_comp else []
    @traits.setter
    def traits(self, v): 
        if self.trait_comp: self.trait_comp.traits = v

    @property
    def abilities(self):
        # 1. Start with trait-based abilities
        abs = {}
        if self.trait_comp:
            abs = self.trait_comp.abilities.copy()
        else:
            abs = getattr(self, '_abilities', {}).copy()
            
        # 2. Dynamically add abilities from components (e.g., Boarding Tools)
        for comp in self.weapon_comps:
            if hasattr(comp, 'tags') and 'boarding' in comp.tags:
                # Map tags/stats to ability definitions
                if 'pods' in comp.tags:
                    abs['Boarding Pods'] = {
                        "type": "boarding",
                        "payload_type": "boarding",
                        "range": comp.weapon_stats.get("range", 25),
                        "atk": comp.weapon_stats.get("troop_damage", 30),
                        "pd_intercept": comp.weapon_stats.get("pd_intercept_chance", 0.4)
                    }
                elif 'teleportation' in comp.tags:
                    abs['Lightning Strike'] = {
                        "type": "boarding",
                        "payload_type": "boarding",
                        "range": comp.weapon_stats.get("range", 15),
                        "atk": comp.weapon_stats.get("troop_damage", 20),
                        "shield_gate": True
                    }
                elif 'boats' in comp.tags:
                    abs['Assault Boats'] = {
                        "type": "boarding",
                        "payload_type": "boarding",
                        "range": comp.weapon_stats.get("range", 60),
                        "atk": comp.weapon_stats.get("troop_damage", 25),
                        "pd_intercept": comp.weapon_stats.get("pd_intercept_chance", 0.6)
                    }
        
        return abs
    @abilities.setter
    def abilities(self, v):
        if self.trait_comp: self.trait_comp.abilities = v
        self._abilities = v
        
    @property
    def authentic_weapons(self):
        # Infer from weapon components
        return [w.name for w in self.weapon_comps] if self.weapon_comps else []

    @property
    def current_suppression(self): return self.morale_comp.suppression if self.morale_comp else 0
    @current_suppression.setter
    def current_suppression(self, v): 
        if self.morale_comp: self.morale_comp.suppression = v

    @property
    def leadership(self): return self.morale_comp.leadership if self.morale_comp else 7
    @leadership.setter
    def leadership(self, v):
        if self.morale_comp: self.morale_comp.leadership = v

    @property
    def morale_current(self): return self.morale_comp.current_morale if self.morale_comp else 100
    @morale_current.setter
    def morale_current(self, v): 
        if self.morale_comp: self.morale_comp.current_morale = v
        
    @property
    def max_morale(self): return self.morale_comp.max_morale if self.morale_comp else 100
    
    @property
    def movement_points(self): return self.movement_comp.current_movement_points if self.movement_comp else 0
    @movement_points.setter
    def movement_points(self, v):
        if self.movement_comp: self.movement_comp.current_movement_points = v

    @property
    def base_movement_points(self): return self.movement_comp.base_movement_points if self.movement_comp else 0
    @base_movement_points.setter
    def base_movement_points(self, v):
        if self.movement_comp: self.movement_comp.base_movement_points = v
    
    @property
    def morale_max(self): return self.max_morale
    @morale_max.setter
    def morale_max(self, v):
        if self.morale_comp: self.morale_comp.max_morale = v

    def init_combat_state(self):
        """Initializes transient combat attributes."""
        self.is_pinned = False
        self.morale_state = "Steady"
        self._shooting_cooldown = 0.0
        self.time_since_last_damage = 0.0
        self.recent_damage_taken = 0.0
        self.is_routing = False
        self.is_suppressed = False
        self.grid_x = getattr(self, 'grid_x', 0)
        self.grid_y = getattr(self, 'grid_y', 0)
        self.grid_z = getattr(self, 'grid_z', 0)
        self.fatigue = 0.0

    def invalidate_strength_cache(self):
        """Deprecated: Use invalidate_cache instead."""
        self.invalidate_cache()

    def set_fleet(self, fleet):
        self._fleet_ref = weakref.ref(fleet) if fleet else None
        
    @property
    def fleet(self):
        return self._fleet_ref() if hasattr(self, '_fleet_ref') and self._fleet_ref else None

    def __getstate__(self):
        """Custom pickling to handle weakrefs."""
        state = self.__dict__.copy()
        # weakref objects are not picklable
        if '_fleet_ref' in state:
            del state['_fleet_ref']
        return state

    def __setstate__(self, state):
        """Restore state and re-init weakrefs as None."""
        self.__dict__.update(state)
        # Verify _fleet_ref exists (it was deleted in getstate)
        if not hasattr(self, '_fleet_ref'):
            self._fleet_ref = None

    def apply_traits(self, trait_mods: Dict[str, Dict[str, Any]]):
        """Applies trait modifications to unit stats."""
        if not self.stats_comp:
            return
            
        for trait in self.traits:
            if trait in trait_mods:
                mods = trait_mods[trait]
                for stat, value in mods.items():
                    if hasattr(self.stats_comp, stat):
                        # Simple additive approach for now
                        current = getattr(self.stats_comp, stat)
                        setattr(self.stats_comp, stat, current + value)
        
    def recalc_stats(self):
        """Recalculates derived stats from components and traits."""
        if self.crew_comp:
            crew_bonus = 0
            troop_bonus = 0
            for comp in self.weapon_comps:
                if hasattr(comp, 'weapon_stats'):
                    crew_bonus += comp.weapon_stats.get("added_crew", 0)
                    troop_bonus += comp.weapon_stats.get("troop_defense_bonus", 0)
            
            self.crew_comp.max_crew_bonus = int(crew_bonus)
            # Update troop value if needed (base + bonus)
            # Assuming troop_value is also dynamic or we just adjust it here
            from src.core.balance import HULL_BASE_STATS
            base_troop = HULL_BASE_STATS.get(self.unit_class, {}).get("troop_value", 10)
            self.crew_comp.troop_value = base_troop + int(troop_bonus)
        
        if self.stats_comp:
            # apply_traits already handles base stat shifts
            pass

    def gain_xp(self, amount: float, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Adds experience to the unit and triggers level up if threshold is reached."""
        from src.core.balance import UNIT_MAX_LEVEL
        self.experience += amount * self.xp_gain_rate
        while self.level < UNIT_MAX_LEVEL:
            threshold = self.get_xp_threshold(self.level)
            if self.experience >= threshold:
                self.experience -= threshold
                self.level_up(context)
            else:
                break

    def get_xp_threshold(self, level: int) -> float:
        """Calculates XP needed to reach the NEXT level."""
        from src.core.balance import UNIT_XP_PER_LEVEL_BASE, UNIT_XP_GROWTH_EXPONENT
        # Exponential growth: 100, 120, 144, 172...
        return UNIT_XP_PER_LEVEL_BASE * (UNIT_XP_GROWTH_EXPONENT ** (level - 1))

    def level_up(self, context: Optional[Dict[str, Any]] = None):
        """Increments level and discovers a new ability."""
        # Recursion Guard
        if getattr(self, "_level_up_lock", False):
            return
            
        self._level_up_lock = True
        try:
            self.level += 1
            
            # Trigger ability discovery if context provides an AbilityManager
            if context and "ability_manager" in context:
                am = context["ability_manager"]
                new_ability_id = am.get_random_applicable_ability(self)
                if new_ability_id:
                    
                    # If this is an upgrade, remove the old version
                    if "_v" in new_ability_id:
                        base = new_ability_id.rsplit("_v", 1)[0]
                        to_remove = [k for k in self.abilities.keys() if k.startswith(base) and k != new_ability_id]
                        for k in to_remove:
                            del self.abilities[k]

                    # Add to unit abilities
                    self.abilities[new_ability_id] = am.registry[new_ability_id]
                    print(f"DEBUG: Unit {self.name} learned {new_ability_id}")
                    
                    # Log event if possible
                    if "battle_state" in context and context["battle_state"].tracker:
                        context["battle_state"].tracker.log_event(
                            "ability_discovered", 
                            self, 
                            None, 
                            description=f"Unit leveled up to {self.level} and learned {new_ability_id}!"
                        )
                else:
                    print(f"DEBUG: Unit {self.name} failed to find ability. Registry size in context: {len(am.registry)}")
            else:
                print("DEBUG: Level up called without ability_manager in context")
        finally:
             self._level_up_lock = False

    # [FEATURE] Fatigue Scaling
    @property
    def ma(self):
        base = self.stats_comp.ma if self.stats_comp else 50
        return int(base * self._get_fatigue_multiplier())

    @property
    def md(self):
        base = self.stats_comp.md if self.stats_comp else 50
        return int(base * self._get_fatigue_multiplier())

    def _get_fatigue_multiplier(self):
        f = getattr(self, 'fatigue', 0)
        if f > 80: return 0.5 # Exhausted
        if f > 50: return 0.8 # Fatigued
        return 1.0

    # [FEATURE] Squadron Logic
    @property
    def member_count(self) -> int:
        """Returns the number of active members in the squadron based on HP."""
        max_m = getattr(self, 'max_members', 1)
        if max_m <= 1: return 1
        
        # Avoid zero division
        if self.max_hp <= 0: return 0
        
        hp_per_member = self.max_hp / max_m
        return math.ceil(self.current_hp / hp_per_member) if hp_per_member > 0 else 0

    # Add other proxies as needed (ma, md, etc.) to prevent crashes
    def __getattr__(self, name):
        # Fallback for dynamic stats
        if name in ["ma", "md", "damage", "base_ma", "base_md", "base_damage", "agility", "base_agility", "leadership", "base_leadership"]:
             if self.stats_comp and hasattr(self.stats_comp, name):
                 return getattr(self.stats_comp, name)
             # Return defaults to prevent crashes
             if name in ["ma", "md"]: return 50
             if name == "damage": return 10
             if name in ["agility", "leadership"]: return 10
             if name in ["movement_points", "base_movement_points"]: return 0
             return 0
        
        # Transient combat flags (Fallback if init_combat_state called late)
        combat_flags = ["is_pinned", "morale_state", "tactical_directive", "_shooting_cooldown", 
                       "time_since_last_damage", "is_routing", "recent_damage_taken", "is_suppressed",
                       "grid_x", "grid_y", "grid_z", "fatigue", "home_defense_morale_bonus", "home_defense_toughness_bonus",
                       "toughness"]
        if name in combat_flags:
             if name in ["time_since_last_damage", "_shooting_cooldown", "recent_damage_taken", "fatigue"]:
                 return 0.0
             if name in ["grid_x", "grid_y", "grid_z", "home_defense_morale_bonus", "home_defense_toughness_bonus", "toughness"]:
                 return 0
             if name == "is_suppressed": return False
             return None
             
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class Ship(Unit):
    def __init__(self, name, faction, **kwargs):
        kwargs.pop("domain", None)
        u_class = kwargs.pop("unit_class", "ship")
        super().__init__(name, faction, unit_class=u_class, domain="space", **kwargs)
    
    def is_ship(self):
        return True

class Regiment(Unit):
    def __init__(self, name, faction, **kwargs):
        kwargs.pop("domain", None)
        u_class = kwargs.pop("unit_class", "regiment")
        super().__init__(name, faction, unit_class=u_class, domain="ground", **kwargs)

    # is_ship() inherited as False from Unit

# --- Legacy Component Class (For compatibility with combat_utils and RealTimeManager) ---
class Component:
    def __init__(self, name, hp, ctype, effect=None, weapon_stats=None):
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.type = ctype
        self.effect = effect
        self.weapon_stats = weapon_stats
        self.is_destroyed = False
        
    def to_dict(self):
        return {
            "name": self.name,
            "hp_current": self.current_hp,
            "hp_max": self.max_hp,
            "type": self.type,
            "is_destroyed": self.is_destroyed,
            "weapon_stats": self.weapon_stats if self.type == "Weapon" else None
        }
