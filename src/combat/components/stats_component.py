from typing import Dict, Any, Optional

class StatsComponent:
    """Manages raw and derived unit statistics."""
    
    def __init__(self, ma: int = 50, md: int = 50, damage: int = 10, armor: int = 0, leadership: int = 50, agility: int = 10, hp: int = 100):
        self.base_ma = ma
        self.base_md = md
        self.base_damage = damage
        self.base_armor = armor
        self.base_leadership = leadership
        self.base_agility = agility
        self.base_hp = hp
        
        # Current derived values
        self.ma = ma
        self.md = md
        self.damage = damage
        self.armor = armor
        self.leadership = leadership
        self.agility = agility
        self.type = "Stats"
        self.is_destroyed = False
        
    def reset_derived(self):
        """Resets derived stats to base values before recalculation."""
        self.ma = self.base_ma
        self.md = self.base_md
        self.damage = self.base_damage
        self.armor = self.base_armor
        self.leadership = self.base_leadership
        self.agility = self.base_agility

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base": {
                "ma": self.base_ma,
                "md": self.base_md,
                "damage": self.base_damage,
                "armor": self.base_armor,
                "leadership": self.base_leadership,
                "agility": self.base_agility,
                "hp": self.base_hp
            },
            "current": {
                "ma": self.ma,
                "md": self.md,
                "damage": self.damage,
                "armor": self.armor,
                "leadership": self.leadership,
                "agility": self.agility
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatsComponent':
        base = data.get("base", data) # Fallback for flat structure
        comp = cls(
            ma=base.get("ma", 50),
            md=base.get("md", 50),
            damage=base.get("damage", 10),
            armor=base.get("armor", 0),
            leadership=base.get("leadership", 50),
            agility=base.get("agility", 10),
            hp=base.get("hp", 100)
        )
        if "current" in data:
            for k, v in data["current"].items():
                setattr(comp, k, v)
        return comp
