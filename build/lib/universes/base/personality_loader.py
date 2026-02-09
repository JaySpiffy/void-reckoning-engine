from typing import Protocol, Dict, Any, runtime_checkable
from .personality_template import FactionPersonality

@runtime_checkable
class PersonalityLoaderProtocol(Protocol):
    """
    Protocol for universe-specific AI personality modules.
    
    Any universe that wishes to provide custom AI behavior must implement
    this interface in its ai_personalities.py module.
    """
    
    def get_personality(self, faction_name: str) -> FactionPersonality:
        """Returns the personality for a specific faction."""
        ...
    
    def get_all_personalities(self) -> Dict[str, FactionPersonality]:
        """Returns all personality definitions."""
        ...
    
    def get_combat_doctrines(self) -> Dict[str, Dict[str, Any]]:
        """Returns the available combat doctrines for the universe."""
        ...

def validate_personalities(module: Any, required_factions: list) -> tuple[bool, list[str]]:
    """
    Validates a personality module against a list of required factions.
    
    Args:
        module: The personality module to validate.
        required_factions: List of faction names that must have personalities.
        
    Returns:
        tuple[bool, list[str]]: (Success, Errors)
    """
    errors = []
    
    if not isinstance(module, PersonalityLoaderProtocol):
        errors.append("Module does not implement PersonalityLoaderProtocol")
        return False, errors
        
    all_p = module.get_all_personalities()
    for faction in required_factions:
        if faction not in all_p:
            errors.append(f"Missing personality for required faction: {faction}")
            
    return len(errors) == 0, errors
