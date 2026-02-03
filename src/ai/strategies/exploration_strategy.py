
import random
from typing import List, Any, TYPE_CHECKING
from src.models.fleet import Fleet, TaskForce

if TYPE_CHECKING:
    from src.managers.ai_manager import StrategicAI
    from src.managers.ai_manager import FactionPersonality

class ExplorationStrategy:
    """
    Handles exploration and scouting logic.
    Identifies unknown systems and dispatches scouts.
    """
    def __init__(self, ai_manager: 'StrategicAI'):
        self.ai = ai_manager

    def handle_exploration(self, faction: str, available_fleets: List[Fleet], f_mgr: Any, personality: 'FactionPersonality'):
        """
        Assigns idle scouts to explore frontier systems.
        """
        # Get pre-calculated frontier from cache
        frontier = self.ai.turn_cache.get("exploration_frontiers", {}).get(faction, set())
        
        if not frontier:
            return
            
        # Filter for Scouts OR Small Fast Fleets (Potential Scouts)
        scouts = []
        for f in available_fleets:
            if getattr(f, 'is_scout', False):
                scouts.append(f)
            elif len(f.units) <= 5 and f.speed >= 6:
                scouts.append(f)
        
        # Fallback: If no scouts, but we are rich (>10k), use any available fleet
        if not scouts and f_mgr.requisition > 10000:
            scouts = available_fleets[:1]
            if scouts and self.ai.engine.logger:
                self.ai.engine.logger.campaign(f"[{faction}] WEALTH FALLBACK: Using {scouts[0].id} as emergency scout")

        if not scouts:
            return

        # Prioritize frontier nodes
        frontier_list = list(frontier)
        if hasattr(f_mgr, 'home_planet_name'):
            # Optimization: Sort frontier by distance to home to keep expansion concentric
            hq = next((p for p in self.ai.engine.all_planets if p.name == f_mgr.home_planet_name), None)
            if hq:
                frontier_list.sort(key=lambda p_name: (
                    ((next((p for p in self.ai.engine.all_planets if p.name == p_name), hq).system.x - hq.system.x)**2 + 
                     (next((p for p in self.ai.engine.all_planets if p.name == p_name), hq).system.y - hq.system.y)**2)
                ))
            else:
                random.shuffle(frontier_list)
        else:
            random.shuffle(frontier_list)
        
        assigned_scouts = []
        
        for scout in scouts:
            if not frontier_list: break
            
            # Pick a target
            target_name = frontier_list.pop()
            
            # Find planet object
            target = next((p for p in self.ai.engine.all_planets if p.name == target_name), None)
            if not target: continue
            
            # Create Scouting Task Force
            self.ai.tf_counter += 1
            tf = TaskForce(f"SCOUT-{self.ai.tf_counter}", faction)
            tf.add_fleet(scout)
            scout.is_scout = True # Activate scout mode (speed boost, behavior)
            tf.target = target
            tf.strategy = "SCOUT"
            tf.state = "TRANSIT" # Skip mustering for single scouts

            # Force immediate movement
            if scout.current_node:
                scout.move_to(target, engine=self.ai.engine)
            elif self.ai.engine.logger:
                self.ai.engine.logger.warning(f"[{faction}] Explorer {scout.id} has NO current_node for move_to(target={target_name})")
            
            self.ai.task_forces[faction].append(tf)
            assigned_scouts.append(scout)
            
            if self.ai.engine.logger:
                self.ai.engine.logger.campaign(f"[{faction}] Explorer {scout.id} sent to {target_name}")
            
        # Remove assigned from available
        for s in assigned_scouts:
            if s in available_fleets:
                available_fleets.remove(s)
