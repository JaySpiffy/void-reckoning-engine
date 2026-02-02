from typing import List, Dict, Any, Optional, Tuple
import weakref
from src.combat.components.health_component import HealthComponent
from src.combat.components.armor_component import ArmorComponent
from src.combat.components.weapon_component import WeaponComponent
from src.combat.components.morale_component import MoraleComponent
from src.combat.components.trait_component import TraitComponent
from src.combat.components.movement_component import MovementComponent
from src.combat.components.stats_component import StatsComponent

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
        
        # Composition: Components are injected
        self.health_comp: Optional[HealthComponent] = None
        self._fleet_ref = None # Weakref to parent fleet
        self.armor_comp: Optional[ArmorComponent] = None
        self.weapon_comps: List[WeaponComponent] = []
        self.morale_comp: Optional[MoraleComponent] = None
        self.trait_comp: Optional[TraitComponent] = None
        self.movement_comp: Optional[MovementComponent] = None
        self.stats_comp: Optional[StatsComponent] = None
        
        self.components = [] 
        
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
            
        self.components.append(component)

    def take_damage(self, amount: float, impact_angle: float = 0, target_component=None, ignore_mitigation=False):
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
            
        # 2. Targeted Component Damage (EaW Style)
        destroyed_component = None
        if target_component and hasattr(target_component, 'take_damage'):
             # Redirect a portion of damage to the component? Or all?
             # For now, all damage goes to component AND hull (structural integrity).
             # Standard EaW: Component has its own HP. Hull has its own.
             c_destroyed = target_component.take_damage(mitigated_amount)
             if c_destroyed:
                  destroyed_component = target_component
        
        # 3. Apply hull/shield damage
        s_dmg, h_dmg, is_destroyed = 0.0, 0.0, False
        if self.health_comp:
            s_dmg, h_dmg, is_destroyed = self.health_comp.take_damage(mitigated_amount)
            
            # Update morale
            if self.morale_comp:
                self.morale_comp.take_damage(h_dmg)
                
        if h_dmg > 0 or s_dmg > 0:
            self.invalidate_cache()
                
        return s_dmg, h_dmg, is_destroyed, destroyed_component

    def to_dict(self) -> Dict[str, Any]:
        """Serializes unit state (Save V2 compatible)."""
        data = {
            "name": self.name,
            "faction": self.faction,
            "unit_type": self.__class__.__name__,
            "extra_data": {
                "unit_class": self.unit_class,
                "domain": self.domain,
                "blueprint_id": self.blueprint_id
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
        return self.health_comp.is_alive() if self.health_comp else False

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
    def abilities(self): return self.trait_comp.abilities if self.trait_comp else {}
    @abilities.setter
    def abilities(self, v):
        if self.trait_comp: self.trait_comp.abilities = v
        
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

    def invalidate_strength_cache(self):
        """Deprecated: Use invalidate_cache instead."""
        self.invalidate_cache()

    def set_fleet(self, fleet):
        self._fleet_ref = weakref.ref(fleet) if fleet else None
        
    @property
    def fleet(self):
        return self._fleet_ref() if hasattr(self, '_fleet_ref') and self._fleet_ref else None

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
        """Recalculates derived stats."""
        if self.stats_comp:
            # For now, just reset to base + trait mods logic if needed, 
            # but apply_traits already modified stats_comp.
            pass

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
                       "grid_x", "grid_y", "home_defense_morale_bonus", "home_defense_toughness_bonus",
                       "toughness"]
        if name in combat_flags:
             if name in ["time_since_last_damage", "_shooting_cooldown", "recent_damage_taken"]:
                 return 0.0
             if name in ["grid_x", "grid_y", "home_defense_morale_bonus", "home_defense_toughness_bonus", "toughness"]:
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
