from typing import Dict, Any, Optional
from .personality_template import FactionPersonality

def export_personality_to_dict(personality: FactionPersonality) -> Dict[str, Any]:
    """Converts a FactionPersonality to a JSON-serializable dict."""
    return personality.to_dict()

def import_personality_from_dict(data: Dict[str, Any]) -> FactionPersonality:
    """Reconstructs a FactionPersonality from dict data."""
    return FactionPersonality.from_dict(data)

def validate_personality_data(personality: FactionPersonality) -> tuple[bool, str]:
    """
    Checks if personality values are within acceptable ranges.
    
    Returns:
        tuple[bool, str]: (Success, Error message)
    """
    if not (0.1 <= personality.aggression <= 2.0):
        return False, f"Aggression {personality.aggression} out of range [0.1, 2.0]"
    
    if not (0.0 <= personality.expansion_bias <= 2.0):
        return False, f"Expansion bias {personality.expansion_bias} out of range [0.0, 2.0]"
        
    if not (0.5 <= personality.cohesiveness <= 2.0):
        return False, f"Cohesiveness {personality.cohesiveness} out of range [0.5, 2.0]"
        
    if not (0.0 <= personality.retreat_threshold <= 1.0):
        return False, f"Retreat threshold {personality.retreat_threshold} out of range [0.0, 1.0]"
        
    return True, ""
