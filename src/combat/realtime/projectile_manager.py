from typing import List, Any, Dict, Optional, Tuple
from src.models.projectile import Projectile

class ProjectileManager:
    """
    Manages the lifecycle, physics, and collision detection of all projectiles.
    Handles the 'Empire at War' style real-time exchange.
    """
    def __init__(self, grid: Any):
        self.grid = grid
        self.projectiles: List[Projectile] = []

    def spawn_projectile(self, owner: Any, target: Any, damage: float, ap: float, speed: float, projectile_type: str = "KINETIC", **kwargs):
        """Spawns a new projectile at the owner's position."""
        pos = (owner.grid_x, owner.grid_y)
        proj = Projectile(owner, target, damage, ap, speed, pos, projectile_type=projectile_type, **kwargs)
        self.projectiles.append(proj)

    def update(self, dt: float, battle_state: Any):
        """Updates all projectiles and checks for collisions."""
        surviving_projectiles = []
        
        # Performance optimization: if no projectiles, skip
        if not self.projectiles:
            return

        for proj in self.projectiles:
            # Save old position for "sweep" collision if needed
            old_x, old_y = proj.x, proj.y
            
            proj.update(dt)
            
            if proj.is_destroyed:
                continue
                
            # Collision Detection
            # [Optimization] Direct target check is O(1) per projectile. 
            # Neighborhood check is O(proj * neighbors) but managed by SpatialIndex.
            hit_unit = self._check_collision(proj, battle_state, old_pos=(old_x, old_y))
            
            if hit_unit:
                self._apply_hit(proj, hit_unit, battle_state)
                proj.is_destroyed = True
            else:
                surviving_projectiles.append(proj)
                
        self.projectiles = surviving_projectiles

    def _check_collision(self, proj: Projectile, battle_state: Any, old_pos: Optional[Tuple[float, float]] = None) -> Optional[Any]:
        """Checks if the projectile has collided with its target or another unit."""
        # 1. Target Check (Priority)
        if proj.target_unit and proj.target_unit.is_alive():
            tx, ty = proj.target_unit.grid_x, proj.target_unit.grid_y
            
            # Simple distance check
            dist = self._get_dist(proj.x, proj.y, tx, ty)
            if dist < 2.0: # Collision threshold
                return proj.target_unit
            
            # [FIX] Swept Collision: Check if we passed through the target
            if old_pos:
                ox, oy = old_pos
                
                # Segment AB: (ox, oy) -> (proj.x, proj.y)
                # Point P: (tx, ty)
                
                # Vector AB
                ab_x = proj.x - ox
                ab_y = proj.y - oy
                
                # Vector AP
                ap_x = tx - ox
                ap_y = ty - oy
                
                # Length squared of AB
                ab_len_sq = ab_x**2 + ab_y**2
                
                if ab_len_sq > 0:
                    # Project AP onto AB to find t
                    t = (ap_x * ab_x + ap_y * ab_y) / ab_len_sq
                    
                    # Clamp t to segment [0, 1]
                    t = max(0.0, min(1.0, t))
                    
                    # Closest point on segment
                    closest_x = ox + t * ab_x
                    closest_y = oy + t * ab_y
                    
                    # Distance from closest point to target
                    dist_sq = (tx - closest_x)**2 + (ty - closest_y)**2
                    
                    if dist_sq < 4.0: # 2.0^2
                        return proj.target_unit
        
        # 2. Grid-based "Accidental" Hit (Check units at the projectile's location)
        # We only do this for non-homing kinetics to allow for scattering.
        if proj.projectile_type == "KINETIC" and self.grid:
            near_units = self.grid.query_units_in_range(proj.x, proj.y, radius=2.0) # Increased to match threshold
            for unit in near_units:
                if unit is not proj.owner and unit.is_alive() and unit.faction != proj.owner.faction:
                    return unit
                    
        return None

    def _get_dist(self, x1, y1, x2, y2) -> float:
        import math
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    def _apply_hit(self, proj: Projectile, unit: Any, battle_state: Any):
        """Applies damage to the unit that was hit."""
        # Mitigation logic is usually handled in unit.take_damage
        dmg_s, dmg_h, is_destroyed, _ = unit.take_damage(
            proj.damage, 
            target_component=proj.target_comp,
            shield_mult=getattr(proj, 'shield_mult', 1.0), 
            hull_mult=getattr(proj, 'hull_mult', 1.0)
        )
        
        # Statistics
        attacker_faction = getattr(proj.owner, 'faction', 'Unknown')
        if attacker_faction in battle_state.battle_stats:
            battle_state.battle_stats[attacker_faction]["total_damage_dealt"] += (dmg_s + dmg_h)
            
        if is_destroyed and battle_state.tracker:
            battle_state.track_unit_destruction(unit.faction, unit, attacker_faction)

        # Log Hit Event
        battle_state.log_event(
            "projectile_hit", 
            getattr(proj.owner, 'name', 'Unknown'), 
            unit.name, 
            f"Hit with {proj.projectile_type} for {int(dmg_s + dmg_h)} total dmg"
        )
