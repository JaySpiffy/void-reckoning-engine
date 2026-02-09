from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional

@dataclass
class Theater:
    id: str
    name: str
    system_names: Set[str] = field(default_factory=set)  # Owned + Frontier systems
    core_systems: Set[str] = field(default_factory=set)  # Owned systems only
    fleet_ids: List[str] = field(default_factory=list)
    threat_score: float = 0.0
    strategic_value: float = 0.0
    assigned_goal: str = "DEFEND"  # DEFEND, ATTACK, EXPAND
    doctrine: str = "BALANCED"    # [Phase 5] BLITZ, SIEGE, FORTIFY, etc.

class TheaterManager:
    def __init__(self, context):
        self.context = context  # SimulationEngine reference
        self.theaters: Dict[str, Theater] = {}  # {theater_id: Theater}

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'context' in state: del state['context']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.context = None

    def analyze_theaters(self, faction: str) -> List[Theater]:
        """
        Groups owned systems into theaters based on connectivity.
        """
        # 1. Identify Owned Systems
        owned_planets = self.context.planets_by_faction.get(faction, [])
        owned_system_names = set(p.system.name for p in owned_planets if p.system)
        
        if not owned_system_names:
            return []

        # 2. Build Adjacency Graph for Owned Systems
        # We need to know which owned systems are connected to which.
        # Use BFS/Flood Fill to find connected components.
        
        clusters = []
        visited = set()
        
        sorted_systems = sorted(list(owned_system_names)) # Deterministic order
        
        for sys_name in sorted_systems:
            if sys_name in visited:
                continue
                
            # Start new cluster
            current_cluster = set()
            queue = [sys_name]
            visited.add(sys_name)
            
            while queue:
                curr = queue.pop(0)
                current_cluster.add(curr)
                
                # Find neighbors
                # We need the System object to access connections
                sys_obj = self._get_system_by_name(curr)
                if sys_obj:
                    for neighbor_sys in sys_obj.connections:
                        n_name = neighbor_sys.name
                        if n_name in owned_system_names and n_name not in visited:
                            visited.add(n_name)
                            queue.append(n_name)
            
            clusters.append(current_cluster)
            
        # 3. Create Theaters from Clusters (including Frontier)
        new_theaters = []
        
        for i, cluster in enumerate(clusters):
            t_id = f"THEATER-{faction}-{i}"
            theater = Theater(
                id=t_id, 
                name=f"Theater {i+1}", 
                core_systems=cluster,
                system_names=cluster.copy()
            )
            
            # Add Frontier (Neighbors of Core)
            for core_sys_name in cluster:
                sys_obj = self._get_system_by_name(core_sys_name)
                if sys_obj:
                    for neighbor in sys_obj.connections:
                        theater.system_names.add(neighbor.name)
            
            # Calculate Metrics
            self._analyze_threats(theater, faction)
            new_theaters.append(theater)
            
        # 4. Merge/Update Global Theater List
        # First, remove old theaters for this faction
        keys_to_remove = [k for k in self.theaters if k.startswith(f"THEATER-{faction}-")]
        for k in keys_to_remove:
            del self.theaters[k]
            
        # Add new theaters
        for t in new_theaters:
            self.theaters[t.id] = t
            
        return new_theaters

    def assign_fleets_to_theaters(self, faction: str, fleets: List['Fleet']):
        """
        Assigns fleets to the theater containing their current location.
        """
        # Clear previous assignments
        for t in self.theaters.values():
            t.fleet_ids.clear()
            
        for f in fleets:
            if f.faction != faction: continue
            
            loc_name = f.location.name if hasattr(f.location, 'name') else str(f.location)
            
            # Find matching theater
            assigned = False
            for t in self.theaters.values():
                if loc_name in t.system_names:
                    t.fleet_ids.append(f.id)
                    f.metadata["assigned_theater"] = t.id
                    assigned = True
                    break
            
            # If in deep space or unknown, assign to nearest (TODO)
            if not assigned:
                # Default to Theater 0
                if self.theaters:
                    first_t = list(self.theaters.values())[0]
                    first_t.fleet_ids.append(f.id)
                    f.metadata["assigned_theater"] = first_t.id

    def _get_system_by_name(self, name: str):
        # Linear search for now (simulation usually has <100 systems)
        # Optimization: Build a lookup dict in SimulationEngine
        if hasattr(self.context, 'systems'):
             for s in self.context.systems:
                 if s.name == name: return s
        return None

    def _analyze_threats(self, theater: Theater, faction: str):
        """
        Calculates threat level based on enemy fleets in theater systems.
        """
        threat = 0.0
        
        # This is expensive if we iterate all fleets vs all systems.
        # Better: Iterate all enemy fleets and check if they are in theater.system_names
        
        enemy_fleets = [f for f in self.context.fleets if f.faction != faction and f.faction != "Neutral"]
        
        for f in enemy_fleets:
            loc_name = f.location.name if hasattr(f.location, 'name') else str(f.location)
            if loc_name in theater.system_names:
                threat += f.power
                
        theater.threat_score = threat
        
        # Determine Goal
        if threat > 5000: # Arbitrary threshold
            theater.assigned_goal = "DEFEND"
        elif threat > 0:
            theater.assigned_goal = "ATTACK" # Clear the border
        else:
            theater.assigned_goal = "EXPAND" # Capture neutral or empty

    def _analyze_choke_points(self, theater: Theater):
        """Identifies systems that are critical bottlenecks (Border Systems)."""
        # A system is a choke point/frontline if it connects to a system NOT in the theater.
        # We need to iterate all systems in the theater and check their neighbors.
        
        theater_systems = theater.system_names
        border_systems = set()
        
        for sys_name in theater_systems:
            sys_obj = self._get_system_by_name(sys_name)
            if not sys_obj: continue
            
            is_border = False
            for neighbor in sys_obj.connections:
                if neighbor.name not in theater_systems:
                    is_border = True
                    break
            
            if is_border:
                border_systems.add(sys_name)
                
        # Store metadata (Theater class needs a field for this really, using metadata if available or just logging)
        # For now, let's assume Theater has no 'choke_points' field unless we add it. 
        # But we can assume 'systems' are generic.
        # Let's add it dynamically to the object instance.
        theater.border_systems = border_systems
        
        # If a system is a border and has > 3 external connections, it's a "Hot Gate"
        # If it has 1 external connection, it's a "Backdoor"

        
    def assign_theater_doctrine(self, faction: str, theater: Theater, personality: 'FactionPersonality'):
        """
        Assigns a strategic doctrine to the theater based on personality and situation.
        """
        # 1. Calculate Situation Metrics
        threat_ratio = theater.threat_score / max(1, sum(f.power for f in self.context.fleets if f.id in theater.fleet_ids))
        
        # 2. Determine Doctrine
        if threat_ratio > 2.0:
            # Overwhelming enemy
            if "DEFENSIVE" in personality.strategic_doctrine or "DEFENSIVE" in str(personality.combat_doctrine):
                theater.assigned_goal = "DEFEND"
                theater.doctrine = "FORTIFY"
            else:
                theater.assigned_goal = "DEFEND"
                theater.doctrine = "RETREAT"
                
        elif threat_ratio > 1.0:
            # Even match / Slight disadvantage
            if "AGGRESSIVE" in personality.strategic_doctrine or "AGGRESSIVE" in str(personality.combat_doctrine):
                theater.assigned_goal = "ATTACK"
                theater.doctrine = "SIEGE"
            else:
                theater.assigned_goal = "DEFEND"
                theater.doctrine = "HOLD_LINE"
                
        else:
            # Advantage
            if "AGGRESSIVE" in personality.strategic_doctrine or "AGGRESSIVE" in str(personality.combat_doctrine):
                theater.assigned_goal = "ATTACK"
                theater.doctrine = "BLITZ"
            else:
                theater.assigned_goal = "EXPAND"
                theater.doctrine = "METHODICAL"
                
        # 3. Store Doctrine in metadata (if we had a field, but assigned_goal works for now)
        # We might want a dedicated field later.
        
    def calculate_strategic_value(self, theater: Theater):
        """Sum of economic value of systems in theater."""
        val = 0.0
        for sys_name in theater.core_systems:
            sys_obj = self._get_system_by_name(sys_name)
            if sys_obj:
                for p in sys_obj.planets:
                    val += p.income_req
        theater.strategic_value = val
