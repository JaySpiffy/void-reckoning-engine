class MovementCalculator:
    """
    Calculates movement vectors for units on the tactical grid based on doctrine.
    """

    @staticmethod
    def calculate_movement_vector(unit, target, doctrine: str, grid):
        """
        Calculates movement delta (dx, dy) based on doctrine.
        """
        # [PHASE 6] Unit-Level Directive Override
        if hasattr(unit, 'tactical_directive') and unit.tactical_directive and unit.tactical_directive != "HOLD_GROUND":
            # If unit has specific orders (e.g. from Fleet), override the faction doctrine
            directive = unit.tactical_directive
            if directive == "KITE": doctrine = "KITE"
            elif directive == "CLOSE_QUARTERS": doctrine = "CHARGE"
            
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
