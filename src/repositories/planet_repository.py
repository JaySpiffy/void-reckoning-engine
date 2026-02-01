from typing import List, Optional, Dict, Any
from src.repositories.base_repository import BaseRepository
from src.models.planet import Planet

class PlanetRepository(BaseRepository):
    """Repository for managing Planet entities."""
    
    def __init__(self):
        self._planets: Dict[str, Planet] = {}
        self._planets_by_owner: Dict[str, List[Planet]] = {}
        
    def get_by_id(self, entity_id: str) -> Optional[Planet]:
        return self._planets.get(entity_id)
        
    def get_all(self) -> List[Planet]:
        return list(self._planets.values())
        
    def save(self, entity: Planet) -> None:
        # If new or updating, we need to handle index
        if entity.name not in self._planets:
            self._planets[entity.name] = entity
            owner = getattr(entity, 'owner', 'Neutral')
            if owner not in self._planets_by_owner:
                self._planets_by_owner[owner] = []
            if entity not in self._planets_by_owner[owner]:
                self._planets_by_owner[owner].append(entity)
        else:
            # If already exists, we assume the caller handles index updates via update_ownership
            # OR we check if ownership changed. 
            # Since objects are references, checking self._planets[name].owner vs entity.owner 
            # is checking the same object if they are the same reference.
            # So checking "change" requires knowing the state in the index vs the object.
            # We defer to update_ownership for explicit moves.
            pass
        
    def delete(self, entity_id: str) -> None:
        if entity_id in self._planets:
            p = self._planets[entity_id]
            owner = getattr(p, 'owner', 'Neutral')
            if owner in self._planets_by_owner and p in self._planets_by_owner[owner]:
                self._planets_by_owner[owner].remove(p)
            del self._planets[entity_id]
            
    def get_by_owner(self, faction_name: str) -> List[Planet]:
        """Returns all planets owned by a specific faction."""
        return self._planets_by_owner.get(faction_name, [])

    def get_ownership_index(self) -> Dict[str, List[Planet]]:
        """Returns the raw ownership index dict."""
        return self._planets_by_owner

    def update_ownership(self, planet: Planet, old_owner: str, new_owner: str) -> None:
        """Updates the ownership index."""
        # Remove from old
        if old_owner in self._planets_by_owner and planet in self._planets_by_owner[old_owner]:
            self._planets_by_owner[old_owner].remove(planet)
            
        # Add to new
        if new_owner not in self._planets_by_owner:
            self._planets_by_owner[new_owner] = []
        
        if planet not in self._planets_by_owner[new_owner]:
            self._planets_by_owner[new_owner].append(planet)

    def clear(self):
        self._planets.clear()
        self._planets_by_owner.clear()
