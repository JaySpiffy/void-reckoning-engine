import functools
import random
import json
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from src.reporting.telemetry import EventCategory
from src.utils.profiler import profile_method
from src.config import logging_config 

if TYPE_CHECKING:
    from src.core.interfaces import IEngine
    from src.models.fleet import Fleet
    from src.models.planet import Planet
    from src.ai.strategic_planner import StrategicPlan
    from universes.base.personality_template import FactionPersonality

class TargetScoringService:
    """
    Service for calculating strategic target scores and evaluating 
    faction strategic posture. Provides cached scoring for performance.
    """
    
    def __init__(self, ai_manager):
        self.ai_manager = ai_manager
        self.engine = ai_manager.engine
        
    @profile_method
    def calculate_expansion_target_score(self, planet_name: str, faction: str, 
                                        home_x: float, home_y: float, 
                                        personality_name: str, econ_state: str, turn: int,
                                        weights: Dict[str, float] = None,
                                        mandates: Dict[str, Any] = None) -> float:
        """Cached expansion target scoring with dynamic weights."""
        # Note: Added 'weights' dict for dynamic scoring. 
        # Caching strategy: We can't easily cache with a dict argument in lru_cache. 
        # For now, we will assume weights are passed from the caller who handles the context.
        # If performance is an issue, we can cache based on a hashed ID of the weights.
        
        planet = self.engine.get_planet(planet_name)
        if not planet: return 0.0
        
        f_mgr = self.engine.get_faction(faction)
        if not f_mgr: return 0.0
        
        # Pull weights from Posture System V3 if none provided
        if weights is None:
            posture_id = getattr(f_mgr, 'strategic_posture', "BALANCED")
            posture_data = self.ai_manager.posture_manager.registry.get_posture(posture_id)
            if posture_data and "weights" in posture_data:
                weights = posture_data["weights"]
            else:
                weights = self.ai_manager.dynamic_weights.get_weights("BALANCED") # Fallback
            
        # [MANDATES] Apply Opponent-Specific Adjustments
        # Copy weights to avoid mutating the shared context weights
        local_weights = weights.copy()
        if mandates and planet.owner in mandates:
             adjustments = mandates[planet.owner]
             for k, v in adjustments.items():
                 # Map mandate keys to weight keys if they differ
                 # e.g. 'threat_weight' -> 'threat'
                 w_key = k.replace('_weight', '')
                 if w_key in local_weights:
                     local_weights[w_key] *= v
        
        weights = local_weights # Use modified weights for calculation

        # --- DYNAMIC SCORING SYSTEM ---
        
        # 1. Economic Value
        base_value = (planet.income_req * weights['income']) + getattr(planet, 'income_prom', 0)
        
        # [INTELLIGENCE] Adjust based on memory
        intel = f_mgr.intelligence_memory.get(planet.name)
        if intel:
            last_seen = intel.get('last_seen_turn', 0)
            turns_ago = turn - last_seen
            
            # Prioritize Stale Intel (Curiosity)
            if turns_ago > 5:
                base_value *= 1.2
                
            # Weakness Exploitation
            if intel.get('income', 0) > 300:
                 base_value *= weights['weakness']

        # [FEATURE] No-Retreat Exploitation (The "Blood in the Water" Check)
        # Check if any enemy fleets at this location have already retreated this turn.
        # If so, they are sitting ducks (cannot retreat again).
        if hasattr(self.ai_manager, 'turn_cache') and "fleets_by_loc" in self.ai_manager.turn_cache:
            loc_id = id(planet)
            fleets_here = self.ai_manager.turn_cache["fleets_by_loc"].get(loc_id, [])
            for f in fleets_here:
                if f.faction != faction and f.faction != "Neutral":
                    # Check hostility (simplified, could check diplo)
                    if getattr(f, 'has_retreated_this_turn', False):
                        # FOUND ONE!
                        # Massive boost to encourage finishing them off.
                        base_value *= 5.0 
                        if logging_config.LOGGING_FEATURES.get('strategy_debug', False) and hasattr(self.engine, 'logger'):
                             self.engine.logger.debug(f"[STRATEGY] {faction} smells blood at {planet_name}! Vulnerable fleet detected (Retreated). Priority BOOSTED.")
                        break

        # [QUIRK] Resource Valorization / Biomass Hunger
        if hasattr(f_mgr, 'learned_personality') and getattr(f_mgr.learned_personality, 'biomass_hunger', 0) > 0:
             bh = f_mgr.learned_personality.biomass_hunger
             base_value *= (1.0 + bh)
             
             # Prioritize Bio-Rich Worlds
             p_class = getattr(planet, 'planet_class', '').lower()
             if any(x in p_class for x in ['agri', 'gaia', 'tropical', 'ocean', 'jungle']):
                 base_value *= (1.0 + bh)
        
        # Neutral Target Bonus (Colonization Priority)
        if planet.owner == "Neutral":
            base_value *= (1.5 + (0.5 * weights['expansion_bias']))
            if econ_state in ["STRESSED", "CRISIS"]:
                base_value *= 1.5

        # 2. Capital Bonus
        is_capital = "Capital" in [n.type for n in planet.provinces]
        capital_mult = weights['capital'] if is_capital else 1.0
        if is_capital and planet.owner != faction and planet.owner != "Neutral":
             capital_mult *= 2.0 # Extra incentive to take enemy capitals
        
        # 3. Strategic Importance
        connections = len(planet.system.connections) if hasattr(planet, 'system') and hasattr(planet.system, 'connections') else 3
        choke_mult = 1.0
        if connections <= 2:
            choke_mult = weights['strategic'] * 1.5
        
        strategic_value = choke_mult
        
        # 4. Distance Penalty
        px = planet.system.x if hasattr(planet, 'system') else 0
        py = planet.system.y if hasattr(planet, 'system') else 0
        dist = ((home_x - px)**2 + (home_y - py)**2)**0.5
        dist = max(10, dist)
        
        # Weighted Distance Penalty: higher weight['distance'] means penalty drops off faster/steeper
        # Standard: 100/dist. 
        # Heavy Penalty: 100 / (dist * weight)
        dist_factor = 100.0 / (dist * weights['distance'])
        
        # 5. Threat Factor
        enemy_power = 0
        if intel:
             turns_since = turn - intel.get('last_seen_turn', 0)
             if turns_since < 5:
                 enemy_power = intel.get('strength', 0)
        
        threat_mult = 1.0
        if enemy_power > 0:
            threat_ratio = enemy_power / 5000.0 
            # High weights['threat'] means we AVOID threat (multiplier < 1.0)
            # Low weights['threat'] means we IGNORE threat (multiplier stays near 1.0)
            avoidance = weights['threat']
            threat_mult = 1.0 / (1.0 + (threat_ratio * avoidance))
        
        # FINAL SCORE
        score = base_value * capital_mult * strategic_value * dist_factor * threat_mult

        # [PHASE 6] Planet Assessment Trace
        if logging_config.LOGGING_FEATURES.get('planet_strategic_value_assessment', False):
            if hasattr(self.ai_manager.engine, 'logger') and hasattr(self.ai_manager.engine.logger, 'strategy'):
                trace_msg = {
                    "event_type": "planet_strategic_value_assessment",
                    "faction": faction,
                    "planet": planet_name,
                    "turn": turn,
                    "score_breakdown": {
                        "base_value": base_value,
                        "capital_mult": capital_mult,
                        "strategic_value": strategic_value,
                        "dist_factor": dist_factor,
                        "threat_mult": threat_mult
                    },
                    "final_score": score
                }
                self.ai_manager.engine.logger.strategy(json.dumps(trace_msg))

        return score

    def calculate_dynamic_retreat_threshold(self, fleet: 'Fleet', location: 'Planet', 
                                          personality: 'FactionPersonality', 
                                          strategic_plan: 'StrategicPlan') -> float:
        """Calculates retreat threshold based on strategic importance."""
        base = personality.retreat_threshold
        
        # 1. Location Importance
        loc_name = getattr(location, 'name', "Deep Space")
        f_mgr = self.engine.factions.get(fleet.faction)
        
        if f_mgr and loc_name == f_mgr.home_planet_name:
            base *= 2.0 # Defend Capital
        
        if strategic_plan:
            if loc_name in strategic_plan.priority_planets:
                base *= 1.5
            if loc_name in strategic_plan.target_systems:
                base *= 1.2
                
        # 2. Economic State
        # Delegate to AI manager which delegates to EconomicEngine
        econ = self.ai_manager.assess_economic_health(fleet.faction)
        if econ['state'] == "CRISIS": base *= 0.7 # Can't afford losses
        
        # 3. Fleet Composition
        has_capital = any(getattr(u, 'ship_class', "") in ["Battleship", "Iron-Sarcophagus", "Titan"] for u in fleet.units if u.is_alive())
        if has_capital: base *= 1.2 # Preserve big ships
        
        # 4. Doctrine Modifiers
        flexibility = personality.retreat_flexibility
        if personality.strategic_doctrine == "AGGRESSIVE_EXPANSION":
            base *= (1.0 + (0.2 * (1.0 - flexibility))) # Stubborn
        elif personality.strategic_doctrine == "OPPORTUNISTIC":
            base *= (1.0 - (0.3 * flexibility)) # Run away easily
            
        # [QUIRK] High Aggression (Furor!)
        if personality.aggression > 1.5:
            base = 0.05
            
        # 5. Data-Driven Quirk Modifier
        base += getattr(personality, 'retreat_threshold_mod', 0.0)
             
        # [PHASE 23] Combat Lethality Tuning
        # Original Cap was 0.9 (Retreat if < 90% power). This is too cowardly.
        # New Base Cap: 0.5 (Retreat if < 50% power).
        # Aggressive factions should have 0.1 or 0.0.
        
        # Upper clamp: 0.6 (Never retreat if you have > 60% of enemy power)
        # Lower clamp: 0.0 (Fight to the death)
        return max(0.0, min(0.6, base))

    def evaluate_strategic_posture(self, faction_name: str, personality: 'FactionPersonality', 
                                  plan: 'StrategicPlan') -> None:
        """Check if we need to switch strategies (Expansion vs Consolidation)."""
        f_mgr = self.engine.get_faction(faction_name)
        if not f_mgr: return
        
        # Calculate Metrics
        territory_count = len(self.engine.planets_by_faction.get(faction_name, []))
        econ = self.ai_manager.assess_economic_health(faction_name)
        
        # Fleet Strength Ratio (Us vs Neighbors)
        my_power = sum(f.power for f in self.engine.fleets if f.faction == faction_name)
        neighbor_power = 0
        known_neighbors = f_mgr.known_factions
        if known_neighbors:
             for n in known_neighbors:
                 neighbor_power += sum(f.power for f in self.engine.fleets if f.faction == n)
        else:
            neighbor_power = 5000 # Dummy baseline
            
        count = len(known_neighbors) if known_neighbors else 1
        ratio = my_power / max(1, neighbor_power / count)
        
        # Overextension Score
        overextension = (territory_count * 1000) / max(1, my_power)
        
        # Decision Logic
        new_posture = f_mgr.strategic_posture
        
        if overextension > 3.0 or econ['state'] == "CRISIS":
            new_posture = "CONSOLIDATION"
        elif ratio > 1.5 and econ['state'] == "HEALTHY":
            new_posture = "EXPANSION"
        
        if new_posture != f_mgr.strategic_posture:
            if random.random() < personality.adaptation_speed:
                 self.switch_strategy(faction_name, new_posture, personality)

    def switch_strategy(self, faction_name: str, new_posture: str, personality: 'FactionPersonality') -> None:
        f_mgr = self.engine.factions.get(faction_name)
        if not f_mgr: return
        
        print(f"  > [STRATEGY] {faction_name} switching posture: {f_mgr.strategic_posture} -> {new_posture}")
        # Telemetry
        self.ai_manager._log_strategic_decision(
            faction_name, 
            "POSTURE_CHANGE", 
            new_posture, 
            "Adaptive Strategy Switch", 
            {"old_posture": f_mgr.strategic_posture, "new_posture": new_posture}, 
            "Improve Strategic Position"
        )

        f_mgr.strategic_posture = new_posture
        f_mgr.posture_changed_turn = self.engine.turn_counter
        
        if new_posture == "CONSOLIDATION":
            personality.aggression *= 0.7
            personality.expansion_bias *= 0.5
        elif new_posture == "EXPANSION":
            personality.aggression *= 1.3
            personality.expansion_bias *= 1.5
            
        # Force plan update next turn
        if f_mgr.active_strategic_plan:
             f_mgr.active_strategic_plan.current_phase = "CONSOLIDATION"
             if new_posture == "CONSOLIDATION":
                 f_mgr.active_strategic_plan.duration = 0

    def clear_caches(self) -> None:
        """Clear LRU caches."""
        if hasattr(self.calculate_expansion_target_score, 'cache_clear'):
            self.calculate_expansion_target_score.cache_clear()
