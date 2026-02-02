import random
from typing import Optional, Any
from src.utils.profiler import profile_method

_ai_rng = random.Random()

def init_ai_rng(seed: Optional[int] = None):
    """Initializes the AI RNG with a specific seed."""
    _ai_rng.seed(seed)

from src.ai.strategies.base import FactionAIStrategy
from src.core.constants import COLONIZATION_REQ_COST

class StandardStrategy(FactionAIStrategy):
    """
    Default implementation of AI logic.
    Uses FactionPersonality data to tune behavior.
    """
    
    @profile_method
    def choose_target(self, fleet: Any, engine: Any) -> Optional[Any]:
        """Decides the next target for a fleet (Extracted from CampaignManager)."""
        
        # 0. Economic & Tactical Check
        f_mgr = engine.factions.get(fleet.faction)
        if not f_mgr: return None

        # [NEW] CONSTRUCTOR TASKING
        is_constructor_fleet = any(getattr(u, 'unit_class', '') == 'constructor' for u in fleet.units)
        if is_constructor_fleet:
            # 1. Prioritize Starbases under construction
            for sb_fleet in engine.fleets:
                if sb_fleet.faction == fleet.faction and not sb_fleet.is_destroyed:
                    if any(getattr(u, 'unit_class', '') == 'Starbase' and getattr(u, 'is_under_construction', False) for u in sb_fleet.units):
                        # Move to support the construction
                        if sb_fleet.location != fleet.location:
                             return sb_fleet.location
            
            # 2. If already at construction site, stay there!
            at_site = False
            for u in fleet.units:
                 # Check if we are already at a site with a construction project
                 for other_f in engine.fleets:
                     if other_f.location == fleet.location and other_f.faction == fleet.faction:
                          if any(getattr(unit, 'unit_class', '') == 'Starbase' and getattr(unit, 'is_under_construction', False) for unit in other_f.units):
                               at_site = True
                               break
            if at_site: return None # Stay put

            # 2.5 [NEW] Strategic Construction Projects
            # If wealthy, expand infrastructure to specialized nodes
            if f_mgr.requisition > 3000:
                valid_targets = []
                # Scan known systems (via known planets)
                known_planet_names = set(f_mgr.known_planets)
                known_systems = set()
                
                # Resolve systems from known planets
                # Resolve systems from known planets
                for p in engine.all_planets:
                    if p.name in known_planet_names and hasattr(p, 'node_reference'):
                        sys = p.node_reference.metadata.get("system")
                        if sys: known_systems.add(sys)
                
                # print(f"DEBUG: {fleet.faction} Constructor scanning {len(known_systems)} systems for targets.")
                for sys in known_systems:
                     for node in sys.nodes:
                         if node.type in ["AsteroidField", "Nebula", "FluxPoint"]:
                             # Check if occupied by ANY structure
                             is_occupied = False
                             # Optimization: Use fleet location map if available, else loop
                             for f in engine.fleets:
                                 if f.location == node and not f.is_destroyed:
                                      # Check for any static structure
                                      if any(getattr(u, 'unit_class', '') in ['Starbase', 'MiningStation', 'ResearchOutpost', 'ListeningPost'] for u in f.units):
                                          is_occupied = True
                                          break
                             
                             if not is_occupied:
                                  valid_targets.append(node)
                
                if valid_targets:
                     # Prioritize closest
                     target = min(valid_targets, key=lambda n: engine.intel_manager.calculate_distance(fleet.location.name, n.name))
                     print(f"DEBUG: {fleet.faction} Constructor selected {target.name} ({target.type})")
                     return target

            # 3. Fallback: Return to a safe shipyard for protection
            home_planets = engine.planets_by_faction.get(fleet.faction, [])
            if home_planets: return _ai_rng.choice(home_planets)
            return None

        # CurrentLocation Assessment
        theater_stats = engine.intel_manager.get_theater_power(fleet.location.name, engine.turn_counter)
        my_side_power = sum(p for f, p in theater_stats.items() if f == fleet.faction)
        enemy_power = sum(p for f, p in theater_stats.items() if f != fleet.faction)

        # EMERGENCY RETREAT
        if enemy_power > my_side_power * 2.0:
            home_planets = engine.planets_by_faction.get(fleet.faction, [])
            if home_planets:
                print(f"  > [RETREAT] {fleet.faction} Fleet {fleet.id} RETREATING from overwhelming odds! ({my_side_power} vs {enemy_power})")
                return _ai_rng.choice(home_planets)

        if f_mgr.requisition < 0:
            # Bankrupt: Defensive retreat
            home_planets = engine.planets_by_faction.get(fleet.faction, [])
            if home_planets: return _ai_rng.choice(home_planets)
            return None

        # 1. Selection Context (Search Neighbors + Known Planets)
        nearby = []
        if hasattr(fleet.location, 'system'):
            nearby.extend(fleet.location.system.planets)
            for s in fleet.location.system.connections:
                nearby.extend(s.planets)
        else:
            nearby = [p for p in engine.all_planets if p.name in f_mgr.known_planets]

        # Categorize Target Candidates (Helper)
        def is_safe(planet):
            # 1. Use Intelligence Memory first
            intel = engine.intel_manager.get_cached_intel(fleet.faction, planet.name, engine.turn_counter)
            
            # [TUNING] Dynamic Threat Tolerance based on Personality and Target Type
            # Expansionist factions (high aggression/expansion) are willing to take more risks.
            aggression = getattr(f_mgr, 'aggression', 1.0)
            expansion = getattr(f_mgr, 'expansion_bias', 0.8)
            
            # Base tolerance is 1.2. High aggression increases it.
            # e.g., Aggression 2.0 -> Tolerance 1.4
            tolerance = 1.0 + (aggression * 0.2)
            
            # If the planet is Neutral, we are even more willing to risk it (Colonization urgency)
            if planet.owner == "Neutral":
                tolerance *= 1.5 # 1.2 * 1.5 = 1.8
            
            if intel and intel[0] > 0: # Check if last_seen_turn > 0
                start_turn = intel[0]
                if engine.turn_counter - start_turn < 4:
                     return intel[3] < tolerance # threat

            # 2. Fallback: If visible, use accurate threat
            if planet.name in f_mgr.visible_planets:
                return engine.intel_manager.calculate_threat_level(planet.name, fleet.faction, engine.turn_counter) < tolerance

            # 3. Completely Unknown (Fog of War)
            if getattr(fleet, 'is_scout', False): return True
            
            # [INTEL] Use cached intel for "real" threat estimation (simulating memory)
            cached_threat = intel[3]
            
            # If we have NO intel (never seen), assume it's risky but explorable
            if intel[0] == 0: return True 
            
            return (cached_threat * 1.3) < tolerance

        candidates = [p for p in nearby if p.name in f_mgr.known_planets or (hasattr(fleet.location, 'system') and p in nearby)]
        safe_targets = []
        for p in candidates:
            try:
                if is_safe(p):
                    safe_targets.append(p)
            except Exception as e:
                print(f"CRASH in is_safe({p.name}): {e}")
                continue
        
        # Desperation Fallback
        if not safe_targets and f_mgr.requisition < 500:
             safe_targets = candidates 

        if not safe_targets:
            safe_targets = engine.planets_by_faction.get(fleet.faction, []) # Fallback to home
        else:
            # Sort by Full Weighted Score
            scored_candidates = []
            home_node = fleet.location.system if hasattr(fleet.location, 'system') else fleet.location
            strat_plan = f_mgr.active_strategic_plan
            
            # Prepare scoring args
            s_priority = tuple(strat_plan.priority_planets) if strat_plan else ()
            s_targets = tuple(strat_plan.target_systems) if strat_plan else ()
            s_fact = strat_plan.target_faction if strat_plan else ""
            s_phase = strat_plan.current_phase if strat_plan else ""
            h_x = home_node.x if hasattr(home_node, 'x') else 0
            h_y = home_node.y if hasattr(home_node, 'y') else 0

            for p in safe_targets:
                try:
                    val = engine.intel_manager.calculate_target_score(
                        p.name, fleet.faction, h_x, h_y,
                        s_priority, s_targets, s_fact, s_phase,
                        engine.turn_counter
                    )
                    scored_candidates.append((p, val))
                except Exception as e:
                    print(f"CRASH in calculate_target_score: {e}")
                    continue

            # Weighted Selection
            total_score = sum(s for p, s in scored_candidates)
            pick_val = _ai_rng.uniform(0, total_score)
            current = 0
            for p, s in scored_candidates:
                current += s
                if current >= pick_val:
                    return p
            return scored_candidates[0][0] if scored_candidates else None
            
        # Priority Logic (Interception, Defense, Aggression)
        
        # A. STRATEGIC INTERCEPTION
        # A. STRATEGIC INTERCEPTION (Optimized)
        current_visible_threats = []
        
        # Resolve my coords
        mx, my = 0, 0
        node = getattr(fleet, 'current_node', None)
        if node and hasattr(node, 'x'): mx, my = node.x, node.y
        elif hasattr(fleet.location, 'x'): mx, my = fleet.location.x, fleet.location.y
        elif hasattr(fleet.location, 'system'): mx, my = fleet.location.system.x, fleet.location.system.y
        
        # Spatial Query (Radius 300 - Threat Detection Range)
        if hasattr(engine, 'spatial_index_fleets'):
            candidates = engine.spatial_index_fleets.query_radius(mx, my, 300)
            for enemy_f in candidates:
                if enemy_f.faction != fleet.faction and not enemy_f.is_destroyed:
                     loc_name = getattr(enemy_f.location, 'name', None)
                     # Only if visible OR close enough to be detected by sensors
                     if loc_name and (loc_name in f_mgr.visible_planets or getattr(enemy_f, 'stealth_rating', 0) < scanner_range):
                         current_visible_threats.append(enemy_f)
        else:
            # Fallback Legacy Loop
            for enemy_f in engine.fleets:
                if enemy_f.faction != fleet.faction and not enemy_f.is_destroyed:
                    loc_name = getattr(enemy_f.location, 'name', None)
                    if loc_name and loc_name in f_mgr.visible_planets:
                         current_visible_threats.append(enemy_f)
        
        if current_visible_threats and engine.diplomacy:
            current_visible_threats = [f for f in current_visible_threats if engine.intel_manager._is_hostile_target(fleet.faction, f.faction)]
            
        if current_visible_threats:
            return current_visible_threats[0].location
            
        # B. DEFEND
        nearby_threatened = [p for p in safe_targets if p.owner == fleet.faction and p.name in f_mgr.visible_planets and any(ag.faction != fleet.faction for ag in p.armies if not ag.is_destroyed)]
        if nearby_threatened: return _ai_rng.choice(nearby_threatened)
        
        # C. WAR PRIORITY
        nearby_enemies = [p for p in safe_targets 
                          if p.owner not in [fleet.faction, "Neutral"] 
                          and p.name in f_mgr.known_planets
                          and engine.intel_manager._is_hostile_target(fleet.faction, p.owner)]
                          
        aggression_bias = 0.7 if fleet.faction in ["Hegemony", "Tau_Empire", "Aaether-kini"] else 0.3
        if nearby_enemies and _ai_rng.random() > aggression_bias:
             target = max(nearby_enemies, key=lambda p: getattr(p, 'income_req', 0))
             print(f"  > [ORDER] {fleet.faction} Fleet {fleet.id} attacking HOSTILE {target.name} (Aggression)")
             return target
             
        # D. LOCAL EXPANSION
        col_cost = engine.game_config.get("economy", {}).get("colonization_cost", COLONIZATION_REQ_COST)
        can_colonize = f_mgr.requisition >= col_cost
        nearby_neutrals = [p for p in safe_targets if p.owner == "Neutral" and p.name in f_mgr.known_planets and can_colonize]
        if nearby_neutrals:
             target = max(nearby_neutrals, key=lambda p: getattr(p, 'income_req', 0))
             return target
             
        # E. SCOUTING
        unknown_neighbors = [p for p in nearby if p.name not in f_mgr.known_planets]
        if unknown_neighbors: return _ai_rng.choice(unknown_neighbors)
        
        # F. BLIND EXPLORATION
        current_node = getattr(fleet, "current_node", None)
        if current_node and hasattr(fleet.location, 'system'):
             system_nodes = fleet.location.system.nodes
             if system_nodes:
                 target_node = _ai_rng.choice(system_nodes)
                 print(f"  > [SCOUT] {fleet.faction} Fleet {fleet.id} scouting Sector {target_node.id} (Exploration)")
                 return target_node
                 
        return _ai_rng.choice(engine.planets_by_faction.get(fleet.faction, [fleet.location]))

    def process_reinforcements(self, faction: str, engine: Any) -> None:
        """Handles logistics and army transport logic (Extracted from CampaignManager)."""
        faction_fleets = [f for f in engine.fleets if f.faction == faction and not f.is_destroyed]
        my_planets = engine.planets_by_faction.get(faction, [])
        threatened = [p for p in my_planets if any(ag.faction != faction for ag in p.armies if not ag.is_destroyed)]
        
        for fleet in faction_fleets:
            if fleet.is_destroyed: continue
            
            # Pickup reinforcements
            if fleet.used_capacity < fleet.transport_capacity:
                loc = fleet.location
                planet = loc if hasattr(loc, 'owner') else None
                if hasattr(loc, 'metadata'): planet = loc.metadata.get("object")
                
                if planet and planet.owner == faction and planet not in threatened:
                     if hasattr(loc, 'armies'):
                         for ag in list(loc.armies):
                             if ag.faction == faction and ag.state == "IDLE" and not ag.is_destroyed:
                                 if fleet.can_transport(ag):
                                     engine.battle_manager.embark_army(fleet, ag)
                                 else:
                                     # Partial Load
                                     space = fleet.transport_capacity - fleet.used_capacity
                                     detachment = ag.split_off(space)
                                     if detachment:
                                         loc.armies.append(detachment)
                                         engine.battle_manager.embark_army(fleet, detachment)
            
            # Logistics Diversion (Pickup)
            if fleet.transport_capacity > 0 and fleet.destination is None and (fleet.used_capacity / fleet.transport_capacity) < 0.5:
                # Scan for friendly planets with IDLE armies
                best_target = None
                for p in my_planets:
                    if p == fleet.location: continue
                    if p in threatened: continue
                    
                    has_idle_army = any(ag.state == "IDLE" and ag.faction == faction for ag in p.armies)
                    if has_idle_army:
                        best_target = p
                        break
                
                if best_target:
                    print(f"  > [LOGISTICS] Fleet {fleet.id} diverting to {best_target.name} to pickup troops.")
                    fleet.move_to(best_target, turn=engine.turn_counter, engine=engine)
            
            # Logistics Diversion (Dropoff)
            elif fleet.cargo_armies and fleet.destination is None:
                if threatened:
                    # Move to nearest threatened planet to drop off
                    best_drop = min(threatened, key=lambda p: engine.intel_manager.calculate_distance(getattr(fleet.location, 'name', 'Unknown'), p.name))
                    print(f"  > [LOGISTICS] Fleet {fleet.id} diverting to {best_drop.name} to drop off reinforcements.")
                    fleet.move_to(best_drop, turn=engine.turn_counter, engine=engine)
