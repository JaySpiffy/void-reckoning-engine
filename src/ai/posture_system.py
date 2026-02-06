import random
from typing import Dict, Any, List, Optional
from src.ai.posture_registry import PostureRegistry

class PostureManager:
    """
    Manages faction posture transitions using a weighted lottery with hysteresis.
    """
    def __init__(self, ai_manager, universe_name: str = "void_reckoning"):
        self.ai_manager = ai_manager
        self.registry = PostureRegistry(universe_name)
        self.inertia_bonus = 30.0
        self.personality_bonus = 20.0
        self.selection_threshold = 0.1 # Pick anything within 10% of top score

    def update_faction_posture(self, faction_name: str):
        """
        Evaluates the current situation and decides if a posture change is needed.
        """
        f_mgr = self.ai_manager.engine.get_faction(faction_name)
        if not f_mgr: return

        # 1. Get Candidates
        candidates = self.registry.get_available_postures(faction_name)
        if not candidates: return

        # 2. Score Candidates
        scored_candidates = []
        current_posture = getattr(f_mgr, 'strategic_posture', "BALANCED")
        
        # Get baseline situation stats
        situation = self._get_situation_context(faction_name, f_mgr)

        for p_id in candidates:
            p_data = self.registry.get_posture(p_id)
            score = self._calculate_posture_score(p_id, p_data, f_mgr, situation, current_posture)
            if score > 0:
                scored_candidates.append((p_id, score))

        if not scored_candidates: return

        # 3. Selection Logic (Weighted Lottery)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_score = scored_candidates[0][1]
        
        # Filter by threshold
        best_candidates = [p for p, s in scored_candidates if s >= top_score * (1.0 - self.selection_threshold)]
        
        new_posture = random.choice(best_candidates)

        # 4. Apply Transition
        if new_posture != current_posture:
            self._apply_posture_change(faction_name, f_mgr, new_posture)

    def _calculate_posture_score(self, p_id: str, p_data: Dict, f_mgr: Any, situation: Dict, current_posture: str) -> float:
        """Calculates final score for a posture candidate."""
        score = 0.0

        # A. Trigger Conditions
        triggers = p_data.get("triggers", {})
        if not self._check_triggers(triggers, situation):
            return 0.0
        
        score += 50.0 # Base score for meeting triggers

        # B. Hysteresis (Inertia)
        if p_id == current_posture:
            score += self.inertia_bonus

        # C. Personality Alignment
        personality = self.ai_manager.get_faction_personality(f_mgr.name)
        if personality:
            archetype = p_data.get("archetype")
            # This is a bit simplified; ideally we check if archetype aligns with doctrine/aggression
            if archetype == "BLITZ" and personality.aggression > 1.3:
                score += self.personality_bonus
            elif archetype == "TURTLE" and personality.aggression < 0.8:
                score += self.personality_bonus

        # D. Situation Match (Emergent Variety)
        # Add small randomness
        score += random.uniform(0, 10)

        return score

    def _check_triggers(self, triggers: Dict, situation: Dict) -> bool:
        """Validates triggers against current situation."""
        if not triggers: return True # Default postures always valid

        # Example Trigger: "at_war": True
        if "at_war" in triggers and triggers["at_war"] != situation["is_at_war"]:
            return False
        
        # Example Trigger: "econ_state": "CRISIS"
        if "econ_state" in triggers and triggers["econ_state"] != situation["econ_state"]:
            return False

        # Example Trigger: "min_military_ratio": 1.2
        if "min_military_ratio" in triggers and situation["military_ratio"] < triggers["min_military_ratio"]:
            return False

        return True

    def _get_situation_context(self, faction_name: str, f_mgr: Any) -> Dict:
        """Derived situation metrics for trigger checking."""
        engine = self.ai_manager.engine
        
        # Econ
        econ = self.ai_manager.assess_economic_health(faction_name)
        
        # War
        is_at_war = False
        if engine.diplomacy:
             for other in engine.factions:
                 if engine.diplomacy.get_relation(faction_name, other) == "War":
                     is_at_war = True
                     break
                     
        # Power Ratio
        my_power = sum(f.power for f in engine.fleets if f.faction == faction_name)
        avg_enemy_power = 1000 # Default
        enemies = [f for f in engine.factions if f != faction_name and f != "Neutral"]
        if enemies:
            enemy_total_power = sum(f.power for f in engine.fleets if f.faction in enemies)
            avg_enemy_power = enemy_total_power / len(enemies)
            
        ratio = my_power / max(1, avg_enemy_power)

        return {
            "is_at_war": is_at_war,
            "econ_state": econ["state"],
            "military_ratio": ratio,
            "turn": engine.turn_counter
        }

    def _apply_posture_change(self, faction_name: str, f_mgr: Any, new_posture: str):
        """Executes the posture switch and logs it."""
        old_posture = getattr(f_mgr, 'strategic_posture', "BALANCED")
        
        # Update Faction
        f_mgr.strategic_posture = new_posture
        f_mgr.posture_changed_turn = self.ai_manager.engine.turn_counter
        
        # Reset cooldowns or duration trackers if needed (Phase 2 extension)
        
        if self.ai_manager.engine.logger:
            self.ai_manager.engine.logger.strategy(f"[POSTURE] {faction_name} switched from {old_posture} to {new_posture}")
            
        # Telemetry
        self.ai_manager._log_strategic_decision(
            faction_name,
            "POSTURE_CHANGE",
            new_posture,
            f"Switching from {old_posture}",
            {"old": old_posture, "new": new_posture},
            "Adaptive Strategy"
        )
