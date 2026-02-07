import math
from typing import Any, Optional, Tuple

class Projectile:
    """
    Representation of a flying projectile in real-time combat (Phase 4).
    Supports Empire at War style physical projectiles with speed and tracking.
    """
    def __init__(
        self,
        owner: Any,
        target_unit: Any,
        damage: float,
        ap: float,
        speed: float,
        pos: Tuple[float, float],
        target_comp: Optional[Any] = None,
        projectile_type: str = "KINETIC",
        **kwargs
    ):
        self.owner = owner
        self.target_unit = target_unit
        self.target_comp = target_comp
        self.damage = damage
        self.ap = ap
        self.speed = speed
        self.projectile_type = projectile_type  # KINETIC, LASER, MISSILE
        self.is_destroyed = False
        
        self.x, self.y = pos
        
        # Accuracy-based deviation (optional, can be passed in kwargs)
        self.deviation = kwargs.get("deviation", 0.0)
        
        self.vx, self.vy = self._calculate_velocity()
            
        self.max_lifetime = kwargs.get("lifetime", 5.0) # Lower default lifetime for performance
        self.lifetime = 0.0

    def _calculate_velocity(self) -> Tuple[float, float]:
        """Calculates initial velocity vector directed at the target."""
        if not self.target_unit:
            return 0.0, 0.0
            
        tx, ty = self.target_unit.grid_x, self.target_unit.grid_y
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            vx = (dx / dist) * self.speed
            vy = (dy / dist) * self.speed
            
            # Apply deviation if any
            if self.deviation != 0:
                angle = math.atan2(vy, vx) + self.deviation
                vx = math.cos(angle) * self.speed
                vy = math.sin(angle) * self.speed
                
            return vx, vy
        return 0.0, 0.0

    def update(self, dt: float):
        """Updates position and tracking for guided munitions."""
        if self.projectile_type == "MISSILE" and self.target_unit and self.target_unit.is_alive():
            # Guided Tracking: Re-calculate velocity to steer toward target
            # [EaW Logic] Missiles have turn rates, but for now we'll do simple tracking
            new_vx, new_vy = self._calculate_velocity()
            # Smooth steering
            self.vx = self.vx * 0.8 + new_vx * 0.2
            self.vy = self.vy * 0.8 + new_vy * 0.2
            
            # Normalize to maintain speed
            mag = math.sqrt(self.vx**2 + self.vy**2)
            if mag > 0:
                self.vx = (self.vx / mag) * self.speed
                self.vy = (self.vy / mag) * self.speed

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime += dt
        
        if self.lifetime >= self.max_lifetime:
            self.is_destroyed = True

    def to_dict(self):
        return {
            "type": self.projectile_type,
            "x": self.x,
            "y": self.y,
            "owner": getattr(self.owner, 'name', "Unknown"),
            "target": getattr(self.target_unit, 'name', "None")
        }
