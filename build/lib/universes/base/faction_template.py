from typing import Protocol, List, Dict, Any, runtime_checkable

@runtime_checkable
class FactionTemplate(Protocol):
    """
    Abstract interface for faction definitions across universes.
    
    Each universe must provide faction implementations that conform to this
    interface, ensuring compatibility with the core simulation engine.
    
    Example:
        class ImperiumFaction(FactionTemplate):
            def get_faction_name(self) -> str:
                return "Imperium"
    """
    
    def get_faction_name(self) -> str:
        """Returns the canonical faction name.
        
        Returns:
            str: The name of the faction.
        """
        ...
    
    def get_subfactions(self) -> List[str]:
        """Returns a list of subfactions or regiments.
        
        Returns:
            List[str]: Names of subfactions.
        """
        ...
    
    def get_starting_resources(self) -> Dict[str, int]:
        """Returns the initial resource pool for this faction.
        
        Returns:
            Dict[str, int]: Map of resource names to amounts.
        """
        ...
    
    def get_faction_traits(self) -> Dict[str, Any]:
        """Returns faction-specific traits, buffs, and quirks.
        
        Returns:
            Dict[str, Any]: Configuration of traits and modifiers.
        """
        ...
    
    def validate_faction_data(self) -> bool:
        """Validates that all required data files for this faction exist.
        
        Returns:
            bool: True if all data is present and valid.
        """
        ...
