from typing import Dict, Any, Optional

class MovementComponent:
    """Manages unit movement points, agility, and detection."""
    
    def __init__(self, movement_points: int, agility: int = 10, detection_range: float = 24.0, 
                 turn_rate: float = 0.0, acceleration: float = 0.0):
        self.base_movement_points = movement_points # Treats as Max Speed
        self.current_movement_points = movement_points
        self.agility = agility
        self.detection_range = detection_range
        self.movement_spent = 0.0
        self.type = "Movement"
        self.is_destroyed = False
        
        # Physics Attributes (Empire at War Style)
        # turn_rate: degrees per tick
        # acceleration: units per tick^2
        self.turn_rate = turn_rate 
        self.acceleration = acceleration
        self.current_speed = 0.0
        self.velocity = (0.0, 0.0)
        self.facing = 0.0 # 0 = East, 90 = South, 180 = West, 270 = North (Standard Grid)
        self.target_facing = 0.0
        
    def reset_movement(self):
        """Resets current movement points for a new turn (Turn-Based Legacy Compatibility)."""
        self.current_movement_points = self.base_movement_points
        self.movement_spent = 0.0
        # Physics state persists across turns in a hybrid system, or resets if strictly turn-based.
        # For Real-Time, we don't reset velocity/speed here usually, 
        # but if this is called at start of battle, it's fine.
        
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
            "movement_spent": self.movement_spent,
            "turn_rate": self.turn_rate,
            "acceleration": self.acceleration,
            "current_speed": self.current_speed,
            "velocity": self.velocity,
            "facing": self.facing
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MovementComponent':
        comp = cls(
            data["base_movement_points"], 
            data.get("agility", 10), 
            data.get("detection_range", 24.0),
            data.get("turn_rate", 0.0),
            data.get("acceleration", 0.0)
        )
        comp.current_movement_points = data.get("current_movement_points", data["base_movement_points"])
        comp.movement_spent = data.get("movement_spent", 0.0)
        comp.current_speed = data.get("current_speed", 0.0)
        comp.velocity = tuple(data.get("velocity", [0.0, 0.0]))
        comp.facing = data.get("facing", 0.0)
        return comp
