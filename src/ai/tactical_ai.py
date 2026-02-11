
from typing import Dict, List, Optional, Tuple, Any
import math

class TacticalAI:
    """
    Provides unit-level tactical decision making for combat.
    Used by Combat Phases to determine optimal moves and targets.
    """
    def __init__(self, ai_manager=None):
        self.ai = ai_manager
        
    def score_position(self, unit, x: int, y: int, grid, enemies: List, optimal_range: int) -> float:
        """
        Evaluates a potential grid position.
        """
        score = 0.0
        
        # 1. Range Score (sweet spot)
        # Find distance to nearest enemy
        min_dist = 999.0
        nearest_enemy = None
        for e in enemies:
             dist = math.sqrt((e.grid_x - x)**2 + (e.grid_y - y)**2)
             if dist < min_dist:
                 min_dist = dist
                 nearest_enemy = e
                 
        if nearest_enemy:
            dist_diff = abs(min_dist - optimal_range)
            # Higher score for being close to optimal range
            score += max(0, 20 - dist_diff)
            
        # 2. Cover / Safety (Simplification: Edge of map is bad?)
        # For now, we don't have distinct terrain types in grid generally, 
        # but if we did, we'd check tile metadata here.
        
        # 3. Flanking Bonus (Simulated)
        # If we are behind the enemy? (Requires facing data)
        
        # 4. Clustering (Formations)
        # Bonus for being near allies (if Doctrine says so)
        
        return score

    def select_target(self, unit, enemies: List, grid, context: Dict = None) -> Optional[Any]:
        """
        Selects the best target from a list of enemies.
        Implements Focus Fire logic.
        """
        if not enemies: return None
        
        best_target = None
        best_score = -999.0
        options = []
        
        # Get Doctrine for rationale
        doctrine = context.get("doctrine", "CHARGE") if context else "STANDARD"
        war_goal = context.get("war_goal", "NONE") if context else "NONE"
        
        for e in enemies:
            score = 0.0
            rationale = {}
            
            # 1. Kill Probability (Low HP)
            hp_pct = e.current_hp / e.max_hp
            if hp_pct < 0.25:
                score += 50.0  # Finish them off!
                rationale["low_hp_bonus"] = 50.0
            elif hp_pct < 0.5:
                score += 20.0
                rationale["med_hp_bonus"] = 20.0
                
            # 2. Threat Level (High DPS)
            if "Capital" in e.name or "Battleship" in e.name:
                score += 30.0
                rationale["high_threat_bonus"] = 30.0
                
            # 3. Distance (Closer is easier to hit usually)
            dist = grid.get_distance(unit, e)
            score -= dist  # Penalty for distance
            rationale["distance_penalty"] = -dist
            
            # [AAA Upgrade] Asymmetric Doctrine Logic
            if war_goal == "SIEGE":
                # Prioritize Starbases and Planets (Static Defense)
                if "Starbase" in e.name or "Platform" in e.name:
                    score += 100.0
                    rationale["siege_priority"] = 100.0
                elif "Planet" in e.name: # If planets are units
                     score += 80.0
                     rationale["siege_priority"] = 80.0
            
            elif war_goal == "BLITZ":
                # Ignore safety to kill Command/Capital units
                if "Capital" in e.name or "Command" in e.name:
                    score += 50.0
                    rationale["blitz_priority"] = 50.0
                # Ignore HP safety checks implicitly by boosting aggression
                if hp_pct > 0.5: 
                    score += 10.0 # Attack healthy targets too
            
            elif war_goal == "INTERCEPT":
                # Focus on Transports or weak support ships
                if "Transport" in e.name or "Colony" in e.name or "Constructor" in e.name:
                    score += 150.0
                    rationale["intercept_priority"] = 150.0
            
            elif war_goal == "GUERRILLA":
                # Avoid strong targets, hit weak ones
                if "Capital" in e.name or "Battleship" in e.name:
                    score -= 50.0
                    rationale["guerrilla_avoid"] = -50.0
                elif hp_pct < 0.3:
                    score += 40.0 # Pick off the weak
                    rationale["guerrilla_exploit"] = 40.0
            
            if score > best_score:
                best_score = score
                best_target = e
                
            options.append({
                "action": f"ATTACK:{getattr(e, 'id', e.name)}",
                "score": score,
                "rationale": rationale
            })
                
        # LOG DECISION ($DEEP_TRACER)
        if best_target and self.ai and hasattr(self.ai, 'decision_logger'):
            # Filter top 3 options
            top_options = sorted(options, key=lambda x: x["score"], reverse=True)[:3]
            self.ai.decision_logger.log_decision(
                decision_type="COMBAT_TARGET",
                actor_id=f"{unit.faction}:{getattr(unit, 'id', 'unknown')}",
                context={"doctrine": doctrine, "unit_type": unit.name, "enemy_count": len(enemies)},
                options=top_options,
                selected_action=f"ATTACK:{getattr(best_target, 'id', best_target.name)}"
            )
            
        return best_target
        
    def decide_movement(self, unit, grid, enemies: List, context: Dict) -> Tuple[int, int]:
        """
        Decides the best (dx, dy) for movement phase.
        """
        doctrine = context.get("doctrine", "CHARGE")
        
        # Determine optimal range based on weapons
        weapons = [c for c in unit.components if c.type == "Weapon"]
        max_range = max([c.weapon_stats.get("Range", 0) for c in weapons], default=0)
        
        optimal_range = 1 # melee
        if doctrine == "KITE":
            optimal_range = max_range * 0.9
        elif doctrine == "CHARGE":
            optimal_range = 1.0
        elif doctrine == "DEFEND":
            optimal_range = 10.0 # Engage at medium range but hold ground
            
        # Sample possible moves (including 0,0)
        moves = [(0,0), (1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,-1), (1,-1), (-1,1)]
        best_move = (0,0)
        best_val = -9999.0
        move_options = []
        
        for dx, dy in moves:
            nx = unit.grid_x + dx
            ny = unit.grid_y + dy
            
            # Bounds check
            if not (0 <= nx < grid.width and 0 <= ny < grid.height):
                continue
                
            # Collision check
            if grid.get_unit_at(nx, ny) and grid.get_unit_at(nx, ny) != unit:
                continue
                
            val = self.score_position(unit, nx, ny, grid, enemies, optimal_range)
            
            # [AAA Upgrade] Asymmetric Movement Logic
            war_goal = context.get("war_goal", "NONE")
            if war_goal == "BLITZ":
                # Move towards enemy capital/command regardless of danger
                # (Simplified as moving towards nearest enemy often)
                pass 
            elif war_goal == "GUERRILLA":
                # [AAA Refinement] Kiting Logic
                # If we have a nearest enemy, try to stay at max range
                if enemies:
                    # Find nearest enemy to this hypothetical position (nx, ny)
                    # We can't reuse the loop form score_position easily without passing it back
                    # So we allow score_position to handle the base scoring, and we modify 'optimal_range' passed in.
                    # But wait, optimal_range was already set to max_range * 0.9 for KITE doctrine?
                    # GUERRILLA war_goal implies KITE doctrine usually, but let's enforce it here.
                    
                    # We can add an explicit bonus for range > 80% of max
                    # And penalty for range < 50%
                    
                    min_dist_sq = 9999.0
                    for e in enemies:
                        d2 = (e.grid_x - nx)**2 + (e.grid_y - ny)**2
                        if d2 < min_dist_sq: min_dist_sq = d2
                    
                    dist = math.sqrt(min_dist_sq)
                    
                    # Kiting Bonus: Sweet spot is 95-110% of max range (Strict Edge Skimming)
                    if max_range > 0:
                        ratio = dist / max_range
                        if 0.95 <= ratio <= 1.1:
                            val += 50.0 # Huge bonus for perfect kiting distance
                        elif ratio < 0.95:
                             # Penalize getting closer than 95%
                             # We want max range for Guerrilla
                            val -= 20.0 
                            if ratio < 0.5: val -= 50.0 # Too close!
                        elif ratio > 1.2:
                            val -= 10.0 # Too far

                     # [STALEMATE BREAKER]
                    # If battle is stalling (no damage for > 150 rounds), force engagement.
                    # Kiting is disabled in this state.
                    mgr = context.get("manager")
                    if mgr and getattr(mgr, 'rounds_since_last_damage', 0) > 150:
                         # print(f"DEBUG: STALEMATE BREAKER ACTIVE for unit {unit.name} (No Dmg for {mgr.rounds_since_last_damage} rounds)")
                         val = 0.0 # Reset kiting bonuses
                         # Add aggressive closure bonus (dist is distance to nearest enemy from nx,ny)
                         # Pull towards enemy
                         val += (30.0 - dist) 
                         # This overrides the "GUERRILLA" keep-away logic effectively turning it into a CHARGE

            # [FEATURE] Dynamic Formation Cohesion
            # Try to stay in formation relative to Fleet Anchor
            fleet_ref = getattr(unit, 'fleet', None)
            if fleet_ref and hasattr(fleet_ref, 'saved_formation'):
                 # Check if we have an anchor
                 # We can calculate this once per unit per decision, or pass in context.
                 # For now, let's find the Anchor (Flagship) in the fleet units
                 # This search is O(N) per unit per move -> O(N^2) total. Acceptable for <200 units.
                 
                 # Optimization: Cache anchor on fleet or context?
                 # Let's find "Unit with offset (0,0)" or closest to it.
                 # Or just first unit in MAIN group.
                 
                 # Fast fetch relative offset
                 uid = str(getattr(unit, 'id', id(unit)))
                 my_offset = fleet_ref.saved_formation.get(uid)
                 
                 if my_offset:
                     # Find Anchor (O(N) search)
                     anchor = None
                     min_d2 = 999999.0
                     
                     # Get Allies from context
                     # context.get("manager") is CombatState
                     # active_units_list is best
                     allies = [a for a in context.get("active_units_list", []) 
                               if getattr(a, 'fleet', None) == fleet_ref and a != unit and a.is_alive()]
                     
                     for ally in allies:
                         uid_a = str(getattr(ally, 'id', id(ally)))
                         off_a = fleet_ref.saved_formation.get(uid_a)
                         if off_a:
                             d2 = off_a[0]**2 + off_a[1]**2
                             if d2 < min_d2:
                                 min_d2 = d2
                                 anchor = ally
                                 
                     if anchor:
                         uid_a = str(getattr(anchor, 'id', id(anchor)))
                         off_a = fleet_ref.saved_formation.get(uid_a)
                         if off_a:
                             ax, ay = anchor.grid_x, anchor.grid_y
                             
                             # Determine Coords
                             # Re-derive Facing logic from CombatState check
                             f_id = str(unit.faction).lower()
                             is_faction_a = ("factiona" in f_id) or (f_id.startswith("a")) or (f_id == "factiona")
                             
                             # My Relative Offset from Anchor
                             # Delta = MyOffset - AnchorOffset
                             dx_rel = my_offset[0] - off_a[0]
                             dy_rel = my_offset[1] - off_a[1]
                             
                             if not is_faction_a:
                                 dx_rel = -dx_rel
                                 # Standard mirroring of X
                             
                             ideal_x = ax + dx_rel
                             ideal_y = ay + dy_rel
                             
                             dist_to_ideal = math.sqrt((nx - ideal_x)**2 + (ny - ideal_y)**2)
                             
                             # Score
                             if dist_to_ideal < 15:
                                 val += (15 - dist_to_ideal) * 1.5 # Strong pull
                     
            if val > best_val:
                best_val = val
                best_move = (dx, dy)
            
            move_options.append({
                "action": f"MOVE:{dx},{dy}",
                "score": val,
                "rationale": {"pos": (nx, ny), "kiting_mod": "GUERRILLA" if war_goal == "GUERRILLA" else "NONE"}
            })
        
        # LOG DECISION ($DEEP_TRACER)
        if self.ai and hasattr(self.ai, 'decision_logger'):
            top_moves = sorted(move_options, key=lambda x: x["score"], reverse=True)[:3]
            self.ai.decision_logger.log_decision(
                decision_type="COMBAT_MOVE",
                actor_id=f"{unit.faction}:{getattr(unit, 'id', 'unknown')}",
                context={"doctrine": doctrine, "optimal_range": optimal_range},
                options=top_moves,
                selected_action=f"MOVE:{best_move[0]},{best_move[1]}"
            )
                
        return best_move
