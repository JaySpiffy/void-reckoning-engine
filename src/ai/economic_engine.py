from typing import Dict, Any, TYPE_CHECKING, Optional
import random
import json
from src.utils.profiler import profile_method
from src.config import logging_config 

if TYPE_CHECKING:
    from src.managers.ai_manager import AIManager

class EconomicEngine:
    """
    Handles AI economic decision-making, extracting logic from StrategicAI/AIManager.
    """
    def __init__(self, ai_manager: 'AIManager'):
        self.ai = ai_manager
        self.engine = ai_manager.engine
        self._health_cache = {} # (faction, turn) -> health_dict

    def assess_economic_health(self, faction: str) -> Dict[str, Any]:
        """
        Evaluates faction's economic state: HEALTHY, STRESSED, CRISIS, BANKRUPT.
        Returns detailed metrics dict. Uses per-turn caching.
        """
        current_turn = getattr(self.engine, 'turn_counter', 0)
        cache_key = (faction, current_turn)
        
        if cache_key in self._health_cache:
            return self._health_cache[cache_key]

        f_mgr = self.engine.get_faction(faction)
        if not f_mgr: 
            result = {"state": "HEALTHY", "margin": 2.0}
            self._health_cache[cache_key] = result
            return result
        
        # Use EconomyManager if available
        if hasattr(self.engine, 'economy_manager'):
            report = self.engine.economy_manager.get_faction_economic_report(faction)
            
            # Recalculate State from Report Data
            margin = report.get("margin", 1.0)
            income = report.get("income", 100)
            upkeep = report.get("upkeep", 100)
            requisition = f_mgr.requisition
            
            # Trigger Role Update (Lazy)
            # self.update_planet_roles(faction) # Expensive? Maybe do it less often or here.
            # Let's do it here, it's just distance calcs for ~10 planets.
            self.update_planet_roles(faction)

            # Get Predictive Model
            prediction = self.predict_economic_state(faction)
            
            state = "HEALTHY"
            if requisition < -1000: state = "BANKRUPT"
            elif prediction.get("status") == "CRASH_IMMINENT": state = "CRISIS" # Pre-emptive Crisis
            elif margin < 0.8: state = "CRISIS"
            elif margin < 1.2: state = "STRESSED"
            elif prediction.get("status") == "WARNING": state = "STRESSED"

            result = {
                "state": state,
                "margin": margin,
                "income": income,
                "upkeep": upkeep,
                "can_sustain_fleet": income > (upkeep + 200),
                "requisition": requisition,
                "prediction": prediction
            }
        else:
            # Fallback (Manual Calcs) if EconomyManager missing
            prediction = self.predict_economic_state(faction)
            state = "HEALTHY"
            if prediction.get("status") == "CRASH_IMMINENT": state = "CRISIS"
            
            result = {
                "state": state,
                "margin": 2.0, 
                "income": 1000,
                "upkeep": 0,
                "can_sustain_fleet": True,
                "requisition": f_mgr.requisition,
                "prediction": prediction
            }
            self.update_planet_roles(faction)
            
        self._health_cache[cache_key] = result
        return result

    def calculate_fleet_upkeep(self, fleet) -> int:
        """Calculates total upkeep for all units in a fleet."""
        return sum(getattr(u, 'upkeep', 0) for u in fleet.units)

    def clear_cache(self) -> None:
        """Clears the economic health cache."""
        self._health_cache.clear()

    def evaluate_research_priorities(self, faction_name: str) -> None:
        """
        AI logic to select and queue research projects using Research Points (RP).
        Prioritizes Infinite Techs once tree is completed.
        """
        f = self.engine.get_faction(faction_name)
        if not f: return
        
        # 1. Check if we need to queue something
        # Queue depth < 2 to keep options flexible
        if len(f.research_queue) >= 2:
            return

        # 2. Get Available Research
        # Includes Base Tree + Infinite Procedural Tiers
        # [MODIFIED] Use "Card" System (Stellaris-style)
        candidates = self.engine.tech_manager.draw_research_cards(f, num_cards=3)
        if not candidates: return

        
        # 3. Selection Strategy (Synergy-Based)
        import random
        from src.models.research_project import ResearchProject

        # [Phase 1] Synergy Scoring & Diversification
        # Goal: Prefer techs that align with existing tech themes (Specialization)
        # but avoid neglecting defense/economy (Diversification)
        
        candidates_scored = []
        unlocked_ids = set(f.unlocked_techs)
        
        # Calculate Current Focus
        theme_counts = {"weapon": 0, "defense": 0, "economy": 0, "utility": 0}
        for u_id in unlocked_ids:
            u_lower = u_id.lower()
            if any(k in u_lower for k in ["weapon", "cannon", "gun", "plasma", "beam"]): theme_counts["weapon"] += 1
            if any(k in u_lower for k in ["shield", "armor", "plating", "hull"]): theme_counts["defense"] += 1
            if any(k in u_lower for k in ["mine", "refinery", "factory", "economic", "trade"]): theme_counts["economy"] += 1
        
        for cand in candidates:
            score = 10.0 # Base Score
            c_id = cand["id"]
            cost = cand["cost"]
            c_lower = c_id.lower()
            
            # 1. Cost Efficiency (Prefer cheaper/starter techs initially)
            if cost < 2000: score += 5
            
            # 2. Synergy Check (Keyword Matching)
            import re
            keywords = set(re.split(r'[_\s]', c_id.lower()))
            
            synergy_hits = 0
            for u_id in unlocked_ids:
                u_keywords = set(re.split(r'[_\s]', u_id.lower()))
                common = keywords.intersection(u_keywords)
                common = {w for w in common if w not in ["tech", "research", "mk", "i", "ii", "iii", "iv", "v", "upgrade"]}
                if common:
                    synergy_hits += len(common)
            
            score += synergy_hits * 2.0
            
            # 3. Diversification Bias
            # If we lack defense, boost defense techs
            if any(k in c_lower for k in ["shield", "armor", "plating", "hull"]) and theme_counts["defense"] < theme_counts["weapon"]:
                score += 8.0
            
            # If we lack economy, boost economy techs
            if any(k in c_lower for k in ["mine", "refinery", "factory", "economic", "trade"]) and theme_counts["economy"] < 3:
                score += 12.0
            
            # 4. Infinite Tech Bias (Keep upgrading weapons)
            if "Mk" in c_id or re.search(r"\d+$", c_id):
                score += 4.0
                
            candidates_scored.append((cand, score))
            
        # Weighted Sort
        candidates_scored.sort(key=lambda x: x[1], reverse=True)
        
        # Pick from top 3
        top_n = candidates_scored[:3]
        if not top_n: return
        
        # [PHASE 6] Research Trace
        if logging_config.LOGGING_FEATURES.get('tech_research_path_analysis', False):
            if hasattr(self.engine.logger, 'research'):
                trace_candidates = [
                    {"id": c[0]["id"], "score": c[1], "cost": c[0]["cost"]} 
                    for c in top_n
                ]
                
                trace_msg = {
                    "event_type": "research_path_analysis",
                    "faction": faction_name,
                    "turn": self.engine.turn_counter,
                    "top_candidates": trace_candidates,
                    "selected": top_n[0][0]["id"],
                    "reasoning": "Highest Synergy/Utility Score"
                }
                self.engine.logger.research(json.dumps(trace_msg))

        # Weighted Choice within top 3? Or just best?
        # Let's verify list isn't empty (checked above)
        target = top_n[0][0] # Pick the highest score consistently for strategic focus
        
        # OLD RANDOM: target = random.choice(candidates)
        
        # 4. Queue Project
        # Validate cost > 0
        cost = max(1, target["cost"])
        
        project = ResearchProject(
            tech_id=target["id"],
            total_cost=cost
        )
        f.research_queue.append(project)
        
        # Log
        if self.engine.logger:
             self.engine.logger.campaign(f"[STRATEGY] {faction_name} queued research: {project.tech_id} (Cost: {project.total_cost} RP)")
             
        # 5. Legacy Weapon Upgrade Integration?
        # The old system upgraded weapons directly via Requisition.
        # Ideally, we should generate these as Techs (e.g. "Weapons Research V").
        # The Infinite Tech system handles this via "Mark V" generation in TechManager.
        # So manual weapon upgrades are deprecated in favor of procedural tech tiers.
        pass

    def predict_economic_state(self, faction_name: str, horizon: int = 15) -> Dict[str, Any]:
        """
        [Phase 1] Predictive Modeling.
        Forecasts economic health N turns into the future to prevent bankruptcy.
        Now includes military expansion decay and historical smoothing.
        """
        f = self.engine.get_faction(faction_name)
        if not f: return {}
        
        current_req = f.requisition
        
        # 1. Historical Trends
        income = f.stats.get("turn_req_income", 0)
        expense = f.stats.get("turn_req_expense", 0)
        
        # 2. Projected Upkeep Growth (Safety Margin)
        # If the faction is expanding fleets, maintenance will grow.
        # Assume 5% maintenance GROWTH if recently active in navy/army recruitment.
        navy_spent = f.stats.get("turn_navy_spent", 0)
        upkeep_drift = 1.0
        if navy_spent > 500:
            upkeep_drift = 1.05 # 5% compounding growth projected
            
        # 3. Multi-turn Forecast
        pure_upkeep = 0
        if hasattr(self.engine, 'economy_manager'):
             report = self.engine.economy_manager.get_faction_economic_report(faction_name)
             pure_upkeep = report.get("upkeep", 0)
        else:
             pure_upkeep = expense * 0.8 # Heuristic estimate
             
        forecast = current_req
        temp_upkeep = pure_upkeep
        for i in range(horizon):
            net = income - (temp_upkeep * (upkeep_drift ** i))
            forecast += net
            
        prediction = {
            "current": current_req,
            "horizon": horizon,
            "forecast": forecast,
            "structural_balance": income - pure_upkeep,
            "status": "STABLE"
        }
        
        if forecast < 0:
            prediction["status"] = "CRASH_IMMINENT"
            # Calculate intersection
            delta = income - pure_upkeep
            prediction["turns_to_bankruptcy"] = abs(current_req / delta) if delta < 0 else 999
        elif forecast < 2500: # Higher buffer
            prediction["status"] = "WARNING"
            
        return prediction

    def update_planet_roles(self, faction_name: str) -> None:
        """
        [Phase 1] Planet Specialization.
        Assigns 'CORE' or 'FRONTIER' roles based on proximity to threats.
        """
        f = self.engine.get_faction(faction_name)
        if not f or not self.engine.all_planets: return
        
        # 1. Identify Owned Planets
        owned_planets = [p for p in self.engine.all_planets if p.owner == faction_name]
        if not owned_planets: return
        
        # 2. Identify Enemy Planets
        enemy_planets = [p for p in self.engine.all_planets if p.owner != "Neutral" and p.owner != faction_name]
        # Treat Neutral as non-threat for now, or maybe low threat?
        # If no enemies, everything is Core? Or Frontier if expansion?
        # Let's assume Frontier if near Neutral too, for expansion logic.
        
        if not enemy_planets: 
            # If alone, everything is Frontier (Expansion focus) or Core (Greed)?
            # Let's say Frontier to encourage defense against Neutrals/Events
            for p in owned_planets: p.role = "FRONTIER"
            return

        import math

        # 3. Calculate Roles
        # Threshold: 50.0 units or nearest neighbor logic?
        # Let's use: If distance to NEAREST enemy < 60.0 -> FRONTIER. Else -> CORE.
        # Map size is roughly 500x500? 60 is decent buffer.
        
        for p in owned_planets:
            p_pos = (p.system.x, p.system.y) if hasattr(p, 'system') and p.system else (0,0)
            
            min_dist = 999999
            for e in enemy_planets:
                e_pos = (e.system.x, e.system.y) if hasattr(e, 'system') and e.system else (0,0)
                dist = math.hypot(p_pos[0] - e_pos[0], p_pos[1] - e_pos[1])
                if dist < min_dist:
                    min_dist = dist
            
            new_role = "FRONTIER" if min_dist < 80.0 else "CORE" # Increased to 80 for safety
            
            # Log change if significant?
            # if p.role != new_role and self.engine.logger:
            #     self.engine.logger.info(f"[ECON] {p.name} redesignated as {new_role} (Dist: {min_dist:.1f})")
            
            p.role = new_role
