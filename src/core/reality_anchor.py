from typing import Tuple, Optional, Dict
from src.core.universe_physics import PhysicsProfile

class RealityAnchor:
    """
    Represents an object or zone that enforces a specific set of physical laws.
    Used to simulate "Null Zones", "Flux Rifts", or "Gellar Fields".
    """
    def __init__(self, name: str, profile: PhysicsProfile, radius: int, x: int = 0, y: int = 0):
        self.name = name
        self.profile = profile
        self.radius = radius
        self.position = (x, y)
        self.is_active = True

    def set_position(self, x: int, y: int):
        self.position = (x, y)

    def is_in_range(self, x: int, y: int) -> bool:
        """Checks if coordinates are within the anchor's radius."""
        if not self.is_active: return False
        dx = abs(x - self.position[0])
        dy = abs(y - self.position[1])
        dist_sq = dx*dx + dy*dy
        return dist_sq <= (self.radius * self.radius)

    def apply_anchor_effect(self, base_profile: PhysicsProfile) -> PhysicsProfile:
        """
        Merges the Anchor's profile with the Base Profile.
        Strategy: Multiplicative blending of matching multipliers.
        """
        blended_multipliers = base_profile.multipliers.copy()
        for key, factor in self.profile.multipliers.items():
            if key in blended_multipliers:
                blended_multipliers[key] *= factor
            else:
                blended_multipliers[key] = factor
            
        return PhysicsProfile(
            description=f"{base_profile.description} [MODIFIED by {self.name}]",
            multipliers=blended_multipliers
        )
