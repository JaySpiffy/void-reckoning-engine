"""
faction_manager.py

Manages the lifecycle and registry of Faction objects.
This manager is responsible for:
- creating/registering Faction instances.
- maintaining the authoritative list of factions in the campaign.
- providing lookups for factions by name.
- filtering factions by status (alive/dead).

This class extracts faction management responsibilities previously held by CampaignEngine.
"""
from typing import Dict, List, Optional, Any
from src.models.faction import Faction
from src.utils.game_logging import GameLogger, LogCategory

from src.core.service_locator import ServiceLocator

class FactionManager:
    """
    Manages the lifecycle and registry of factions in the campaign.
    Extracts this responsibility from CampaignEngine.
    """
    def __init__(self, logger: Optional[GameLogger] = None):
        self.logger = logger
        self._repo = None

    @property
    def repository(self):
        if self._repo is None:
            self._repo = ServiceLocator.get("FactionRepository")
        return self._repo

    @property
    def factions(self) -> Dict[str, Faction]:
        # Backward compatibility for direct dict access
        return {f.name: f for f in self.repository.get_all()}

    def register_faction(self, faction: Faction):
        """Registers a faction in the manager."""
        self.repository.save(faction)
        if self.logger:
            self.logger.debug(f"Faction registered: {faction.name}")

    def get_faction(self, faction_name: str) -> Optional[Faction]:
        return self.repository.get_by_id(faction_name)

    def get_all_factions(self) -> List[Faction]:
        return self.repository.get_all()

    def get_faction_names(self) -> List[str]:
        return [f.name for f in self.repository.get_all()]
    
    def get_living_factions(self) -> List[Faction]:
        return self.repository.get_living_factions()

    def clear(self):
        self.repository.clear()
