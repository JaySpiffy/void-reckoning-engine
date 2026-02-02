import random
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from src.models.fleet import TaskForce, Fleet
from src.utils.profiler import profile_method
from src.config import logging_config 
from src.reporting.telemetry import EventCategory

if TYPE_CHECKING:
    from src.core.interfaces import IEngine
    from universes.base.personality_template import FactionPersonality

class TaskForceManager:
    """
    Manages the lifecycle and strategic operations of AI Task Forces.
    Handles formation, reinforcement, raiding, and withdrawal logic.
    """
    
    def __init__(self, ai_manager):
        self.ai_manager = ai_manager
        self.engine = ai_manager.engine
        self.task_forces: Dict[str, List[TaskForce]] = {} # {Faction: [TaskForce]}
        self._fleet_to_tf_map: Dict[str, TaskForce] = {} # {FleetID: TaskForce} (Inverse Index)
        self.tf_counter = 0

    def get_task_force_for_fleet(self, fleet: Fleet) -> Optional[TaskForce]:
        """Finds the TaskForce containing the given fleet. O(1) Lookup."""
        if not fleet: return None
        return self._fleet_to_tf_map.get(fleet.id)

    def ensure_faction_list(self, faction: str) -> None:
        """Ensures the task force list exists for a faction and cleans up empty TFs."""
        if faction not in self.task_forces:
            self.task_forces[faction] = []
        # Cleanup empty TFs
        self.task_forces[faction] = [tf for tf in self.task_forces[faction] if tf.fleets]

    def manage_task_forces_lifecycle(self, faction: str, available_fleets: List[Fleet], 
                                    f_mgr: Any, personality: 'FactionPersonality', 
                                    econ_health: dict, strategic_plan: Any) -> None:
        """
        Handles post-strategy operations: Task Force cleaning, patrols, and retreats.
        Delegated from StrategicAI._handle_post_strategy_ops.
        """
        self.ensure_faction_list(faction)
        
        # 1. Update Task Forces with Tactical Assessment
        econ_state = econ_health['state']
        
        # Sort task forces so DEF ones get first pick of reinforcements
        sorted_tfs = sorted(self.task_forces[faction], key=lambda x: 0 if x.id.startswith("DEF") else 1)
        
        for tf in list(sorted_tfs): # Use list() to avoid removal issues during iteration
            tf.turns_active += 1
            
            # Check Status of Fleets (Engaged?)
            engaged_fleets = [f for f in tf.fleets if getattr(f, 'is_engaged', False)]
            if engaged_fleets:
                tf.state = "ATTACKING"
            elif tf.state == "ATTACKING" and not engaged_fleets:
                # Battle over?
                if tf.target and getattr(tf.target, 'owner', None) == faction:
                    print(f"  > [VICTORY] Task Force {tf.id} captured {tf.target.name}. Disbanding.")
                    tf.state = "IDLE"
                    self.log_tf_effectiveness(tf)
                    if tf in self.task_forces[faction]:
                        self.task_forces[faction].remove(tf)
                    continue
                else:
                    # Lost or retreated?
                    tf.state = "TRANSIT" # Try again?

            # Scout TF Completion Check
            if tf.composition_type == "SCOUT":
                fleets_done = True
                for f in tf.fleets:
                    if getattr(f, 'exploration_target_system', None) is not None:
                        fleets_done = False
                        break
                    if tf.state == "TRANSIT" and f.location != tf.target:
                        fleets_done = False
                        break
                
                if fleets_done:
                     print(f"  > [SCOUT] Task Force {tf.id} completed exploration mission. Disbanding.")
                     tf.state = "IDLE"
                     for f in tf.fleets:
                         f.is_scout = False
                     self.log_tf_effectiveness(tf)
                     if tf in self.task_forces[faction]:
                         self.task_forces[faction].remove(tf)
                     continue

            # Construction TF Completion Check
            if getattr(tf, 'mission_role', None) == "CONSTRUCTION":
                # Check if Starbase exists at target
                if tf.target and hasattr(tf.target, 'system'):
                     # Target is a Node
                     sys = tf.target.system
                     has_built = False
                     for sb in sys.starbases:
                         if sb.faction == faction and sb.is_alive():
                             # Check if it is at the specific node?
                             # Starbases are units in a fleet. Find the fleet.
                             sb_fleet = next((f for f in self.engine.fleets if any(u == sb for u in f.units)), None)
                             if sb_fleet and sb_fleet.location == tf.target:
                                 if not sb.is_under_construction:
                                     has_built = True
                                     break
                     
                     if has_built:
                         print(f"  > [CONSTRUCT] Task Force {tf.id} completed Starbase at {tf.target.name}. Disbanding.")
                         tf.state = "IDLE"
                         self.log_tf_effectiveness(tf)
                         if tf in self.task_forces[faction]:
                             self.task_forces[faction].remove(tf)
                         continue

            # Raid Plunder Logic
            if getattr(tf, 'is_raid', False) and tf.state == "ATTACKING":
                 if tf.raid_timer >= tf.raid_duration:
                    if not tf.target:
                        tf.state = "IDLE"
                        if tf in self.task_forces[faction]:
                            self.task_forces[faction].remove(tf)
                        continue

                    loot = getattr(tf.target, 'income_req', 100) * 0.5
                    f_mgr.requisition += loot
                    print(f"  > [PLUNDER] {faction} raids {tf.target.name} for {loot} Requisition!")
                    
                    if self.engine.diplomacy:
                        target_owner = getattr(tf.target, 'owner', "Neutral")
                        if target_owner != "Neutral" and target_owner != faction:
                              self.engine.diplomacy.add_grudge(target_owner, faction, 20, "Raided our world")

                    # Issue Retreat
                    friendly = [p for p in self.engine.planets_by_faction.get(faction, [])]
                    if friendly:
                        px, py = tf.target.system.x, tf.target.system.y
                        retreat_target = min(friendly, key=lambda p: ((p.system.x - px)**2 + (p.system.y - py)**2))
                        for f in tf.fleets:
                            f.retreat(retreat_target)
                    
                    tf.state = "IDLE"
                    if tf in self.task_forces[faction]:
                        self.task_forces[faction].remove(tf)
                    continue

            # Calculate Total TF Power
            total_power = sum(f.power for f in tf.fleets if not f.is_destroyed)
            
            if tf.state == "WITHDRAWING":
                self.execute_fighting_retreat(tf)
            
            if tf.state in ["MUSTERING", "ATTACKING"]:
                if tf.target:
                    # Estimate Defender Power
                    theater_stats = self.ai_manager.get_cached_theater_power(tf.target, faction)
                    defender_power = sum(p for f, p in theater_stats.items() if f != faction)
                    
                    # 4X Logic: Personality-driven ratio
                    aggression_mult = personality.aggression if not tf.id.startswith("DEF") else (personality.aggression * 1.5)
                    required_ratio = 1.5 / aggression_mult
                    
                    reinforcements_pulled = 0
                    max_pulls = 3
                    
                    if total_power < defender_power * required_ratio and len(tf.fleets) < 10:
                        while available_fleets and len(tf.fleets) < 10 and reinforcements_pulled < max_pulls:
                            current_power = sum(f.power for f in tf.fleets)
                            if current_power >= defender_power * 1.1 and not tf.id.startswith("DEF"):
                                break
                            
                            f_to_add = self._select_best_reinforcement(tf, available_fleets)
                            if not f_to_add: break
                            
                            available_fleets.remove(f_to_add)
                            tf.add_fleet(f_to_add)
                            # Sync Map
                            self._fleet_to_tf_map[f_to_add.id] = tf
                            reinforcements_pulled += 1
                            
                            print(f"  > [Reinforce] {faction} {tf.id} pulling reinforcements for {tf.target.name} (Power: {sum(f.power for f in tf.fleets)} vs Req: {int(defender_power * required_ratio)})")
                            if tf.id.startswith("DEF"): break
            
            tf.update(self.engine)

        # 3. Battle Management / Retreat Logic
        my_engaged_fleets = [f for f in self.engine.fleets if f.faction == faction and getattr(f, 'is_engaged', False)]
        locations = list(set([f.location for f in my_engaged_fleets]))
        
        for loc in locations:
            theater_stats = self.ai_manager.get_cached_theater_power(loc, faction)
            my_power = theater_stats.get(faction, 0)
            enemy_power = sum(p for f, p in theater_stats.items() if f != faction)
            
            if enemy_power > 0:
                ratio = my_power / enemy_power
                
                rep_fleet = next((f for f in my_engaged_fleets if f.location == loc), None)
                threshold = personality.retreat_threshold
                if rep_fleet and strategic_plan:
                     threshold = self.ai_manager.calculate_dynamic_retreat_threshold(rep_fleet, loc, personality, strategic_plan)

                if ratio < threshold:
                    print(f"  > [RETREAT] {faction} retreating from {loc.name} (Odds: {ratio:.2f} vs Threshold {threshold:.2f})")
                    fleets_here = [f for f in my_engaged_fleets if f.location == loc]
                    
                    for f in fleets_here:
                        tf = self.get_task_force_for_fleet(f)
                        if tf:
                            if tf.state != "WITHDRAWING":
                                self.initiate_staged_withdrawal(tf, loc, personality)
                        else:
                            safe_havens = [p for p in self.engine.planets_by_faction.get(faction, []) if p != loc]
                            fallback = safe_havens[0] if safe_havens else None
                            if fallback:
                                f.retreat(fallback)
                            else:
                                print(f"  > [DOOM] Fleet {f.id} has nowhere to retreat!")

    def initiate_staged_withdrawal(self, task_force: TaskForce, current_location, personality: 'FactionPersonality') -> None:
        """Sets up a withdrawal plan for a task force."""
        rally_target = None
        f_mgr = self.engine.factions.get(task_force.faction)
        if not f_mgr: return
        
        if personality.rally_point_preference == "CAPITAL":
            rally_target = next((p for p in self.engine.all_planets if p.name == f_mgr.home_planet_name), None)
        elif personality.rally_point_preference == "NEAREST_SAFE":
             my_planets = self.engine.planets_by_faction.get(task_force.faction, [])
             best_dist = 9999
             curr_pos = current_location.position if hasattr(current_location, 'position') else (0,0)
             
             for p in my_planets:
                 if getattr(p, 'is_sieged', False): continue
                 if hasattr(p, 'system'):
                     d = ((p.system.x - curr_pos[0])**2 + (p.system.y - curr_pos[1])**2)**0.5
                     if d < best_dist:
                         best_dist = d
                         rally_target = p
                         
        elif personality.rally_point_preference == "STRATEGIC_CHOKEPOINT":
             my_planets = self.engine.planets_by_faction.get(task_force.faction, [])
             candidates = []
             for p in my_planets:
                 if getattr(p, 'is_sieged', False): continue
                 if hasattr(p, 'system') and len(p.system.connections) <= 2:
                     candidates.append(p)
             
             if candidates:
                 best_dist = 9999
                 curr_pos = current_location.position if hasattr(current_location, 'position') else (0,0)
                 for p in candidates:
                     d = ((p.system.x - curr_pos[0])**2 + (p.system.y - curr_pos[1])**2)**0.5
                     if d < best_dist:
                         best_dist = d
                         rally_target = p
        
        if not rally_target and f_mgr.known_planets:
             rally_target = next((p for p in self.engine.all_planets if p.name == f_mgr.home_planet_name), None)
             
        if rally_target:
             print(f"  > [TACTICAL] Task Force {task_force.id} initiating WITHDRAWAL to {rally_target.name}")
             task_force.state = "WITHDRAWING"
             task_force.withdrawal_plan = {
                 "rally_point": rally_target.name,
                 "fighting_retreat": True
             }
             task_force.target = rally_target
             
             # [PHASE 6] Mission Update Log
             if logging_config.LOGGING_FEATURES.get('task_force_mission_tracking', False):
                 if hasattr(self.engine, 'logger') and hasattr(self.engine.logger, 'mission'):
                     self.engine.logger.mission(f"[{task_force.faction}] TF {task_force.id} RETREATING to {rally_target.name}")

    def execute_fighting_retreat(self, task_force: TaskForce) -> None:
        """Manages the rearguard action while the rest of the task force withdraws."""
        if not task_force.withdrawal_plan: return
        
        candidates = [f for f in task_force.fleets if getattr(f, 'is_engaged', False)]
        if not candidates: return

        # Capability-Aware Rearguard: Prefer heavy hitters (Battleships/Cruisers)
        candidates.sort(key=lambda f: (
            f.get_capability_matrix().get("Battleship", 0) * 10 + 
            f.get_capability_matrix().get("Cruiser", 0) * 5 +
            f.power / 1000
        ), reverse=True)
        rearguard = candidates[0]
        
        rally_point_name = task_force.withdrawal_plan.get("rally_point")
        rally_point = next((p for p in self.engine.all_planets if p.name == rally_point_name), None)
        
        if rally_point:
             for f in task_force.fleets:
                 if f != rearguard and getattr(f, 'is_engaged', False):
                     f.retreat(rally_point)
        
        if rearguard.units:
             current_hp = sum(u.current_hp for u in rearguard.units)
             max_hp = sum(u.max_hp for u in rearguard.units)
             hp_pct = current_hp / max(1, max_hp)
             
             if hp_pct < 0.3:
                 print(f"  > [TACTICAL] Rearguard {rearguard.id} collapsing (<30% HP). Retreating!")
                 rearguard.retreat(rally_point)

    @profile_method
    def form_raiding_task_force(self, faction: str, available_fleets: List[Fleet]) -> None:
        """Forms a small, fast task force to raid enemy economy when bankrupt."""
        f_mgr = self.engine.factions[faction]
        potential_targets = []
        
        for p in self.engine.all_planets:
            if p.name in f_mgr.known_planets and p.owner != faction and p.owner != "Neutral":
                 if not self.ai_manager.is_valid_target(faction, p.owner): continue
                 
                 val = getattr(p, 'income_req', 100)
                 if val > 800 or getattr(p, 'income_prom', 0) > 50:
                      theater = self.ai_manager.get_cached_theater_power(p, faction)
                      enemy_pow = sum(pw for f, pw in theater.items() if f != faction)
                      if enemy_pow < 2000:
                          potential_targets.append(p)
                          
        if not potential_targets: return
        
        target = random.choice(potential_targets)
        
        self.tf_counter += 1
        raid_tf = TaskForce(f"RAID-{self.tf_counter}", faction)
        raid_tf.target = target
        raid_tf.strategy = "RAID"
        raid_tf.composition_type = "RAIDER"
        raid_tf.is_raid = True
        raid_tf.raid_duration = 2
        
        candidates = sorted(available_fleets, key=lambda x: x.power) 
        count = min(len(candidates), random.randint(2, 4))
        
        for i in range(count):
            f = candidates[i]
            raid_tf.add_fleet(f)
            self._fleet_to_tf_map[f.id] = raid_tf
            
        if raid_tf.fleets:
             self.ensure_faction_list(faction)
             self.task_forces[faction].append(raid_tf)
             print(f"  > [RAID] {faction} LAUNCHING DESPERATE RAID on {target.name} (Value: {target.income_req})")
             
             # [PHASE 6] Mission Creation Log
             if logging_config.LOGGING_FEATURES.get('task_force_mission_tracking', False):
                 if hasattr(self.engine, 'logger') and hasattr(self.engine.logger, 'mission'):
                     self.engine.logger.mission(f"[{faction}] MISSION START: Raid on {target.name} (TF: {raid_tf.id})")

    @profile_method
    def concentrate_forces(self, faction: str) -> None:
        """Scans active Task Forces and merges them if they are redundant."""
        self.ensure_faction_list(faction)
        tfs = self.task_forces[faction]
        if len(tfs) < 2: 
            # Still call consolidation for single TFs
            for tf in tfs:
                self.consolidate_task_force_fleets(tf)
            return
        
        tfs.sort(key=lambda x: x.id)
        tfs_to_remove = []
        
        for i in range(len(tfs)):
            tf1 = tfs[i]
            if tf1 in tfs_to_remove: continue
            if tf1.state not in ["TRANSIT", "MUSTERING"]: continue
            
            for j in range(i+1, len(tfs)):
                tf2 = tfs[j]
                if tf2 in tfs_to_remove: continue
                if tf2.state not in ["TRANSIT", "MUSTERING"]: continue
                
                if tf1.target and tf2.target and tf1.target == tf2.target:
                    print(f"  > [STRATEGY] {faction} MERGING {tf2.id} into {tf1.id} for concentrated assault on {tf1.target.name}")
                    for f in tf2.fleets:
                        tf1.add_fleet(f)
                        self._fleet_to_tf_map[f.id] = tf1 # Update Map
                    tfs_to_remove.append(tf2)
                    
        for tf in tfs_to_remove:
            if tf in self.task_forces[faction]:
                self.task_forces[faction].remove(tf)

        # Phase 2: Internal Fleet Consolidation (Merge small fleets into one)
        for tf in self.task_forces[faction]:
            self.consolidate_task_force_fleets(tf)

    def consolidate_task_force_fleets(self, task_force: TaskForce) -> None:
        """Merges fleets within a Task Force if they are at the same location and have room."""
        if len(task_force.fleets) < 2: return
        
        max_size = getattr(self.ai_manager.engine, 'max_fleet_size', 100)
        
        # Group by location
        by_loc = {}
        for f in task_force.fleets:
            if f.is_destroyed: continue
            loc_id = id(f.location)
            if loc_id not in by_loc: by_loc[loc_id] = []
            by_loc[loc_id].append(f)
            
        for loc_id, fleets in by_loc.items():
            if len(fleets) < 2: continue
            
            # Sort by size (merge smaller into larger)
            fleets.sort(key=lambda x: len(x.units), reverse=True)
            
            primary = fleets[0]
            for i in range(1, len(fleets)):
                secondary = fleets[i]
                if (len(primary.units) + len(secondary.units)) <= max_size:
                    print(f"  > [LOGISTICS] {task_force.faction} consolidating fleet {secondary.id} into {primary.id} (Size: {len(primary.units)} + {len(secondary.units)})")
                    primary.merge_with(secondary)
                else:
                    # Maybe try merging into another? For now, just stop or keep as primary for next
                    primary = secondary 

        # Clean up destroyed fleets from Task Force
        task_force.fleets = [f for f in task_force.fleets if not f.is_destroyed]
        
        # Clean up Map (remove destroyed or removed fleets)
        # Iterate keys to find those pointing to this TF but not in fleets list
        # This is expensive O(MapSize). Better: when fleet is destroyed, update map?
        # Or just lazy update here.
        # Allow lazy for now or handle in add/remove. 
        # Adding explicitly:
        # We need to make sure we don't have dangling refs in the map.
        current_ids = set(f.id for f in task_force.fleets)
        keys_to_remove = [k for k, v in self._fleet_to_tf_map.items() if v == task_force and k not in current_ids]
        for k in keys_to_remove:
            del self._fleet_to_tf_map[k]

    def split_overlarge_fleets(self, faction: str, available_fleets: List[Fleet]) -> List[Fleet]:
        """
        If a faction has few fleets but they are very large, split them
        to create more flexible operational groups.
        """
        if not available_fleets:
            return available_fleets
            
        # 1. Decision Parameters
        max_size = getattr(self.engine, 'max_fleet_size', 100)
        
        # If we have < 3 idle fleets, consider splitting the biggest ones
        if len(available_fleets) < 3:
            # Sort by size to split the biggest first
            available_fleets.sort(key=lambda x: len(x.units), reverse=True)
            
            for f in list(available_fleets):
                if f.is_destroyed: continue
                
                # Split threshold: Over 50% of global max size and at least 20 units
                if len(f.units) >= max(20, max_size * 0.5):
                    print(f"  > [LOGISTICS] {faction} splitting overlarge fleet {f.id} (Size: {len(f.units)}) to increase coverage.")
                    new_f = f.split_off(ratio=0.5)
                    if new_f:
                        # Register with engine/manager
                        if hasattr(self.engine, 'add_fleet'):
                            self.engine.add_fleet(new_f)
                        available_fleets.append(new_f)
                        
                        # Only split one per turn per faction to avoid explosion
                        break
                        
        return available_fleets

    def _select_best_reinforcement(self, tf: TaskForce, available_fleets: List[Fleet]) -> Optional[Fleet]:
        """Selects the best fleet from available pool based on TF mission role."""
        if not available_fleets: return None
        
        role = getattr(tf, 'mission_role', 'ASSAULT')
        
        def score_fleet(f: Fleet) -> float:
            matrix = f.get_capability_matrix()
            base_score = f.power
            
            if role == 'INVASION':
                return base_score + (matrix.get("Transport", 0) * 500)
            elif role == 'SCOUT':
                return base_score + (matrix.get("Scout", 0) * 800) + (matrix.get("Escort", 0) * 200)
            elif role == 'ASSAULT':
                return base_score + (matrix.get("Battleship", 0) * 1000) + (matrix.get("Cruiser", 0) * 400)
            elif role == 'DEFENSE':
                return base_score + (matrix.get("Battleship", 0) * 500) + (matrix.get("Cruiser", 0) * 200)
                
            return base_score

        scored = sorted(available_fleets, key=score_fleet, reverse=True)
        return scored[0]

    def log_tf_effectiveness(self, tf: TaskForce):
        """Logs the effectiveness of a Task Force upon completion (Metric #5)."""
        if not hasattr(self.engine, 'telemetry') or not self.engine.telemetry:
            return

        from src.reporting.telemetry import EventCategory
        
        # Calculate achievement score
        achievement_score = (tf.battles_won * 20) + (tf.enemies_destroyed * 5)
        if tf.battles_lost > 0:
            achievement_score /= (tf.battles_lost + 1)
            
        self.engine.telemetry.log_event(
            EventCategory.STRATEGY,
            "task_force_effectiveness",
            {
                "faction": tf.faction,
                "tf_id": tf.id,
                "turn": self.engine.turn_counter,
                "turns_active": tf.turns_active,
                "battles_won": tf.battles_won,
                "battles_lost": tf.battles_lost,
                "enemies_destroyed": tf.enemies_destroyed,
                "achievement_score": achievement_score,
                "composition": tf.composition_type
            },
            turn=self.engine.turn_counter,
            faction=tf.faction
        )

        # [PHASE 6] Mission Complete Log
        if logging_config.LOGGING_FEATURES.get('task_force_mission_tracking', False):
            if hasattr(self.engine, 'logger') and hasattr(self.engine.logger, 'mission'):
                self.engine.logger.mission(f"[{tf.faction}] MISSION COMPLETE: TF {tf.id} (Score: {achievement_score:.1f})")

    @profile_method
    def form_construction_task_force(self, faction: str, available_fleets: List[Fleet]) -> None:
        """
        Forms a task force to build a Deep Space Station at a strategic choke point.
        """
        if not available_fleets: return
        
        # 1. Identify detailed requirements (rich/defensive faction?)
        f_mgr = self.engine.factions[faction]
        if f_mgr.requisition < 5000: return # Save money for ships first
        
        # 2. Find Choke Points (Border Systems)
        # We need the Theater Manager for this
        if not hasattr(self.ai_manager.planner, 'theater_manager'): return
        
        tm = self.ai_manager.planner.theater_manager
        # Ensure theaters are analyzed
        if not tm.theaters:
            tm.analyze_theaters(faction)
            
        targets = []
        for t in tm.theaters.values():
            if not hasattr(t, 'border_systems'): continue
            for sys_name in t.border_systems:
                sys = tm._get_system_by_name(sys_name)
                if not sys: continue
                
                # Check if we already have a Starbase there
                has_sb = False
                for sb in sys.starbases:
                    if sb.faction == faction and sb.is_alive():
                        has_sb = True
                        break
                
                if has_sb: continue
                
                # Check if we already have a TF assigned there
                is_assigned = False
                for tf in self.task_forces[faction]:
                    if tf.target and getattr(tf.target, 'system', None) == sys:
                        is_assigned = True
                        break
                    # Also check for nodes
                    if tf.target and hasattr(tf.target, 'type') and tf.target.type in ["FluxPoint", "Portal"] and getattr(tf.target, 'system', None) == sys:
                        is_assigned = True
                        break
                        
                if is_assigned: continue
                
                # Valid Target!
                targets.append(sys)
        
        if not targets: return
        
        # Pick one
        target_sys = random.choice(targets)
        
        # Select specific node (Primary Node usually)
        target_node = target_sys.get_primary_node()
        if not target_node: return

        # Form TF
        # Prefer smaller fleets (Escorts/Frigates) as they are cheaper to tie up
        candidates = sorted(available_fleets, key=lambda f: f.power)
        fleet = candidates[0]
        
        self.tf_counter += 1
        tf = TaskForce(f"CONST-{self.tf_counter}", faction)
        tf.target = target_node
        tf.strategy = "CONSTRUCT"
        tf.mission_role = "CONSTRUCTION"
        tf.composition_type = "ENGINEER"
        tf.add_fleet(fleet)
        self._fleet_to_tf_map[fleet.id] = tf
        
        self.ensure_faction_list(faction)
        self.task_forces[faction].append(tf)
        
        # Remove from available
        available_fleets.remove(fleet)
        
        print(f"  > [STRATEGY] {faction} dispatching CONSTRUCTION fleet to {target_sys.name}")

