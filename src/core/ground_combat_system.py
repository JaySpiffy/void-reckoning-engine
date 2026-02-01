
from typing import Dict, List, Any

class GroundStats:
    def __init__(self, hp: int, armor: int, morale: int, 
                 melee_attack: int, melee_defense: int, 
                 ranged_attack: int, charge_bonus: int,
                 weapon_strength: int, armor_piercing: int,
                 speed: float, entity_count: int):
        self.hp = hp
        self.armor = armor
        self.morale = morale
        self.melee_attack = melee_attack
        self.melee_defense = melee_defense
        self.ranged_attack = ranged_attack
        self.charge_bonus = charge_bonus
        self.weapon_strength = weapon_strength
        self.armor_piercing = armor_piercing
        self.speed = speed
        self.entity_count = entity_count # 120 men, or 1 monster
        
    def to_dict(self):
        return self.__dict__

class GroundUnitClass:
    """
    Defines a class of unit (e.g. 'Line Infantry') and its base stats.
    """
    def __init__(self, id: str, name: str, stats: GroundStats, 
                 attributes: List[str] = None):
        self.id = id
        self.name = name
        self.stats = stats
        self.attributes = attributes or [] # e.g. "large", "psychology_immune"

class Regiment:
    """
    A specific instance of a ground unit in an army.
    """
    def __init__(self, name: str, unit_class: GroundUnitClass, xp_level: int = 0):
        self.name = name
        self.unit_class = unit_class
        self.current_hp = unit_class.stats.hp
        self.current_entities = unit_class.stats.entity_count
        self.current_morale = unit_class.stats.morale
        self.fatigue = 0.0 # 0.0 to 1.0
        self.xp_level = xp_level

    def get_effective_stats(self) -> Dict[str, float]:
        """Calculates stats active in battle (applying fatigue/morale penalties)."""
        stats = self.unit_class.stats.to_dict()
        
        # Fatigue Penalties
        if self.fatigue > 0.5:
            stats["speed"] *= 0.8
            stats["melee_attack"] *= 0.8
            stats["charge_bonus"] *= 0.5
            
        return stats
