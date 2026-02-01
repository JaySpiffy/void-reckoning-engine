
import math
from typing import Dict, Any, List, Optional
from universes.base.personality_template import FactionPersonality

class AIPersonalityGenerator:
    """
    Converts raw extracted AI data into standardized FactionPersonality objects.
    Handles data normalization, heuristic linking, and combat doctrine inference.
    """
    
    def __init__(self):
        pass

    # Note: Third-party personality generation methods (generate_from_stellaris, generate_from_eaw) have been removed.
    # To add custom universe-specific personality generation, add new methods here.

    def generate_from_generic(self, faction_name: str, hints: Dict) -> FactionPersonality:
        """Fallback generator."""
        agg = 1.0
        diplo = 0
        
        name_lower = faction_name.lower()
        if "empire" in name_lower or "dominion" in name_lower:
            agg = 1.3
            diplo = -20
        elif "republic" in name_lower or "federation" in name_lower:
            agg = 0.8
            diplo = 20
        elif "horde" in name_lower or "swarm" in name_lower:
            agg = 1.5
            diplo = -100
            
        return FactionPersonality(
            name=f"{faction_name}_Generic",
            aggression=agg,
            diplomacy_bonus=diplo
        )

    def normalize_personality(self, personality: FactionPersonality) -> FactionPersonality:
        """Ensures values are within sane ranges."""
        personality.aggression = max(0.1, min(3.0, personality.aggression))
        personality.expansion_bias = max(0.1, min(3.0, personality.expansion_bias))
        personality.retreat_threshold = max(0.0, min(0.9, personality.retreat_threshold))
        personality.cohesiveness = max(0.1, min(2.0, personality.cohesiveness))
        return personality

    def infer_combat_doctrine(self, behaviors: Dict, quirks: Dict) -> str:
        """Infers combat doctrine string from behavior flags."""
        if behaviors.get("sneak_attacker") or quirks.get("evasion_rating", 0) > 0.1:
            return "AMBUSH"
        if behaviors.get("purger") or "swarm" in str(quirks):
            return "SWARM"
        if behaviors.get("defensive_mode") or quirks.get("turtling"):
            return "DEFENSIVE_WALL"
        if behaviors.get("aggressiveness", 0) > 1.5:
             return "AGGRESSIVE_ASSAULT"
             
        # Fallback
        return "STANDARD"
