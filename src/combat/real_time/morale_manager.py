import math
from typing import List, Any
from src.core import balance as bal

class MoraleManager:
    """
    Handles morale calculations for units in real-time combat.
    Inspired by Total War: Warhammer 3.
    """
    
    @staticmethod
    def update_unit_morale(unit: Any, dt: float, all_units: List[Any], grid: Any):
        """Processes morale changes for a single unit over time dt."""
        if not unit.is_alive() or unit.morale_state == "Shattered":
            return
            
        # 1. Base Decay / Recovery
        # Naturally recover morale if not recently damaged
        if unit.time_since_last_damage > 10.0:
            unit.morale_current += bal.MORALE_RECOVERY_RATE * dt
        else:
            unit.time_since_last_damage += dt

        # 2. Damage Penalties (Recent Loss)
        # Losing a high % of HP in a short window causes rapid morale drop
        if unit.recent_damage_taken > 0:
            hp_pct_lost = (unit.recent_damage_taken / unit.max_hp) * 100
            # Penalty scales with % of HP lost
            unit.morale_current -= hp_pct_lost * bal.MORALE_DAMAGE_WEIGHT
            # Slowly bleed off recent damage tracking (e.g., 20% per second)
            unit.recent_damage_taken -= unit.recent_damage_taken * 0.2 * dt
            if unit.recent_damage_taken < 0.1: unit.recent_damage_taken = 0
            
            # [Phase 23] Shell Shock: High single-hit damage
            # Handled via is_shell_shocked flag on Unit if we want, or calculated here.
            # Simpler: If HP lost > 10% in ONE hit, the Unit.take_damage method reduced Morale directly.
            # So here we just handle the sustained effect:
            
        # [Phase 23] Suppression & Pinned Morale Drain
        if getattr(unit, 'is_pinned', False):
             unit.morale_current -= 15.0 * dt # Massive drain when pinned (Under Heavy Fire)
        elif getattr(unit, 'is_suppressed', False):
             unit.morale_current -= 2.0 * dt # Light anxiety

        # 3. Flanking & Rear Penalties
        # Use TacticalGrid to check proximity of enemies in flanks/rear
        nearby_enemies = grid.query_units_in_range(unit.grid_x, unit.grid_y, radius=15.0)
        for enemy in nearby_enemies:
            if enemy.faction != unit.faction and enemy.is_alive():
                bearing = grid.get_relative_bearing(unit, enemy)
                # 0=Front, 90/270=Flank, 180=Rear
                if 135 <= bearing <= 225: # Rear
                    unit.morale_current -= bal.MORALE_REAR_PENALTY * dt
                elif (45 <= bearing <= 135) or (225 <= bearing <= 315): # Flank
                    unit.morale_current -= bal.MORALE_FLANK_PENALTY * dt

        # 4. Friendly Proximal Death (Army Losses)
        # Check for recently destroyed units nearby
        
        # 5. [PHASE 30] Special Traits: Fear, Terror, and Inspiration
        # Fear: Drains morale of nearby enemies. 
        # Terror: Larger drain, can cause immediate routing if morale low.
        # Inspiration: Nearby allies get morale boost.
        for other in nearby_enemies:
            if other.faction != unit.faction:
                if "Fear" in getattr(other, 'abilities', {}):
                    unit.morale_current -= bal.MORALE_FEAR_DRAIN * dt
                if "Terror" in getattr(other, 'abilities', {}):
                    unit.morale_current -= bal.MORALE_TERROR_DRAIN * dt
                    if unit.morale_current < 20: # Terror effect: break early
                        unit.morale_state = "Routing"
            else:
                if "Inspiring" in getattr(other, 'abilities', {}):
                    unit.morale_current += bal.MORALE_INSPIRATION_BOOST * dt

        # 6. Friendly Proximal Support
        # Units gain morale when surrounded by allies
        allies = [o for o in nearby_enemies if o.faction == unit.faction]
        if len(allies) > 3:
            unit.morale_current += 1.0 * dt

        # 6. Clamp & State Transitions
        unit.morale_current = max(0, min(unit.morale_max, unit.morale_current))
        
        # [FIX] State Hysteresis: Prevent "Morale Yo-Yo" by requiring thresholds to rally.
        if unit.morale_current <= 0:
            unit.morale_state = "Routing"
        else:
            if unit.morale_state == "Routing":
                # Unit is Routing. It only stops routing if it rallies (Morale > 50)
                if unit.morale_current > 50:
                    unit.morale_state = "Shaken" # Transition to Shaken first
            elif unit.morale_state == "Shaken":
                # Unit is Shaken. It rallies to Steady if Morale > 40, 
                # or breaks to Routing if Morale <= 0 (handled above)
                if unit.morale_current > 40:
                    unit.morale_state = "Steady"
            else:
                # Unit is Steady. It becomes Shaken if Morale < 30
                if unit.morale_current < 30:
                    unit.morale_state = "Shaken"

        # if unit.morale_state == "Routing" and prev_state != "Routing":
            # print(f"BREAK: {unit.name} is routing!")
