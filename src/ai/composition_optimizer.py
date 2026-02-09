
from typing import Dict, List, Any
import json
from src.core.interfaces import IEngine
from src.config import logging_config

class CompositionOptimizer:
    """
    Analyzes enemy fleet compositions and designs specific counters.
    Implements a Rock-Paper-Scissors logic for Hull/Weapon types.
    """
    def __init__(self, ai_manager):
        self.ai = ai_manager
        self.engine = ai_manager.engine

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'engine' in state: del state['engine']
        if 'ai' in state: del state['ai']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.engine = None
        self.ai = None
        
    def analyze_enemy_composition(self, enemy_faction: str) -> Dict[str, float]:
        """
        Scans known enemy fleets/ships to determine their composition profile.
        Returns: {shield_bias: 0.0-1.0, armor_bias: 0.0-1.0, swarm_bias: 0.0-1.0}
        """
        profile = {"shield_bias": 0.0, "armor_bias": 0.0, "swarm_bias": 0.0}
        
        # Get Intel on Enemy Fleets
        # We use known_fleets from IntelligenceManager or scan visible fleets
        f_mgr = self.engine.get_faction(enemy_faction)
        # Actually we (self.ai.faction?) are analyzing ENEMY.
        # So we need to look at what *we* know about them.
        # But this method is usually called by AI for *itself* against an enemy.
        # Let's assume input is just the faction name we want to counter.
        # We need access to the "Observer's" knowledge. 
        # But for now let's cheat slightly and look at actual enemy fleets for simulation purpose
        # OR use intelligence service. Let's use actual fleets to be robust for now.
        
        fleets = [f for f in self.engine.fleets if f.faction == enemy_faction and not f.is_destroyed]
        if not fleets: return profile
        
        total_ships = 0
        total_shields = 0
        total_armor = 0
        swarm_count = 0
        
        for f in fleets:
            for u in f.units:
                total_ships += 1
                stats = getattr(u, 'stats', {})
                
                # Check Defenses
                shields = stats.get('max_shields', 0)
                hp = stats.get('max_hp', 0)
                # Heuristic: If Shields > 50% of HP, it's a shield ship
                if shields > hp * 0.5:
                    total_shields += 1
                else:
                    total_armor += 1
                    
                # Check Size (Swarm)
                if stats.get('max_hp', 0) < 500: # Small ship threshold
                    swarm_count += 1
                    
        if total_ships > 0:
            profile["shield_bias"] = total_shields / total_ships
            profile["armor_bias"] = total_armor / total_ships
            profile["swarm_bias"] = swarm_count / total_ships
            
        # [PHASE 24] Interdiction Logic
        # Estimate retreat rate from global intelligence or stats
        # For now, check if we have Diplo/Intel data on their "Cowardice" or history
        # Simplify: If we have tracked battles against them, check retreat count
        
        # Stub: If enemy is Aaether-kini/Drukhari (known skittish), boost this
        f_obj = self.engine.get_faction(enemy_faction)
        if f_obj:
             dna = getattr(f_obj, 'personality_id', '')
             if dna in ['Aaether-kini_Craftworld', 'Drukhari_Cabal']:
                  profile["retreat_rate"] = 0.8
             else:
                  profile["retreat_rate"] = 0.1
                  
             # Better: Check actual Telemetry if available
             # But telemetry is send-only usually.
             # We could check self.ai.opponent_profiler if implemented.
             if hasattr(self.ai, 'opponent_profiler') and self.ai.opponent_profiler:
                 prof = self.ai.opponent_profiler.get_profile(enemy_faction)
                 if prof: profile["retreat_rate"] = prof.get("retreat_tendency", 0.1)
            
        # [PHASE 6] Composition Optimization Trace
        if logging_config.LOGGING_FEATURES.get('fleet_optimization_tracking', False):
            if hasattr(self.engine.logger, 'ai'):
                trace_msg = {
                    "event_type": "enemy_composition_analyzed",
                    "enemy_faction": enemy_faction,
                    "profile": profile,
                    "total_ships": total_ships,
                    "turn": self.engine.turn_counter
                }
                self.engine.logger.ai(f"[OPTIMIZER] Analyzed {enemy_faction} composition", extra=trace_msg)
            
        return profile
        
    def recommend_counter_doctrine(self, enemy_profile: Dict[str, float]) -> str:
        """
        Returns a doctrine/design recommendation based on profile.
        """
        if enemy_profile.get("retreat_rate", 0.0) > 0.4:
            rec = "INTERDICTION" # They run away too much!
        elif enemy_profile["shield_bias"] > 0.6:
            rec = "ANTI_SHIELD" # Recomend Void/Lance weapons
        elif enemy_profile["armor_bias"] > 0.6:
            rec = "ANTI_ARMOR" # Recommend Plasma/Macro
        elif enemy_profile["swarm_bias"] > 0.6:
            rec = "AREA_EFFECT" # Recommend Blast/AoE
        else:
            rec = "BALANCED"

        # [PHASE 6] Recommendation Trace
        if logging_config.LOGGING_FEATURES.get('fleet_optimization_tracking', False):
            if hasattr(self.engine.logger, 'ai'):
                trace_msg = {
                    "event_type": "counter_doctrine_recommended",
                    "profile": enemy_profile,
                    "recommendation": rec,
                    "turn": self.engine.turn_counter
                }
                self.engine.logger.ai(f"[OPTIMIZER] Recommended {rec} for profile", extra=trace_msg)

        return rec

    def adjust_production_priorities(self, faction: str, doctrine: str):
        """
        Adjusts the Tech/Ship production weights for the faction.
        """
        f_mgr = self.engine.get_faction(faction)
        if not f_mgr: return
        
        # This hook would interact with ShipDesignService to prioritize 
        # generating blueprints that match the doctrine.
        
        # E.g. Set a global "design_preference" on the faction
        f_mgr.design_preference = doctrine
        
        if self.engine.logger:
            self.engine.logger.campaign(f"[OPTIMIZER] {faction} shifting production to {doctrine} to counter enemy composition.")
