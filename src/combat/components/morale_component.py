from typing import Any

class MoraleComponent:
    """Manages unit morale, leadership, and suppression."""
    
    def __init__(self, base_leadership: int = 7, max_morale: int = 100):
        self.leadership = base_leadership
        self.max_morale = max_morale
        self.current_morale = max_morale
        self.suppression = 0
        self.type = "Morale"
        self.is_destroyed = False
        
    def take_damage(self, amount: float):
        """Impacts morale based on damage taken."""
        self.apply_suppression(int(amount))

    def apply_suppression(self, amount: int):
        self.suppression += amount
        if self.suppression > self.current_morale:
            self.is_broken = True
            
    def recover(self, amount: int):
        self.suppression = max(0, self.suppression - amount)
        if self.suppression < (self.current_morale / 2):
            self.is_broken = False
            
    def check_panic(self, roll: int) -> bool:
        """True if unit panics."""
        return roll > self.leadership

    def to_dict(self) -> dict:
        return {
            "leadership": self.leadership,
            "max_morale": self.max_morale,
            "current_morale": self.current_morale,
            "suppression": self.suppression,
            "is_broken": self.is_broken
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MoraleComponent':
        comp = cls(data["leadership"], data["max_morale"])
        comp.current_morale = data["current_morale"]
        comp.suppression = data["suppression"]
        comp.is_broken = data["is_broken"]
        return comp
