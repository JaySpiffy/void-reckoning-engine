
import functools
from collections import deque
from typing import Any, Dict, List, Set, Tuple, Optional, TYPE_CHECKING
from src.reporting.telemetry import EventCategory
from src.config import logging_config


from src.utils.profiler import profile_method

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine

class IntelligenceManager:
    """
    Manages Intelligence, Fog of War, Visibility, and Threat Assessment.
    Operates on the CampaignEngine state.
    """
    def __init__(self, engine: 'CampaignEngine') -> None:
        self.engine = engine
        self._visibility_cache = {} # turn_id -> faction -> set(planet_names)
        self._cached_turn = -1

    def calculate_distance(self, start_name: str, end_name: str) -> float:
        """Calculates Euclidean distance between two planets."""
        p1 = self.engine.get_planet(start_name)
        p2 = self.engine.get_planet(end_name)
        if not p1 or not p2:
            return 1000.0
            
        x1 = p1.system.x if hasattr(p1, 'system') else 0
        y1 = p1.system.y if hasattr(p1, 'system') else 0
        x2 = p2.system.x if hasattr(p2, 'system') else 0
        y2 = p2.system.y if hasattr(p2, 'system') else 0
        
        return ((x1 - x2)**2 + (y1 - y2)**2)**0.5

    def _get_visibility_cache(self):
        """Internal helper for CacheManager registration."""
        return self._visibility_cache

    def clear_visibility_cache(self):
        """Clears the turn-based visibility cache and LRU intelligence caches."""
        self._visibility_cache = {}
        self._cached_turn = -1
        
        # Invalidate LRU caches to prevent stale data (Comment 3)
        self.calculate_threat_level.cache_clear()
        self.get_cached_intel.cache_clear()
        self.calculate_target_score.cache_clear()
        self.get_theater_power.cache_clear()

    @functools.lru_cache(maxsize=1024)
    @profile_method('targeting_time')
    def get_theater_power(self, location_name: str, turn: int, viewer_faction: str = None) -> Dict[str, int]:
        """
        Calculates total power for each faction at a given location.
        If viewer_faction is provided, respects Fog of War.
        Returns: {FactionName: TotalPower}
        """
        location = self.engine.get_planet(location_name)
        if not location: return {}

        # Fog of War Check
        if viewer_faction:
            f_obj = self.engine.get_faction(viewer_faction)
            if f_obj and location_name not in getattr(f_obj, 'visible_planets', set()):
                # Viewer cannot see this location; return empty or last known intel?
                # For this method, we return empty as it represents "Active Scan".
                return {}
        
        powers: Dict[str, int] = {}
        # Fleets
        orbit_node = getattr(location, 'node_reference', None)
        for f in self.engine.fleets:
            if f.is_destroyed: continue
            
            # Check if fleet is AT the planet or IN ORBIT of the planet
            is_here = (f.location == location)
            if not is_here and orbit_node and f.location == orbit_node:
                is_here = True
                
            if is_here:
                powers[f.faction] = powers.get(f.faction, 0) + f.power
        
        # Planet Garrison / Armies
        if hasattr(location, 'armies'):
            for ag in location.armies:
                if not ag.is_destroyed:
                    powers[ag.faction] = powers.get(ag.faction, 0) + ag.power
        
        # Planet base defense (Natural fortifications)
        if hasattr(location, 'defense_level') and location.owner != "Neutral":
             # [TUNING] Lowered base defense multiplier to 250 (from 500) to reduce early-game paralysis
             powers[location.owner] = powers.get(location.owner, 0) + (location.defense_level * 250)
        
        return powers
        
    def _is_hostile_target(self, faction: str, target_owner: str) -> bool:
        """Diplomatic check: valid offensive target if at war."""
        if not hasattr(self.engine, 'diplomacy') or not self.engine.diplomacy:
            return True
        treaty = self.engine.diplomacy.treaties.get(faction, {}).get(target_owner, "Peace")
        return treaty == "War"

    @functools.lru_cache(maxsize=1024)
    @profile_method('threat_calc_time')
    def calculate_threat_level(self, location_name: str, faction: str, turn: int = 0) -> float:
        """Calculates threat score. respects visibility if called for self-assessment."""
        location = next((p for p in self.engine.all_planets if p.name == location_name), None)
        if not location:
            return 0.5

        # Assessing threat as 'faction' at 'location_name'
        theater_stats = self.get_theater_power(location_name, turn, viewer_faction=faction)
        
        # If we can't see the theater, threat is indeterminate (0.5) 
        # unless we have intel memory (handled at a higher level)
        if not theater_stats:
            return 0.5

        my_power = sum(p for f, p in theater_stats.items() if f == faction)
        enemy_power = sum(p for f, p in theater_stats.items() if f != faction and f != "Neutral")
        
        if my_power == 0: return 10.0 if enemy_power > 0 else 0.5
        return enemy_power / my_power

    def get_intelligence_report(self, faction_name: str, planet_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves intelligence record for a planet."""
        faction = self.engine.get_faction(faction_name)
        if not faction: return None
        return faction.intelligence_memory.get(planet_name)

    @functools.lru_cache(maxsize=512)
    def get_cached_intel(self, faction: str, planet_name: str, turn: int) -> Tuple[int, int, int, float, str]:
        """
        Cached intelligence lookup returning immutable tuple.
        Returns: (last_seen_turn, strength, income, threat, last_owner)
        """
        f_mgr = self.engine.get_faction(faction)
        if not f_mgr: return (0, 0, 0, 0.0, "Neutral")
        
        record = f_mgr.intelligence_memory.get(planet_name, {})
        last_seen = record.get('last_seen_turn', 0)
        threat = record.get('threat', 0.0)
        
        # [QUIRK] Intelligence Decay (from CampaignEngine)
        if turn - last_seen > 5:
             threat *= 0.5
             
        return (
            last_seen,
            record.get('strength', 0),
            record.get('income', 0),
            threat,
            record.get('last_owner', 'Neutral')
        )

    @profile_method('visibility_time')
    def update_faction_visibility(self, f_name: str, force_refresh: bool = False) -> None:
        """Calculates current visibility and updates intelligence memory."""
        faction = self.engine.factions.get(f_name)
        if not faction: return
        
        # Turn-based isolation
        if self.engine.turn_counter != self._cached_turn:
            self.clear_visibility_cache()
            self._cached_turn = self.engine.turn_counter
            
        if not force_refresh and f_name in self._visibility_cache:
            faction.visible_planets = self._visibility_cache[f_name]
            return

        new_visible_planets = set()
        
        # 1. Base Visibility: Owned Planets
        my_planets = self.engine.planets_by_faction.get(f_name, [])
        for p in my_planets:
            new_visible_planets.add(p.name)

        # 2. Fleet Visibility
        my_fleets = [f for f in self.engine.fleets if f.faction == f_name and not f.is_destroyed]
        scanned_nodes_this_pass = set()

        for fleet in my_fleets:
            scan_node = getattr(fleet, "current_node", None)
            if not scan_node:
                loc = fleet.location
                if hasattr(loc, "node_reference"):
                    scan_node = loc.node_reference
                elif hasattr(loc, "edges"): 
                    scan_node = loc
            
            if not scan_node:
                if hasattr(fleet.location, "system"):
                   new_visible_planets.add(fleet.location.name)
                continue
            
            scan_radius = getattr(fleet, "scanning_range", 3)
            if getattr(fleet, "is_scout", False):
                scan_radius += 2
            
            # Listening Post Benefit
            if any(getattr(u, 'unit_class', '') == 'ListeningPost' for u in fleet.units):
                scan_radius = max(scan_radius, 5) # Sets base range to 5

            if (scan_node.id, scan_radius) in scanned_nodes_this_pass:
                continue

            scanned_nodes_this_pass.add((scan_node.id, scan_radius))

            queue = deque([(scan_node, 0)]) 
            visited = {scan_node.id}

            while queue: 
                curr, dist = queue.popleft()

                p_obj = curr.metadata.get("object")
                if p_obj and hasattr(p_obj, "name"):
                     new_visible_planets.add(p_obj.name)
                     if hasattr(p_obj, "system"):
                         faction.explored_systems.add(p_obj.system.name)

                if dist < scan_radius:
                    for edge in curr.edges:
                        neighbor = edge.target
                        new_dist = dist + edge.distance

                        if neighbor.id not in visited and new_dist <= scan_radius:
                            visited.add(neighbor.id)
                            queue.append((neighbor, new_dist))

        # 3. Discovery Update
        faction.visible_planets = new_visible_planets
        self._visibility_cache[f_name] = new_visible_planets

        current_turn = self.engine.turn_counter

        # Accumulate knowledge
        for p_name in sorted(new_visible_planets):
            if p_name not in faction.known_planets:
                if self.engine.logger:
                    self.engine.logger.campaign(f"[DISCOVERY] {f_name} discovered system {p_name}")
            faction.known_planets.add(p_name)

            p = self.engine.get_planet(p_name)
            if p:
                if p.owner != "Neutral" and p.owner != f_name and p.owner not in faction.known_factions:
                    if self.engine.logger:
                        self.engine.logger.campaign(f"[CONTACT] {f_name} made FIRST CONTACT with {p.owner} at {p.name}!")
                    faction.known_factions.add(p.owner)

                record = faction.intelligence_memory.get(p_name, {})
                record['last_seen_turn'] = current_turn
                record['last_owner'] = p.owner

                record['income'] = getattr(p, 'income_req', 0)
                # theater = self.get_theater_power(p, f_name) # Unused call
                record['threat'] = self.calculate_threat_level(p.name, f_name, current_turn)

                faction.intelligence_memory[p_name] = record

        # Fleet Intel Tracking
        for f in self.engine.fleets:
            if f.is_destroyed: continue
            if f.faction == f_name: continue 

            loc_name = getattr(f.location, 'name', None)
            if loc_name and loc_name in new_visible_planets:
                 intel_entry = {
                     "id": f.id,
                     "faction": f.faction,
                     "location": loc_name,
                     "power": f.power,
                     "last_seen_turn": current_turn
                 }
                 faction.fleet_intel[f.id] = intel_entry

    @functools.lru_cache(maxsize=1024)
    @profile_method
    def calculate_target_score(self, planet_name: str, faction: str, 
                               home_x: float, home_y: float,
                               strat_priority: tuple, strat_targets: tuple, 
                               strat_target_faction: str, strat_phase: str,
                               turn: int) -> float:
        """Calculates a weighted score for a planet as a target, with caching."""
        planet = self.engine.get_planet(planet_name)
        if not planet: return 0.0
        
        val = getattr(planet, 'income_req', 100)
        
        is_capital = "Capital" in [n.type for n in getattr(planet, 'provinces', [])]
        if is_capital: val *= 5.0 
        
        connections = len(planet.system.connections) if hasattr(planet, 'system') and hasattr(planet.system, 'connections') else 3
        if connections <= 2: val *= 1.5 
        # Promethium check removed 
        
        px = planet.system.x if hasattr(planet, 'system') else 0
        py = planet.system.y if hasattr(planet, 'system') else 0
        
        d = ((home_x - px)**2 + (home_y - py)**2)**0.5
        d = max(10, d)
        dist_factor = 100.0 / d
        val *= dist_factor
        
        if planet_name in strat_priority: val *= 2.0
        if planet_name in strat_targets: val *= 1.5
        if strat_target_faction and planet.owner == strat_target_faction: val *= 1.3
        
        if strat_phase == "CONSOLIDATION" and d > 300: val *= 0.5
        
        threat = 0
        intel = self.get_cached_intel(faction, planet_name, turn)
        last_seen = intel[0]
        if turn - last_seen < 5:
            threat = intel[3]
        else:
            threat = self.calculate_threat_level(planet_name, faction, turn) # Fix: passed string
            
        val *= (1.0 / max(0.5, threat))
        
        return val

    def attempt_blueprint_theft(self, faction_name: str, target_faction: str, target_location: Any, engine: 'CampaignEngine'):
        """Intelligence operations to steal blueprints from enemy starbases/fleets."""
        faction = engine.get_faction(faction_name)
        if not faction: return False
        
        # 0. Intel Point Check (Comment 3)
        if hasattr(faction, 'intel_points') and faction.intel_points < 200:
             return False
        
        # 1. Visibility Check
        if target_location.name not in faction.visible_planets:
            return False
            
        # 2. Success Calculation
        import random
        success_chance = 0.15 # Base 15%
        
        # Modifiers
        # +10% if target is sieged
        if hasattr(target_location, 'is_sieged') and target_location.is_sieged:
             success_chance += 0.10
             
        # +5% per scout fleet at location
        scouts = sum(1 for f in engine.fleets if f.faction == faction_name and f.location == target_location and getattr(f, 'is_scout', False))
        success_chance += (scouts * 0.05)
        
        # -10% if target has defense platforms
        defense_val = getattr(target_location, 'defense_level', 0)
        if defense_val > 0:
             success_chance -= 0.10
             
        success_chance = max(0.05, min(0.95, success_chance))
        
        # Roll
        roll = random.random()
        if roll < success_chance:
             # ON SUCCESS
             # Select random blueprint from target faction's unlocked techs
             target_f_obj = engine.get_faction(target_faction)
             if not target_f_obj: return False
             
             unlocked = getattr(target_f_obj, 'unlocked_techs', [])
             if not unlocked: return False
             
             from src.utils.blueprint_registry import BlueprintRegistry
             import copy
             
             # Weighted by strategic value
             tech_values = engine.tech_manager.analyze_tech_tree(target_faction)
             candidates = [t for t in unlocked if t in tech_values]
             if not candidates: candidates = unlocked
             
             total_val = sum(tech_values.get(t, 1.0) for t in candidates)
             if total_val > 0:
                  weights = [tech_values.get(t, 1.0) / total_val for t in candidates]
                  blueprint_id = random.choices(candidates, weights=weights, k=1)[0]
             else:
                  blueprint_id = random.choice(candidates)
             
             # Load and Modify
             bp = BlueprintRegistry.get_instance().get_blueprint(blueprint_id)
             if not bp: return False
             
             modified_bp = copy.deepcopy(bp)
             
             # Apply "Reverse-Engineered" trait (reduces effectiveness by 10%)
             if "base_stats" in modified_bp:
                  for stat in modified_bp["base_stats"]:
                       if isinstance(modified_bp["base_stats"][stat], (int, float)):
                            modified_bp["base_stats"][stat] *= 0.9
                            
             if "default_traits" not in modified_bp: modified_bp["default_traits"] = []
             if "Reverse-Engineered" not in modified_bp["default_traits"]:
                  modified_bp["default_traits"].append("Reverse-Engineered")
                  
             # Check if faction doctrine allows using stolen tech (Step 8)
             ai_mgr = engine.ai_manager
             if hasattr(ai_mgr, 'filter_tech_by_doctrine'):
                 if not ai_mgr.filter_tech_by_doctrine(faction, blueprint_id, "theft"):
                     engine.faction_reporter.log_event(faction_name, "intelligence", 
                         f"Doctrine rejected stolen blueprint {blueprint_id} from {target_faction}")
                     if hasattr(ai_mgr, 'apply_doctrine_effects'):
                         ai_mgr.apply_doctrine_effects(faction, "reject_alien_tech", blueprint_id)
                     return False  # Don't register

             BlueprintRegistry.get_instance().register_blueprint(modified_bp, faction_owner=faction_name)
             
             # Cost: Deduct intel points
             if hasattr(faction, 'intel_points'):
                  faction.intel_points -= 200
                  
             # Diplomatic penalty
             if hasattr(engine, 'diplomacy'):
                  engine.diplomacy.add_grudge(target_faction, faction_name, 30, reason="Technology Theft")
                  
             # Persist to faction model (Phase 8 logic)
             if hasattr(faction, 'register_stolen_blueprint'):
                  faction.register_stolen_blueprint(blueprint_id, target_faction, engine.turn_counter)
             
             # Intra-Universe Fix: Unlock tech for the faction so it satisfies prerequisites
             if blueprint_id not in faction.unlocked_techs:
                 faction.unlocked_techs.append(blueprint_id)
                 faction.tech_unlocked_turns[blueprint_id] = engine.turn_counter
                  
             engine.faction_reporter.log_event(faction_name, "intelligence", f"Stole blueprint {blueprint_id} from {target_faction}")
             
             # Log Telemetry
             if hasattr(engine, 'telemetry'):
                  engine.telemetry.log_event(
                      EventCategory.TECHNOLOGY, "blueprint_stolen",
                      {"faction": faction_name, "blueprint_id": blueprint_id, "target_faction": target_faction, "success": True},
                      turn=engine.turn_counter,
                      faction=faction_name
                  )
             if engine.logger:
                  engine.logger.campaign(f"[ESPIONAGE] {faction_name} SUCCESSFUL technology theft at {target_location.name} (Stole {blueprint_id})")
             return True
        else:
             # ON FAILURE
             # 50% chance of detection
             detected = False
             if random.random() < 0.50:
                  detected = True
                  if hasattr(engine, 'diplomacy'):
                       engine.diplomacy.add_grudge(target_faction, faction_name, 10, reason="Attempted Technology Theft")
                       engine.diplomacy.modify_relation(target_faction, faction_name, -5)
                  engine.faction_reporter.log_event(target_faction, "diplomacy", f"Caught {faction_name} attempting technology theft at {target_location.name}!")

             # Log Telemetry (Failure)
             if hasattr(engine, 'telemetry'):
                  engine.telemetry.log_event(
                      EventCategory.TECHNOLOGY, "blueprint_stolen",
                      {"faction": faction_name, "target_faction": target_faction, "success": False, "detected": detected},
                      turn=engine.turn_counter,
                      faction=faction_name
                  )
             
             if engine.logger:
                  engine.logger.campaign(f"[ESPIONAGE] {faction_name} FAILED technology theft at {target_location.name}")
             return False
        

    # --- Advanced Espionage (Phase 2 Implementation) ---

    def update_spy_networks(self, faction_name: str) -> None:
        """
        Turn-based update for spy networks: growth, decay, and exposure checks.
        """
        faction = self.engine.get_faction(faction_name)
        if not faction: return

        # Load networks if they exist
        if not hasattr(faction, 'spy_networks'): return

        # NEW: Base Intel Point Income
        # Base: 50 + Tech Modifiers
        income = 50
        income *= faction.get_modifier("intel_income_mult", 1.0)
        faction.intel_points += int(income)

        for target_name, network in faction.spy_networks.items():
            if network.is_exposed:
                # Decay exposed networks rapidly
                network.degrade(5.0)
                # Chance to recover exposure status if infiltration drops low enough
                if network.infiltration_level < 10.0:
                    network.is_exposed = False
            else:
                # Passive Growth based on Intel Points investment or tech
                # Default growth: 1.0 per turn
                growth_rate = 1.0
                
                # Tech modifiers check (Phase 107)
                growth_rate *= faction.get_modifier("espionage_growth_mult", 1.0)
                
                network.grow(growth_rate)
                
                # Counter-Espionage Check (Passive Detection)
                target_f = self.engine.get_faction(target_name)
                if target_f:
                    # Base chance 2% + 1% per 10 infiltration
                    detection_chance = 0.02 + (network.infiltration_level / 1000.0) 
                    # Defense Multiplier (e.g. from Tech/Buildings)
                    detection_chance *= target_f.get_modifier("counter_espionage_mult", 1.0)
                    
                    import random
                    if random.random() < detection_chance:
                        network.expose()
                        if self.engine.logger:
                            self.engine.logger.campaign(f"[ESPIONAGE] Spy Network from {faction_name} EXPOSED in {target_name} by counter-intel sweep!")
                        if self.engine.diplomacy:
                             self.engine.diplomacy.add_grudge(target_name, faction_name, 20, "Discovered spy network")

    def establish_spy_network(self, faction_name: str, target_faction_name: str) -> bool:
        """
        Attempts to plant a spy network in a target faction.
        """
        faction = self.engine.get_faction(faction_name)
        target = self.engine.get_faction(target_faction_name)
        if not faction or not target: return False

        # Check if already exists
        if target_faction_name in faction.spy_networks:
            return False

        # Cost Check (e.g. 500 Intel Points)
        cost = 500
        if faction.intel_points < cost:
            return False

        faction.intel_points -= cost
        
        # Import dynamically to avoid circular imports at top level if needed
        from src.models.spy_network import SpyNetwork
        
        new_net = SpyNetwork(target_faction_name)
        new_net.established_turn = self.engine.turn_counter
        faction.spy_networks[target_faction_name] = new_net
        
        if self.engine.logger:
            self.engine.logger.campaign(f"[ESPIONAGE] {faction_name} established Spy Network in {target_faction_name}.")
            
        return True

    def conduct_espionage_mission(self, faction_name: str, target_name: str, mission_type: str) -> bool:
        """
        Executes a mission using the spy network.
        Missions: SABOTAGE_PRODUCTION, INCITE_UNREST, STEAL_TECH, STEAL_MAP
        """
        faction = self.engine.get_faction(faction_name)
        network = faction.spy_networks.get(target_name)
        
        if not network or network.is_exposed:
            return False

        import random

        # Mission Requirements
        requirements = {
            "STEAL_MAP": {"level": 10, "cost": 100},
            "SABOTAGE_PRODUCTION": {"level": 30, "cost": 300},
            "STEAL_TECH": {"level": 50, "cost": 500},
            "INCITE_UNREST": {"level": 70, "cost": 800}
        }

        req = requirements.get(mission_type)
        if not req: return False

        if network.infiltration_level < req["level"] or faction.intel_points < req["cost"]:
            return False

        # Execute
        faction.intel_points -= req["cost"]
        
        # Risk Check
        # Base detection chance 20% + (Infiltration / 200) -> Higher infiltration = slightly higher risk of high profile ops? 
        # Actually usually higher skill = lower risk. Let's say risk scales with MISSION difficulty.
        risk_map = {
            "STEAL_MAP": 0.10,
            "SABOTAGE_PRODUCTION": 0.25,
            "STEAL_TECH": 0.40,
            "INCITE_UNREST": 0.50
        }
        detection_chance = risk_map.get(mission_type, 0.3)
        
        # Modifier: Counter-Espionage Tech
        target_faction = self.engine.get_faction(target_name)
        if target_faction:
            detection_chance *= target_faction.get_modifier("counter_espionage_mult", 1.0)

        is_detected = random.random() < detection_chance

        if is_detected:
            network.expose()
            if self.engine.diplomacy:
                self.engine.diplomacy.add_grudge(target_name, faction_name, 40, f"Caught spy attempting {mission_type}")
            
            # [PHASE 6] Espionage Detection Trace
            import src.config.logging_config as logging_config
            if logging_config.LOGGING_FEATURES.get('intelligence_espionage_tracing', False):
                 if hasattr(self.engine.logger, 'campaign'):
                     trace_msg = {
                         "event_type": "espionage_mission_outcome",
                         "faction": faction_name,
                         "target": target_name,
                         "mission": mission_type,
                         "result": "DETECTED",
                         "turn": self.engine.turn_counter
                     }
                     self.engine.logger.campaign(f"[INTEL] {faction_name} agent DETECTED by {target_name}", extra=trace_msg)

            if self.engine.logger:
                self.engine.logger.campaign(f"[ESPIONAGE] {faction_name} agent CAPTURED in {target_name} during {mission_type}!")
            return False

        # Success Effects
        success = False
        if mission_type == "SABOTAGE_PRODUCTION":
            success = self._effect_sabotage(target_name)
        elif mission_type == "INCITE_UNREST":
            success = self._effect_unrest(target_name)
        elif mission_type == "STEAL_TECH":
            # Reuse existing logic but gated by network
            # We need a dummy location for the old method, or refactor. 
            # Let's pick a random visible planet for the 'location' argument
            if faction.visible_planets:
                # Find one owned by target
                targets_planets = [p for p in faction.visible_planets if self.engine.get_planet(p).owner == target_name]
                if targets_planets:
                    p_name = random.choice(targets_planets)
                    p_obj = self.engine.get_planet(p_name)
                    success = self.attempt_blueprint_theft(faction_name, target_name, p_obj, self.engine)
            else:
                success = False # Can't steal if we can't see where they are
        elif mission_type == "STEAL_MAP":
            success = self._effect_steal_map(faction, target_faction)

        if success:
        # [PHASE 6] Espionage Success Trace
            import src.config.logging_config as logging_config
            if logging_config.LOGGING_FEATURES.get('intelligence_espionage_tracing', False):
                 if hasattr(self.engine.logger, 'campaign'):
                     trace_msg = {
                         "event_type": "espionage_mission_outcome",
                         "faction": faction_name,
                         "target": target_name,
                         "mission": mission_type,
                         "result": "SUCCESS",
                         "turn": self.engine.turn_counter
                     }
                     self.engine.logger.campaign(f"[INTEL] {faction_name} SUCCESS: {mission_type} against {target_name}", extra=trace_msg)

            if self.engine.logger:
                 self.engine.logger.campaign(f"[ESPIONAGE] {faction_name} SUCCESS: {mission_type} against {target_name}")
            # XP for network? 
            # network.grow(5.0) 
        
        return success

    def _effect_sabotage(self, target_faction_name: str) -> bool:
        """Halts construction queues on a random planet."""
        target = self.engine.get_faction(target_faction_name)
        import random
        # Get planets with active queues
        valid_planets = [p for p in self.engine.planets_by_faction.get(target_faction_name, []) if p.construction_queue]
        if not valid_planets: return False
        
        planet = random.choice(valid_planets)
        # Verify queue is not empty again
        if not planet.construction_queue: return False
        
        # Sabotage: Add 5 turns to the first item
        item = planet.construction_queue[0]
        item["turns_left"] += 5
        
        if self.engine.logger:
            self.engine.logger.campaign(f"[SABOTAGE] Saboteurs delayed construction at {planet.name} by 5 turns.")
        return True

    def _effect_unrest(self, target_faction_name: str) -> bool:
        """Reduces stability on a key planet."""
        target = self.engine.get_faction(target_faction_name)
        import random
        planet = random.choice(self.engine.planets_by_faction.get(target_faction_name, []))
        if not planet: return False
        
        # Reduce stability
        current_stab = getattr(planet, 'stability', 100)
        planet.stability = max(0, current_stab - 20)
        
        if self.engine.logger:
            self.engine.logger.campaign(f"[UNREST] Agitators lowered stability at {planet.name} to {planet.stability}.")
        return True

    def _effect_steal_map(self, faction, target_faction) -> bool:
        """Reveals target's visible planets to us."""
        if not target_faction: return False
        
        # Copy their visible set
        learned_count = 0
        for p_name in target_faction.visible_planets:
            if p_name not in faction.known_planets:
                faction.known_planets.add(p_name)
                learned_count += 1
        
        return learned_count > 0

