from typing import Dict, Any, Optional

class MovementComponent:
    """Manages unit movement points, agility, and detection."""
    
    def __init__(self, movement_points: int, agility: int = 10, detection_range: float = 24.0):
        self.base_movement_points = movement_points
        self.current_movement_points = movement_points
        self.agility = agility
        self.detection_range = detection_range
        self.movement_spent = 0.0
        self.type = "Movement"
        self.is_destroyed = False
        
    def reset_movement(self):
        """Resets current movement points for a new turn."""
        self.current_movement_points = self.base_movement_points
        self.movement_spent = 0.0
        
    def consume_movement(self, amount: float) -> bool:
        """Consumes movement points. Returns True if enough points were available."""
        if self.current_movement_points >= amount:
            self.current_movement_points -= amount
            self.movement_spent += amount
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_movement_points": self.base_movement_points,
            "current_movement_points": self.current_movement_points,
            "agility": self.agility,
            "detection_range": self.detection_range,
            "movement_spent": self.movement_spent
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MovementComponent':
        comp = cls(
            data["base_movement_points"], 
            data.get("agility", 10), 
            data.get("detection_range", 24.0)
        )
        comp.current_movement_points = data.get("current_movement_points", data["base_movement_points"])
        comp.movement_spent = data.get("movement_spent", 0.0)
        return comp
