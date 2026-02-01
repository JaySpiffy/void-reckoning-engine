import math
from typing import List, Any, Tuple, Optional

class SteeringManager:
    """
    Implements Boids (Separation, Alignment, Cohesion) and Steering Behaviors.
    """
    
    @staticmethod
    def calculate_formation_steering(unit: Any, target_slot_pos: Tuple[float, float]) -> Tuple[float, float]:
        """
        Force that pushes an entity toward its assigned slot in a formation.
        """
        tx, ty = target_slot_pos
        dx = tx - unit.grid_x
        dy = ty - unit.grid_y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 0.1: return 0.0, 0.0
        
        # High intensity Seek force for formation maintenance
        return (dx / dist) * 2.0, (dy / dist) * 2.0

    @staticmethod
    def calculate_flee_steering(unit: Any, threat_pos: Tuple[float, float]) -> Tuple[float, float]:
        """
        Force that pushes an entity AWAY from a threat.
        """
        tx, ty = threat_pos
        dx = unit.grid_x - tx
        dy = unit.grid_y - ty
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 0.1: return 0.0, 0.0
        
        # High intensity Flee force
        return (dx / dist) * 2.0, (dy / dist) * 2.0

    @staticmethod
    def calculate_obstacle_avoidance(unit: Any, obstacles: List[Any]) -> Tuple[float, float]:
        """
        Force that pushes an entity AWAY from static obstacles.
        """
        avoid_dx, avoid_dy = 0.0, 0.0
        for obs in obstacles:
            dx = unit.grid_x - obs.x
            dy = unit.grid_y - obs.y
            dist = math.sqrt(dx**2 + dy**2)
            
            # Use radius + small buffer
            avoid_rad = obs.radius + 1.0
            if dist < avoid_rad:
                if dist > 0:
                    # Exponential push as we get closer
                    force = (avoid_rad - dist) / avoid_rad
                    avoid_dx += (dx / dist) * force * 5.0
                    avoid_dy += (dy / dist) * force * 5.0
                else:
                    # On top? Push random
                    avoid_dx += 1.0
                    avoid_dy += 1.0
        return avoid_dx, avoid_dy

    @staticmethod
    def calculate_combined_steering(unit: Any, neighbors: List[Any], target_pos: Optional[Tuple[float, float]] = None, obstacles: List[Any] = [], doctrine: str = "CHARGE") -> Tuple[float, float]:
        """
        Calculates the final movement vector based on weighted Boids forces, Seek/Flee, and Obstacle Avoidance.
        """
        total_dx, total_dy = 0.0, 0.0
        
        # 0. Obstacle Avoidance (Highest Priority)
        if obstacles:
            obs_dx, obs_dy = SteeringManager.calculate_obstacle_avoidance(unit, obstacles)
            total_dx += obs_dx * 3.0
            total_dy += obs_dy * 3.0

        # 1. Routing Behavior (Flee instead of Seek)
        is_routing = getattr(unit, 'morale_state', 'Steady') == "Routing"
        
        if is_routing:
            # Flee from target position (which is usually enemy center of mass)
            if target_pos:
                flee_dx, flee_dy = SteeringManager.calculate_flee_steering(unit, target_pos)
                total_dx += flee_dx * 1.5 # High Flee weight
                total_dy += flee_dy * 1.5
        else:
            # 1. Seek / Kite Behavior
            if target_pos:
                target_x, target_y = target_pos
                dx = target_x - unit.grid_x
                dy = target_y - unit.grid_y
                dist = math.sqrt(dx**2 + dy**2)
                
                if doctrine == "KITE":
                    # Kiting: Maintain optimal range (e.g. 20-30 units)
                    # If too close, Flee. If too far, Seek/Stop.
                    optimal_range = 25.0
                    if dist < optimal_range:
                        # Too close! Back off.
                        total_dx -= (dx / dist) * 1.0 
                        total_dy -= (dy / dist) * 1.0
                    else:
                        # In range or far. Slow seek to maintain.
                        # Actually if we are far, we might want to close, but cautiously?
                        # For simple kiting, just stop if in range.
                        if dist > 35.0:
                             total_dx += (dx / dist) * 0.5 
                             total_dy += (dy / dist) * 0.5 
                             
                elif doctrine == "DEFEND":
                    # Defend: Stay near start or objective. 
                    # If target is enemy, only engage if close.
                    if dist < 15.0:
                        total_dx += (dx / dist) * 0.5
                        total_dy += (dy / dist) * 0.5
                    # Otherwise hold (maybe return to start? Not tracked here yet)
                    
                else: # CHARGE / Default
                    if dist > 0:
                        total_dx += (dx / dist) * 0.8 # Aggressive Seek
                        total_dy += (dy / dist) * 0.8
                
        if not neighbors:
            return total_dx, total_dy
            
        # 2. Separation (Avoid Crowding)
        sep_dx, sep_dy = 0.0, 0.0
        sep_dist = 2.0 # Minimum distance between units
        
        if doctrine == "KITE": sep_dist = 4.0 # Spread out more when kiting
        
        for n in neighbors:
            dx = unit.grid_x - n.grid_x
            dy = unit.grid_y - n.grid_y
            dist = math.sqrt(dx**2 + dy**2)
            if 0 < dist < sep_dist:
                sep_dx += dx / dist
                sep_dy += dy / dist
        
        total_dx += sep_dx * 1.5 # High weight for separation
        total_dy += sep_dy * 1.5
        
        # 3. Alignment (Match velocity/direction) - Simplification: use facing
        align_dx, align_dy = 0.0, 0.0
        for n in neighbors:
            # We assume 'facing' is degrees, convert to vector
            rad = math.radians(getattr(n, 'facing', 0))
            align_dx += math.cos(rad)
            align_dy += math.sin(rad)
            
        if neighbors:
            total_dx += (align_dx / len(neighbors)) * 0.3
            total_dy += (align_dy / len(neighbors)) * 0.3
            
        # 4. Cohesion (Stay with group)
        # CHARGE: Tight cohesion. KITE: Loose.
        if doctrine != "KITE":
            avg_x = sum(n.grid_x for n in neighbors) / len(neighbors)
            avg_y = sum(n.grid_y for n in neighbors) / len(neighbors)
            coh_dx = avg_x - unit.grid_x
            coh_dy = avg_y - unit.grid_y
            dist = math.sqrt(coh_dx**2 + coh_dy**2)
            if dist > 0:
                weight = 0.2 if doctrine == "CHARGE" else 0.1
                total_dx += (coh_dx / dist) * weight
                total_dy += (coh_dy / dist) * weight
            
        return total_dx, total_dy
