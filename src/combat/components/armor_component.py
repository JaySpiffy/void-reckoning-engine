from typing import Dict, Optional, Any

class ArmorComponent:
    """Manages unit armor and facing-specific protection."""
    
    def __init__(self, base_armor: int, facing_mods: Optional[Dict[str, int]] = None):
        self.base_armor = base_armor
        self.facing_mods = facing_mods or {
            "Front": 0,
            "Side": -10,
            "Rear": -20,
            "Dorsal": 0,
            "Ventral": -5
        }
        self.type = "Armor"
        self.is_destroyed = False
        
    def get_armor_for_facing(self, facing: str) -> int:
        """Returns the modified armor value for a specific hit facing."""
        mod = self.facing_mods.get(facing, 0)
        return max(0, self.base_armor + mod)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_armor": self.base_armor,
            "facing_mods": self.facing_mods
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArmorComponent':
        return cls(data["base_armor"], data.get("facing_mods"))
