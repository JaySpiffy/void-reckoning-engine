from typing import Dict, Any, List, Optional

class WeaponComponent:
    """Manages an individual weapon system on a unit."""
    
    def __init__(self, name: str, weapon_stats: Dict[str, Any], tags: Optional[List[str]] = None, arc: str = "Front"):
        self.name = name
        self.weapon_stats = weapon_stats # Raw stats (Range, S, AP, D, Type)
        self.tags = tags or []
        self.arc = arc
        self.cooldown = 0
        self.is_destroyed = False
        self.type = "Weapon"
        self.max_hp = 50 
        self.current_hp = 50
        
    def take_damage(self, amount: float) -> bool:
        """
        Applies damage to the weapon system.
        Returns True if the weapon is destroyed.
        """
        if self.is_destroyed: return False
        
        self.current_hp -= amount
        if self.current_hp <= 0:
            self.is_destroyed = True
            self.current_hp = 0
            return True
        return False
        
    @property
    def range(self) -> int:
        return self.weapon_stats.get("Range", 24)
        
    @property
    def strength(self) -> int:
        return self.weapon_stats.get("Str", self.weapon_stats.get("S", 4))
        
    @property
    def ap(self) -> int:
        return self.weapon_stats.get("AP", 0)
        
    @property
    def damage(self) -> int:
        return self.weapon_stats.get("D", 1)
        
    def update_cooldown(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "weapon_stats": self.weapon_stats,
            "tags": self.tags,
            "arc": self.arc,
            "cooldown": self.cooldown,
            "is_destroyed": self.is_destroyed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeaponComponent':
        comp = cls(data["name"], data["weapon_stats"], data.get("tags"), data.get("arc", "Front"))
        comp.cooldown = data.get("cooldown", 0)
        comp.is_destroyed = data.get("is_destroyed", False)
        return comp
