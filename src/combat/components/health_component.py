from typing import Dict, Any, Tuple, Optional

class HealthComponent:
    """Manages unit health, shields, and regeneration."""
    
    def __init__(self, max_hp: int, current_hp: Optional[int] = None, regen: float = 0.0, max_shield: int = 0):
        self.max_hp = max_hp
        self.current_hp = current_hp if current_hp is not None else max_hp
        self.regen = regen
        self.max_shield = max_shield
        self.current_shield = max_shield
        self.type = "Health"
        
    @property
    def is_destroyed(self) -> bool:
        return self.current_hp <= 0
        
    def take_damage(self, amount: float) -> Tuple[float, float, bool]:
        """
        Applies damage to shields then HP.
        Returns (shield_damage, hp_damage, is_destroyed)
        """
        shield_dmg = 0
        hp_dmg = 0
        
        if self.current_shield > 0:
            shield_dmg = min(self.current_shield, amount)
            self.current_shield -= shield_dmg
            amount -= shield_dmg
            
        if amount > 0:
            hp_dmg = min(self.current_hp, amount)
            self.current_hp -= hp_dmg
            
        return shield_dmg, hp_dmg, self.current_hp <= 0

    def regenerate(self):
        """Applies regenerative effects."""
        self.current_hp = min(self.max_hp, self.current_hp + self.regen)
        
    def regenerate_shields(self, amount: float = 0):
        """Regenerates shields by amount or logic."""
        # Simple regen for now if amount not provided (though logic implies caller or component handles rate)
        if self.max_shield > 0 and self.current_shield < self.max_shield:
             # Default regen?
             pass 
        self.current_shield = min(self.max_shield, self.current_shield + amount)

    def is_alive(self) -> bool:
        return self.current_hp > 0
        
    @property
    def hp_percentage(self) -> float:
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "regen": self.regen,
            "max_shield": self.max_shield,
            "current_shield": self.current_shield
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthComponent':
        comp = cls(data["max_hp"], data["current_hp"], data["regen"], data["max_shield"])
        comp.current_shield = data["current_shield"]
        return comp
