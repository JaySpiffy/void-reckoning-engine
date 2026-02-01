from typing import Dict, Any, Optional
from universes.base.personality_template import FactionPersonality

class DynamicWeightSystem:
    """
    Manages context-aware weighting for target selection.
    Allows the AI to shift priorities (e.g. from Economy to Military)
    based on strategic context.
    """
    def __init__(self):
        # Default Weights (Balanced)
        self.default_weights = {
            "income": 1.0,          # Economic value
            "strategic": 1.0,       # Choke points, connections
            "distance": 1.0,        # Distance penalty factor
            "threat": 1.0,          # Avoidance of strong enemies
            "capital": 1.0,         # Priority for enemy capitals
            "weakness": 1.0,        # Priority for weak targets
            "expansion_bias": 1.0   # General urge to take planets
        }
        
        # Context Overrides
        self.context_profiles = {
            "EARLY_EXPANSION": {
                "income": 1.5,
                "distance": 2.0,      # Grab nearby stuff fast
                "threat": 0.5,        # Less concerned with enemies yet
                "expansion_bias": 1.5
            },
            "TOTAL_WAR": {
                "strategic": 2.0,
                "capital": 5.0,       # Decapitate
                "threat": 0.2,        # Attack into teeth of enemy
                "weakness": 1.5,
                "distance": 0.8       # Willing to go further
            },
            "CONSOLIDATION": {
                "distance": 3.0,      # Only super close things
                "income": 2.0,        # Build tall
                "threat": 2.0,        # Avoid conflict
                "expansion_bias": 0.2
            },
            "OPPORTUNISTIC": {
                "weakness": 3.0,      # Pounce on weak
                "distance": 0.5,      # Willing to travel for free loot
                "threat": 1.0
            },
            "DESPERATE_DEFENSE": {
                "strategic": 3.0,     # Hold choke points
                "income": 0.5,
                "expansion_bias": 0.0
            },
            "THREATENED": {
                "income": 0.8,
                "strategic": 1.5,     # Fortify
                "threat": 2.5,        # High avoidance of strong enemies
                "expansion_bias": 0.4
            }
        }

    def get_weights(self, context: str, personality: Optional['FactionPersonality'] = None) -> Dict[str, float]:
        """
        Returns the weight dictionary for a given context, 
        modulated by personality.
        """
        # Start with defaults
        weights = self.default_weights.copy()
        
        # Apply Context Overrides
        if context in self.context_profiles:
            profile = self.context_profiles[context]
            for key, val in profile.items():
                weights[key] = val
                
        # Apply Personality Modifiers
        if personality:
            # Aggression increases willingness to fight strong targets (lowers threat avoidance)
            # and increases expansion bias
            weights['threat'] /= max(0.1, personality.aggression)
            weights['expansion_bias'] *= personality.expansion_bias
            
            # Cohesiveness increases strategic focus (choke points)
            weights['strategic'] *= personality.cohesiveness
            
        return weights
