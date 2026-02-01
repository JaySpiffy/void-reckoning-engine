from typing import Dict, Any, Tuple, List

class PhysicsProfile:
    """
    Stores high-level multipliers for a specific universe.
    Enables "reality manipulation" by scaling fundamental properties.
    Note: Atom-level DNA scaling has been decommissioned.
    """
    def __init__(self, multipliers: Dict[str, float] = None, description: str = ""):
        self.description = description
        # Default multipliers (e.g., "damage", "speed", "hp")
        self.multipliers = multipliers or {}
            
    def apply_to_stats(self, stats: Dict[str, float]) -> Dict[str, float]:
        """Multiplies stats by corresponding multipliers."""
        result = stats.copy()
        for key, mult in self.multipliers.items():
            if key in result:
                result[key] *= mult
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhysicsProfile':
        """Creates a PhysicsProfile from a dictionary."""
        description = data.get("description", "")
        multipliers = {k: v for k, v in data.items() if k != "description"}
        return cls(multipliers, description)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the profile to a dictionary."""
        result = {"description": self.description}
        result.update(self.multipliers)
        return result

    def validate(self) -> Tuple[bool, List[str]]:
        """Validates that multipliers are valid numbers."""
        errors = []
        for key, mult in self.multipliers.items():
            if not isinstance(mult, (int, float)):
                errors.append(f"Multiplier for {key} must be numeric, got {type(mult)}")
        return len(errors) == 0, errors
