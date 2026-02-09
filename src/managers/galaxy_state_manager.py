"""
galaxy_state_manager.py

Manages the runtime state of the galaxy's topology, specifically Systems and Planets.
This manager is responsible for:
- Storing the list of all System objects.
- Storing the list of all Planet objects.
- providing efficient lookups for systems/planets by name.
- Tracking planet ownership (though the Faction model holds the authoritative owner string).

This class extracts state management responsibilities previously held by CampaignEngine.
"""
from typing import List, Optional, Dict, Any, Union
from src.core.universe_data import UniverseDataManager
from src.models.planet import Planet
from src.utils.game_logging import GameLogger, LogCategory

from src.core.service_locator import ServiceLocator

class GalaxyStateManager:
    """
    Manages the runtime state of the galaxy, including systems and planets.
    Extracts this responsibility from CampaignEngine.
    """
    def __init__(self, universe_data_manager: UniverseDataManager, logger: Optional[GameLogger] = None):
        self.universe_data = universe_data_manager
        self.logger = logger
        self._planet_repo = None
        self._system_repo = None

    def __getstate__(self):
        """Exclude logger and singleton universe_data from pickling."""
        state = self.__dict__.copy()
        if 'logger' in state: del state['logger']
        if 'universe_data' in state: del state['universe_data']
        return state

    def __setstate__(self, state):
        """Restore state and re-acquire singleton."""
        self.__dict__.update(state)
        self.logger = None # Re-injected by engine/logger system if needed, or lazy loaded
        from src.core.universe_data import UniverseDataManager
        self.universe_data = UniverseDataManager.get_instance()


    @property
    def planet_repository(self):
        if self._planet_repo is None:
            self._planet_repo = ServiceLocator.get("PlanetRepository")
        return self._planet_repo

    @property
    def system_repository(self):
        if self._system_repo is None:
            self._system_repo = ServiceLocator.get("SystemRepository")
        return self._system_repo

    def set_systems(self, systems: List[Any]):
        """Sets the list of systems and indexes them."""
        self.system_repository.clear()
        self.planet_repository.clear()
        
        for system in systems:
            self.system_repository.save(system)
            for planet in system.planets:
                self.planet_repository.save(planet)
        
        if self.logger:
            self.logger.info(f"GalaxyStateManager synchronized with {len(self.system_repository.get_all())} systems and {len(self.planet_repository.get_all())} planets.")

    def get_system(self, system_name: str) -> Optional[Any]:
        return self.system_repository.get_by_id(system_name)

    def get_planet(self, planet_name: str) -> Optional[Planet]:
        return self.planet_repository.get_by_id(planet_name)

    @property
    def planets_by_faction(self) -> Dict[str, List[Planet]]:
        return self.planet_repository.get_ownership_index()
        
    @planets_by_faction.setter
    def planets_by_faction(self, value):
        # [COMPATIBILITY] Legacy initializer sets this to empty dict.
        # We ignore it as Repository manages state.
        pass

    def update_planet_ownership(self, planet: Planet, old_owner: str, new_owner: str) -> None:
        """Updates the repository index for planet ownership."""
        self.planet_repository.update_ownership(planet, old_owner, new_owner)

    def get_all_systems(self) -> List[Any]:
        return self.system_repository.get_all()

    def get_all_planets(self) -> List[Planet]:
        return self.planet_repository.get_all()
        
    def get_planets_by_owner(self, faction_name: str) -> List[Planet]:
        """Returns all planets owned by a specific faction."""
        return self.planet_repository.get_by_owner(faction_name)

