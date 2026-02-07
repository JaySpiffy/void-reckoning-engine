class MovementCalculator:
    """
    Calculates movement vectors for units on the tactical grid based on doctrine.
    """

    @staticmethod
    def calculate_movement_vector(unit, target, doctrine: str, grid, dt: float = 1.0):
        """
        Calculates movement delta (dx, dy) based on doctrine.
        Returns a vector. Magnitude 1.0 = Max Speed.
        """
        # [PHASE 6] Unit-Level Directive Override
        if hasattr(unit, 'tactical_directive') and unit.tactical_directive and unit.tactical_directive != "HOLD_GROUND":
            # If unit has specific orders (e.g. from Fleet), override the faction doctrine
            directive = unit.tactical_directive
            if directive == "KITE": doctrine = "KITE"
            elif directive == "CLOSE_QUARTERS": doctrine = "CHARGE"
            
        # Dispatch based on domain
        domain = getattr(unit, 'domain', 'ground')
        if domain == "space" and hasattr(unit, 'movement_comp') and unit.movement_comp:
            return MovementCalculator._calculate_inertial_movement(unit, target, doctrine, grid, dt)
        else:
            return MovementCalculator._calculate_ground_movement(unit, target, doctrine, grid)

    @staticmethod
    def _calculate_inertial_movement(unit, target, doctrine, grid, dt):
        """
        Calculates movement for space units using inertia, turn rates, and acceleration.
        Returns (dx, dy) scaled by current_speed / max_speed.
        """
        import math
        
        mc = unit.movement_comp
        # Default stats if missing (safety)
        turn_rate = getattr(mc, 'turn_rate', 30.0)
        accel = getattr(mc, 'acceleration', 1.0)
        max_speed = mc.base_movement_points
        
        # 1. Determine Desired Heading
        dx = target.grid_x - unit.grid_x
        dy = target.grid_y - unit.grid_y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 0.1: return 0, 0
        
        # Logic for desired position based on doctrine
        desired_x, desired_y = target.grid_x, target.grid_y
        
        # Kiting Logic
        if doctrine == "KITE":
            # Ideal range ~80% of max range
            max_range = getattr(unit, 'weapon_range_default', 24)
            if hasattr(unit, 'components'):
                 ranges = [c.weapon_stats.get("Range", 0) for c in unit.components if c.type == "Weapon" and not c.is_destroyed]
                 if ranges: max_range = max(ranges)
            
            ideal_dist = max_range * 0.8
            if dist < ideal_dist:
                # Move AWAY
                desired_x = unit.grid_x - dx
                desired_y = unit.grid_y - dy
            elif dist > max_range:
                # Close in
                pass 
            else:
                 # Orbit / Maintain?
                 # For simple kiting, just stop or drift? 
                 # Let's slow down
                 pass

        # Calculate angle to desired point
        target_angle_rad = math.atan2(desired_y - unit.grid_y, desired_x - unit.grid_x)
        target_angle_deg = math.degrees(target_angle_rad)
        
        # 2. Update Facing (Turn Rate)
        current_facing = mc.facing
        
        # Normalize angles
        target_angle_deg = target_angle_deg % 360
        current_facing = current_facing % 360
        
        diff = target_angle_deg - current_facing
        if diff > 180: diff -= 360
        elif diff < -180: diff += 360
        
        turn_amount = turn_rate * dt
        
        if abs(diff) <= turn_amount:
            mc.facing = target_angle_deg
        else:
            if diff > 0: mc.facing += turn_amount
            else: mc.facing -= turn_amount
            
        mc.facing = mc.facing % 360
        
        # 3. Update Speed (Acceleration)
        # If facing is roughly on target, accelerate. If sharp turn, decelerate?
        # EaW Style: Ships usually maintain speed but can slow down? 
        # Let's assume they try to reach max speed unless stopping.
        
        # Simple throttle logic:
        # If we need to turn > 45 degrees, throttle down?
        throttle = 1.0
        if abs(diff) > 45: throttle = 0.5
        if abs(diff) > 90: throttle = 0.1
        
        # Stop if extremely close/on top and HOLDing?
        if dist < 1.0 and doctrine != "CHARGE": throttle = 0.0
        
        desired_speed = max_speed * throttle
        
        if mc.current_speed < desired_speed:
            mc.current_speed = min(desired_speed, mc.current_speed + (accel * dt))
        elif mc.current_speed > desired_speed:
            mc.current_speed = max(desired_speed, mc.current_speed - (accel * dt))
            
        # 4. Calculate Vector
        rad = math.radians(mc.facing)
        vx = math.cos(rad)
        vy = math.sin(rad)
        
        # Return normalized vector scaled by speed factor (current / max)
        # RealTimeManager multiplies by (max_speed * dt).
        # We want result to be (current_speed * dt).
        # So factor = current_speed / max_speed
        
        if max_speed > 0:
            factor = mc.current_speed / max_speed
        else:
            factor = 0
            
        return vx * factor, vy * factor

    @staticmethod
    def _calculate_ground_movement(unit, target, doctrine, grid):
        """Legacy grid-based movement for ground units."""
        dist = grid.get_distance(unit, target)
        step_x = 0
        if target.grid_x > unit.grid_x: step_x = 1
        elif target.grid_x < unit.grid_x: step_x = -1
        
        step_y = 0
        if target.grid_y > unit.grid_y: step_y = 1
        elif target.grid_y < unit.grid_y: step_y = -1
        
        # Determine engagement ranges based on weaponry
        max_range = getattr(unit, 'weapon_range_default', 24)
        if hasattr(unit, 'components'):
             ranges = [c.weapon_stats.get("Range", 0) for c in unit.components if c.type == "Weapon" and not c.is_destroyed]
             if ranges: max_range = max(ranges)
             
        # Ideal range: Get closer to ensure hits (60% instead of 80% to force engagement)
        ideal_min = max(1, int(max_range * 0.3))
        ideal_max = max(2, int(max_range * 0.6))
        
        # [AI OVERRIDE] If out of range, ALWAYS close distance (unless Kiting with Long Range)
        if dist > max_range and doctrine != "KITE":
             return step_x, step_y
        
        if doctrine == "CHARGE":
             # Melee/Assault: Close for the kill
             if max_range <= 2: 
                  if dist > 1.5: return step_x, step_y
                  else: return 0, 0
             
             # Hybrid: Close to optimal firing range
             if dist > ideal_max: return step_x, step_y
             elif dist < ideal_min: return -step_x, -step_y 
             else: return 0, 0
             
        elif doctrine == "KITE":
             # Maintain distance between 30% and 60% range (or stay at max range)
             if max_range < 10: return step_x, step_y
             
             if dist < ideal_min: return -step_x, -step_y
             elif dist > ideal_max: return step_x, step_y
             else: return 0, 0
                 
        elif doctrine == "DEFEND":
             # [ADVANCED AI] Proximity Logic
             if dist > 10: return step_x, step_y
             elif dist < 5: return -step_x, -step_y
             else: return 0, 0
             
        return 0, 0
