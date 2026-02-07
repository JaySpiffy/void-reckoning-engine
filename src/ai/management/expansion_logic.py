from typing import Any, Dict, List, Set
import random
from src.utils.profiler import profile_method

class ExpansionLogic:
    def __init__(self, ai_manager: Any):
        self.ai = ai_manager
        self.engine = ai_manager.engine

    @profile_method
    def calculate_expansion_target_score(self, planet_name: str, faction: str, 
                                        home_x: float, home_y: float, 
                                        personality_name: str, econ_state: str, turn: int,
                                        weights: Dict[str, float] = None) -> float:
        """Cached expansion target scoring with intelligence integration."""
        mandates = self.ai.turn_cache.get('mandates', {}).get(faction, {})
        
        return self.ai.target_scoring.calculate_expansion_target_score(
            planet_name, faction, home_x, home_y, personality_name, econ_state, turn, 
            mandates=mandates, weights=weights
        )

    def handle_expansion_logic(self, faction: str, f_mgr: Any, available_fleets: list, personality: Any, econ_state: str, owned_planets: list, expansion_bias: float, weights: dict):
        """Specific logic for exploration vs expansion (Honey Pot Logic)."""
        owned_systems_count = len(set([p.system.name for p in owned_planets if hasattr(p, 'system')]))
        
        if owned_systems_count < 2:
             # ISOLATED: Prioritize finding/seizing first colony
             has_col_target = False
             if f_mgr.requisition >= 200:
                 for pname in f_mgr.known_planets:
                     p = next((x for x in self.engine.all_planets if x.name == pname), None)
                     if p and p.owner == "Neutral" and p.name not in [op.name for op in owned_planets]:
                         has_col_target = True
                         break
             
             if has_col_target:
                 # Colonize first!
                 self.ai.offensive_strategy.handle_offensive_expansion(faction, available_fleets, f_mgr, personality, econ_state, owned_planets, expansion_bias, weights)
                 self.ai.exploration_strategy.handle_exploration(faction, available_fleets, f_mgr, personality)
             else:
                 # Explore first!
                 self.ai.exploration_strategy.handle_exploration(faction, available_fleets, f_mgr, personality)
                 self.ai.offensive_strategy.handle_offensive_expansion(faction, available_fleets, f_mgr, personality, econ_state, owned_planets, expansion_bias, weights)
        else:
             # ESTABLISHED: Prioritize Expansion/War
             self.ai.offensive_strategy.handle_offensive_expansion(faction, available_fleets, f_mgr, personality, econ_state, owned_planets, expansion_bias, weights)
             self.ai.exploration_strategy.handle_exploration(faction, available_fleets, f_mgr, personality)

    @profile_method
    def classify_defense_zones(self, faction: str) -> Dict[str, str]:
        """Classifies owned planets into Capital Zone, Border Zone, and Core Zone."""
        zones = {}
        owned = self.engine.planets_by_faction.get(faction, [])
        if not owned: return zones
        
        # 1. Identify Capital
        capital = next((p for p in owned if "Capital" in [n.type for n in p.provinces]), owned[0])
        
        # 2. Identify Borders
        for p in owned:
            is_border = False
            if hasattr(p, 'system') and p.system.connections:
                for neighbor_sys in p.system.connections:
                    external_threat = False
                    for np in neighbor_sys.planets:
                        if np.owner != faction:
                            external_threat = True
                            break
                    if external_threat:
                        is_border = True
                        break
            
            if p == capital: zones[p.name] = "CAPITAL"
            elif is_border: zones[p.name] = "BORDER"
            else: zones[p.name] = "CORE"
                
        # Buffer zones around capital
        if hasattr(capital, 'system') and capital.system.connections:
            for neighbor_sys in capital.system.connections:
                for np in neighbor_sys.planets:
                    if np.owner == faction and zones.get(np.name) != "CAPITAL":
                        zones[np.name] = "CAPITAL_ZONE"
                        
        return zones

    @profile_method
    def calculate_exploration_frontier(self, faction: str):
        """Identifies and prioritizes systems for exploration."""
        f_mgr = self.engine.factions[faction]
        owned_planets = self.engine.planets_by_faction.get(faction, [])
        if not owned_planets: return
        
        # Only update periodically (every 5 turns) or if frontier is empty
        if f_mgr.exploration_frontier and (self.engine.turn_counter - f_mgr.last_exploration_update < 5):
            return

        f_mgr.exploration_frontier = []
        candidates = set()
        
        for p in owned_planets:
            if hasattr(p.system, 'connections'):
                for neighbor in p.system.connections:
                    if neighbor.name not in f_mgr.explored_systems:
                        candidates.add(neighbor)
                        
        personality = self.ai.get_faction_personality(faction)
        
        for sys in candidates:
            # Diplomatic Filter
            if self.engine.diplomacy:
                has_invalid_ally = False
                coordinating = (f_mgr.active_strategic_plan and f_mgr.active_strategic_plan.diplomatic_goal == "COORDINATE_WITH_ALLY")
                    
                for p in sys.planets:
                     if p.owner != "Neutral" and p.owner != faction:
                         if not self.ai.is_valid_target(faction, p.owner) and not coordinating:
                             has_invalid_ally = True
                             break
                                 
                if has_invalid_ally: continue

            # Score Calculation
            score = self._score_exploration_system(sys, owned_planets, personality)
            f_mgr.exploration_frontier.append((score, sys))
            
        f_mgr.exploration_frontier.sort(key=lambda x: x[0], reverse=True)
        f_mgr.last_exploration_update = self.engine.turn_counter

    def _score_exploration_system(self, sys: Any, owned_planets: list, personality: Any) -> float:
        score = 0
        min_dist = 9999
        for p in owned_planets:
            d = ((p.system.x - sys.x)**2 + (p.system.y - sys.y)**2)**0.5
            if d < min_dist: min_dist = d
        
        score += max(0, 100 - min_dist)
        connections = len(sys.connections)
        if connections <= 2: score += 20 # Chokepoint
        if connections >= 5: score += 10 # Hub
        if personality.aggression > 1.2: score += 5
        return score

    @profile_method
    def predict_enemy_threats(self, faction: str):
        """Scans visible enemy fleets to detect incoming attacks."""
        threats = []
        f_mgr = self.engine.factions[faction]
        
        # Optimized: Use Cached Candidates
        candidates = self.ai.turn_cache.get("threats_by_faction", {}).get(faction, [])
        
        for f in candidates:
            if f.faction == faction or f.is_destroyed: continue
            if f.faction == "Neutral": continue
            
            # Visibility Check (Fog of War)
            is_visible = False
            current_loc_name = f.location.name if hasattr(f.location, 'name') else None
            if current_loc_name and current_loc_name in f_mgr.visible_planets:
                is_visible = True
            
            if not is_visible: continue
            if not f.destination: continue
            
            # Calculate ETA
            eta = len(f.route) if f.route else 1 
            
            threats.append({
                "target": f.destination,
                "fleet": f,
                "eta": eta,
                "strength": f.power
            })
            if self.engine.logger:
                 self.engine.logger.intelligence(f"{faction} detects {f.faction} fleet incoming to {f.destination.name} (ETA: {eta})")
                
        return threats


    def select_scout_target(self, faction: str, f_mgr):
        """Selects the next best target for a scout fleet from the frontier."""
        self.calculate_exploration_frontier(faction)
        
        if not f_mgr.exploration_frontier:
            return None
            
        # Pop highest priority system
        score, target_system = f_mgr.exploration_frontier.pop(0)
        
        # Select a random planet in that system
        if target_system.planets:
            return random.choice(target_system.planets)
            
        return None

    def _process_sieges(self, faction: str):
        """[Phase 22] Checks for sieged planets where we have armies and triggers invasions."""
        f_mgr = self.engine.factions.get(faction)
        if not f_mgr: return

        # Get all fleets of this faction
        fleets = [f for f in self.engine.fleets if f.faction == faction and not f.is_destroyed]
        
        for fleet in fleets:
            if not fleet.location: continue
            
            # Check if location is a valid target (Planet)
            if not hasattr(fleet.location, 'owner'): continue
            
            planet = fleet.location
            
            # Skip invalid targets
            if planet.owner == faction: continue
            
            # Phase 22: Proactive Invasion Trigger
            is_at_war = False
            if planet.owner != "Neutral" and hasattr(self.engine, 'diplomacy') and self.engine.diplomacy:
                 dm = self.engine.diplomacy
                 state = dm.treaty_coordinator.get_treaty(faction, planet.owner)
                 is_at_war = state == "War"
            
            can_invade = False
            if planet.owner == "Neutral":
                can_invade = True
            elif is_at_war:
                can_invade = True
            elif getattr(planet, 'is_sieged', False):
                can_invade = True
            
            if not can_invade:
                continue

            # [FIX] Proactive War Check for Invasion
            if planet.owner != "Neutral" and hasattr(self.engine, 'diplomacy') and self.engine.diplomacy:
                 dm = self.engine.diplomacy
                 state = dm.treaty_coordinator.get_treaty(faction, planet.owner)
                 rel = dm.get_relation(faction, planet.owner)
                 if state != "War" and rel < -25:
                     dm._declare_war(faction, planet.owner, rel, self.engine.turn_counter, reason="Invasion of " + planet.name)
                
            # Check for Cargo Armies
            if not fleet.cargo_armies: continue
            
            # Trigger Invasion
            if self.engine.logger:
                 self.engine.logger.campaign(f"[STRATEGY] {faction} launching invasion of {planet.name} from {fleet.id}!")
            
            if hasattr(self.engine.battle_manager, 'land_armies'):
                 self.engine.battle_manager.land_armies(fleet, planet)

    def get_cached_exploration_frontier(self, faction: str):
        f_mgr = self.engine.factions[faction]
        if faction not in self.ai.turn_cache.get("exploration_frontiers", {}):
            if "exploration_frontiers" not in self.ai.turn_cache:
                self.ai.turn_cache["exploration_frontiers"] = {}
            self.calculate_exploration_frontier(faction)
            self.ai.turn_cache["exploration_frontiers"][faction] = f_mgr.exploration_frontier
        return self.ai.turn_cache["exploration_frontiers"][faction]
