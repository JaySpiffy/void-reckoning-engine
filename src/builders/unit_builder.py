from typing import List, Dict, Any, Optional
from src.models.unit import Unit # This might need to be adjusted later if Unit is moved
from src.combat.components.health_component import HealthComponent
from src.combat.components.armor_component import ArmorComponent
from src.combat.components.weapon_component import WeaponComponent
from src.combat.components.morale_component import MoraleComponent
from src.combat.components.trait_component import TraitComponent
from src.combat.components.movement_component import MovementComponent
from src.combat.components.stats_component import StatsComponent

class UnitBuilder:
    """Fluent builder for creating component-based units."""
    
    def __init__(self, name: str, faction: str):
        self.name = name
        self.faction = faction
        self.health = None
        self.armor = None
        self.morale = None
        self.trait = None
        self.weapons = []
        self.movement = None
        self.stats_comp = None
        self.stats = {} # Legacy stats dict
        self.extra_data = {}
        
    def with_health(self, max_hp: int, regen: float = 0.0, max_shield: int = 0) -> 'UnitBuilder':
        self.health = HealthComponent(max_hp, regen=regen, max_shield=max_shield)
        return self
        
    def with_armor(self, base_armor: int, facing_mods: Optional[Dict[str, int]] = None) -> 'UnitBuilder':
        self.armor = ArmorComponent(base_armor, facing_mods)
        return self
        
    def with_morale(self, leadership: int, max_morale: int = 100) -> 'UnitBuilder':
        self.morale = MoraleComponent(leadership, max_morale)
        return self
        
    def with_traits(self, traits: List[str], abilities: Dict[str, Any]) -> 'UnitBuilder':
        self.trait = TraitComponent(traits, abilities)
        return self
        
    def with_weapon(self, name: str, stats: Dict[str, Any], tags: Optional[List[str]] = None, arc: str = "Front") -> 'UnitBuilder':
        self.weapons.append(WeaponComponent(name, stats, tags, arc))
        return self
        
    def with_base_stats(self, stats: Dict[str, int]) -> 'UnitBuilder':
        self.stats.update(stats)
        return self
        
    def with_extra_data(self, key: str, value: Any) -> 'UnitBuilder':
        self.extra_data[key] = value
        return self
        
    def with_movement(self, movement_points: int, agility: int = 10, detection: float = 24.0,
                      turn_rate: float = 0.0, acceleration: float = 0.0) -> 'UnitBuilder':
        self.movement = MovementComponent(movement_points, agility, detection, turn_rate, acceleration)
        return self
        
    def with_stats_comp(self, ma=50, md=50, damage=10, armor=0, hp=100) -> 'UnitBuilder':
        self.stats_comp = StatsComponent(ma=ma, md=md, damage=damage, armor=armor, hp=hp)
        return self
        
    def build(self) -> Unit:
        from src.models.unit import Ship, Regiment
        
        # Determine unit class
        unit_type = self.extra_data.get("unit_type", "Unit")
        if unit_type == "Ship":
            unit = Ship(name=self.name, faction=self.faction)
        elif unit_type == "Regiment":
            unit = Regiment(name=self.name, faction=self.faction)
        elif unit_type == "Starbase":
            from src.models.starbase import Starbase
            unit = Starbase(name=self.name, faction=self.faction, system=None)
        else:
            unit = Unit(
                name=self.name, 
                faction=self.faction, 
                unit_class=self.extra_data.get("unit_class"),
                domain=self.extra_data.get("domain")
            )
            
        unit.health_comp = self.health
        unit.armor_comp = self.armor
        unit.morale_comp = self.morale
        unit.trait_comp = self.trait
        unit.weapon_comps = self.weapons
        unit.movement_comp = self.movement
        unit.stats_comp = self.stats_comp
        
        # Legacy compatibility (Syncing stats to old fields for now)
        if self.health:
            unit.base_hp = self.health.max_hp
            unit.current_hp = self.health.current_hp
            if hasattr(unit, "shield_max"):
                 unit.shield_max = self.health.max_shield
                 unit.shield_current = self.health.current_shield
        if self.armor:
            unit.base_armor = self.armor.base_armor
        if self.trait:
            unit.traits = self.trait.traits
            unit.abilities = self.trait.abilities
            
        # Update with base stats
        for k, v in self.stats.items():
            setattr(unit, f"base_{k}" if hasattr(unit, f"base_{k}") else k, v)
            
        # Add extra metadata
        for k, v in self.extra_data.items():
            if k != "unit_type":
                setattr(unit, k, v)
            
        return unit

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Unit:
        """Hydrates a Unit from a dictionary (Save V2)."""
        builder = cls(data["name"], data.get("faction", "Unknown"))
        
        if "health_comp" in data:
            builder.health = HealthComponent.from_dict(data["health_comp"])
        if "armor_comp" in data:
            builder.armor = ArmorComponent.from_dict(data["armor_comp"])
        if "morale_comp" in data:
            builder.morale = MoraleComponent.from_dict(data["morale_comp"])
        if "trait_comp" in data:
            builder.trait = TraitComponent.from_dict(data["trait_comp"])
        if "weapon_comps" in data:
            builder.weapons = [WeaponComponent.from_dict(w) for w in data["weapon_comps"]]
            
        if "movement_comp" in data:
            builder.movement = MovementComponent.from_dict(data["movement_comp"])
            
        if "stats_comp" in data:
            builder.stats_comp = StatsComponent.from_dict(data["stats_comp"])
            
        builder.stats = data.get("stats", {})
        builder.extra_data = data.get("extra_data", {})
        
        return builder.build()
