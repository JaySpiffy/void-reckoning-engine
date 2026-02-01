
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

    def select_target(self, unit, enemies: List, grid) -> Optional[Any]:
        """
        Selects the best target from a list of enemies.
        Implements Focus Fire logic.
        """
        if not enemies: return None
        
        # Filter by range validity? Usually handled by caller.
        
        best_target = None
        best_score = -999.0
        
        for e in enemies:
            score = 0.0
            
            # 1. Kill Probability (Low HP)
            hp_pct = e.current_hp / e.max_hp
            if hp_pct < 0.25:
                score += 50.0  # Finish them off!
            elif hp_pct < 0.5:
                score += 20.0
                
            # 2. Threat Level (High DPS)
            # Heuristic: Weapon count or known class
            if "Capital" in e.name or "Battleship" in e.name:
                score += 30.0
                
            # 3. Distance (Closer is easier to hit usually)
            dist = grid.get_distance(unit, e)
            score -= dist  # Penalty for distance
            
            # 4. Focus Fire History (Has this target been hit this round?)
            # Requires context, passed in? Or stored on unit?
            # Assuming 'e' tracks incoming damage/hits this turn?
            # If not available, we skip.
            
            if score > best_score:
                best_score = score
                best_target = e
                
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
        
        for dx, dy in moves:
            nx = unit.grid_x + dx
            ny = unit.grid_y + dy
            
            # Bounds check
            if not (0 <= nx < grid.width and 0 <= ny < grid.height):
                continue
                
            # Collision check? handled by grid usually, but we assume empty for score
            # Real collision check:
            if grid.get_unit_at(nx, ny) and grid.get_unit_at(nx, ny) != unit:
                continue
                
            val = self.score_position(unit, nx, ny, grid, enemies, optimal_range)
            if val > best_val:
                best_val = val
                best_move = (dx, dy)
                
        return best_move
