from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, TypedDict

class CombatPhase(TypedDict):
    """Structure for defining a combat phase.
    
    Attributes:
        name: e.g., "psychic", "shooting", "melee"
        handler: Function to execute phase
        priority: Execution order (lower = earlier)
        required: Whether phase is mandatory
        dependencies: List of phases names that must run before this
    """
    name: str
    handler: Callable
    priority: int
    required: bool
    dependencies: List[str]

class CombatRulesBase(ABC):
    """
    Abstract base class for pluggable combat systems.
    
    Allows different universes to define their own combat mechanics,
    phases, and execution order while keeping the tactical engine generic.
    """
    
    @abstractmethod
    def register_phases(self) -> List[CombatPhase]:
        """Registers all combat phases available in this universe.
        
        Returns:
            List[CombatPhase]: A list of phase definitions.
        """
        pass
    
    @abstractmethod
    def get_phase_order(self) -> List[str]:
        """Returns the sorted list of phase names in execution order.
        
        Returns:
            List[str]: Ordered phase names.
        """
        pass
    
    @abstractmethod
    def initialize_combat_state(self, armies_dict: Dict, grid: Any, tracker: Any) -> Dict:
        """Initializes any universe-specific combat state.
        
        Args:
            armies_dict: Dictionary of armies in combat.
            grid: Combat grid object.
            tracker: Combat tracker object.
            
        Returns:
            Dict: The initial combat state.
        """
        pass
    
    @abstractmethod
    def validate_combat_rules(self) -> bool:
        """Validates that all registered phases have valid handlers and dependencies.
        
        Returns:
            bool: True if rules are valid.
        """
        pass
