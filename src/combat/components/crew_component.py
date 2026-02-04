from typing import Dict, Any, Optional

class CrewComponent:
    """Manages unit crew, troop defense, and the drifting hulk state."""
    
    def __init__(self, max_crew: int, current_crew: Optional[int] = None, troop_value: int = 10):
        self.max_crew_base = max_crew
        self.max_crew_bonus = 0
        self.current_crew = current_crew if current_crew is not None else max_crew
        self.troop_value = troop_value
        self.type = "Crew"
        self._is_hulk = False
        
    @property
    def max_crew(self) -> int:
        return self.max_crew_base + self.max_crew_bonus

    @property
    def is_hulk(self) -> bool:
        return self.current_crew <= 0 or self._is_hulk
        
    @is_hulk.setter
    def is_hulk(self, value: bool):
        self._is_hulk = value

    def take_crew_damage(self, amount: int, bonus_attack_value: int = 0, effective_defense: Optional[int] = None, bonus_defense_value: int = 0) -> int:
        """
        Applies damage to crew based on attack value vs troop defense.
        Returns amount of crew killed.
        """
        if self.is_hulk:
            return 0
            
        defense = effective_defense if effective_defense is not None else self.troop_value
        # Add bonus defense from transported troops or other sources
        defense += bonus_defense_value
        
        # Effective attrition: 
        # (Attack + bonus/5) / (Defense / 5) -> Simple model.
        # If defense is 10, divisor is 2. If 20 (Battleship), divisor is 4.
        # This makes heavier ships harder to clear out.
        divisor = max(1, defense // 5)
        killed = min(self.current_crew, (amount + (bonus_attack_value // 5)) // divisor)
        
        # Ensure at least 1 dies if amount > 0 and not intercepted
        if amount > 0 and killed == 0:
            killed = 1
            
        self.current_crew -= killed
        return killed
        
    def capture_ship(self, initial_crew: int):
        """Resets the hulk state and sets initial crew after capture."""
        self.current_crew = min(self.max_crew, initial_crew)
        self._is_hulk = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_crew": self.max_crew,
            "current_crew": self.current_crew,
            "troop_value": self.troop_value,
            "is_hulk": self.is_hulk
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrewComponent':
        comp = cls(data["max_crew"], data["current_crew"], data.get("troop_value", 10))
        comp._is_hulk = data.get("is_hulk", False)
        return comp
