from typing import List, Dict, Optional

class SpyNetwork:
    """
    Represents an intelligence network established within a target faction.
    """
    def __init__(self, target_faction_name: str):
        self.target_faction = target_faction_name
        self.infiltration_level = 0.0  # 0 to 100
        self.is_exposed = False
        self.agents: List[str] = []  # List of agent roles (e.g., "Mole", "Saboteur")
        self.points_invested = 0
        self.established_turn = 0

    def grow(self, amount: float):
        """Increases infiltration level, capped at 100."""
        if self.is_exposed: return
        self.infiltration_level = min(100.0, self.infiltration_level + amount)

    def degrade(self, amount: float):
        """Decreases infiltration level."""
        self.infiltration_level = max(0.0, self.infiltration_level - amount)

    def expose(self):
        """Triggers exposure, halting growth and risking diplomatic penalties."""
        self.is_exposed = True
        self.infiltration_level *= 0.5  # Lose half progress immediately

    def to_dict(self) -> Dict:
        return {
            "target_faction": self.target_faction,
            "infiltration_level": self.infiltration_level,
            "is_exposed": self.is_exposed,
            "agents": self.agents,
            "points_invested": self.points_invested,
            "established_turn": self.established_turn
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SpyNetwork':
        net = cls(data["target_faction"])
        net.infiltration_level = data.get("infiltration_level", 0.0)
        net.is_exposed = data.get("is_exposed", False)
        net.agents = data.get("agents", [])
        net.points_invested = data.get("points_invested", 0)
        net.established_turn = data.get("established_turn", 0)
        return net
