from abc import ABC, abstractmethod
from typing import Optional, Any

class FactionAIStrategy(ABC):
    """
    Interface for Faction AI decision making (Strategy Pattern).
    Encapsulates tactical and operational logic previously in CampaignManager.
    """
    
    @abstractmethod
    def choose_target(self, fleet: Any, engine: Any) -> Optional[Any]:
        """Decides the next target for a fleet."""
        pass
        
    @abstractmethod
    def process_reinforcements(self, faction: str, engine: Any) -> None:
        """Handles logistics and army transport logic."""
        pass
