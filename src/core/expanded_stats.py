
from typing import Dict, List, Any, Optional

class DamageType:
    """
    Represents a specific type of damage distribution.
    e.g. 80% Energy, 20% Acidic
    """
    def __init__(self, type_name: str, percentage: float):
        self.type = type_name.lower()  # physical, energy, acidic, etc.
        self.percentage = percentage  # 0.0 to 1.0 (or 0-100 normalized)

    def to_dict(self):
        return {"type": self.type, "percentage": self.percentage}

class Ability:
    """
    Represents a discrete active or passive power.
    e.g. "Acidic Blood" (Passive) -> detailed effect logic handled by EffectSystem later.
    """
    def __init__(self, id: str, name: str, ability_type: str, effect_key: str, value: float = 0):
        self.id = id
        self.name = name
        self.type = ability_type  # passive, active, reaction
        self.effect_key = effect_key # Hook for EffectSystem
        self.value = value

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "effect_key": self.effect_key,
            "value": self.value
        }

class ExpandedStats:
    """
    The new 'D&D Sheet' for Units and Weapons.
    Replaces the flat dictionary of 50 atomic stats.
    """
    def __init__(self, 
                 hp: int = 0, 
                 armor: int = 0, 
                 shield: int = 0,
                 damage: int = 0, 
                 speed: int = 0,
                 accuracy: int = 0):
        
        # Primary Stats
        self.hp = hp
        self.armor = armor
        self.shield = shield
        self.damage = damage
        self.speed = speed
        self.accuracy = accuracy # 0-100 typically
        
        # Resistances (Percent reduction, e.g. 20 = 20% reduced dmg)
        self.resistances: Dict[str, float] = {
            "physical": 0.0,
            "energy": 0.0,
            "acidic": 0.0,
            "corrosive": 0.0,
            "thermal": 0.0,
            "radiation": 0.0,
            "resonant": 0.0
        }
        
        # Damage Output Profile
        self.damage_types: List[DamageType] = []
        
        # Special Abilities
        self.abilities: List[Ability] = []
        self.active_effects: List[Dict] = [] # Runtime status effects

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hp": self.hp,
            "armor": self.armor,
            "shield": self.shield,
            "damage": self.damage,
            "speed": self.speed,
            "accuracy": self.accuracy,
            "resistances": self.resistances,
            "damage_types": [d.to_dict() for d in self.damage_types],
            "abilities": [a.to_dict() for a in self.abilities]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpandedStats':
        stats = cls(
            hp=data.get("hp", 0),
            armor=data.get("armor", 0),
            shield=data.get("shield", 0),
            damage=data.get("damage", 0),
            speed=data.get("speed", 0),
            accuracy=data.get("accuracy", 0)
        )
        stats.resistances = data.get("resistances", stats.resistances)
        
        # Parse nested
        dt = data.get("damage_types", [])
        stats.damage_types = [DamageType(d["type"], d["percentage"]) for d in dt]
        
        ab = data.get("abilities", [])
        stats.abilities = [Ability(a["id"], a["name"], a["type"], a["effect_key"], a.get("value", 0)) for a in ab]
        
        return stats
