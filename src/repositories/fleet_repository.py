from typing import List, Optional, Dict, Any, Set
from src.repositories.base_repository import BaseRepository
from src.models.fleet import Fleet

class FleetRepository(BaseRepository):
    """Repository for managing Fleet entities."""
    
    def __init__(self):
        self._fleets: Dict[str, Fleet] = {}
        self._by_faction: Dict[str, Set[str]] = {} # faction_name -> set of fleet_ids
        
    def get_by_id(self, entity_id: str) -> Optional[Fleet]:
        return self._fleets.get(entity_id)
        
    def get_all(self) -> List[Fleet]:
        return list(self._fleets.values())
        
    def save(self, entity: Fleet) -> None:
        # Use fleet ID if available, otherwise name or identity
        fid = getattr(entity, 'id', str(id(entity)))
        
        # Handle faction change or overwrite
        if fid in self._fleets:
            old_fleet = self._fleets[fid]
            if old_fleet.faction != entity.faction:
                self._remove_from_index(fid, old_fleet.faction)
        
        self._fleets[fid] = entity
        self._add_to_index(fid, entity.faction)
        
    def delete(self, entity_id: str) -> None:
        if entity_id in self._fleets:
            fleet = self._fleets[entity_id]
            self._remove_from_index(entity_id, fleet.faction)
            del self._fleets[entity_id]
            
    def get_by_faction(self, faction_name: str) -> List[Fleet]:
        """Returns all fleets belonging to a faction (Optimized R11)."""
        ids = self._by_faction.get(faction_name, set())
        return [self._fleets[fid] for fid in ids if fid in self._fleets]

    def _add_to_index(self, fid: str, faction: str):
        if faction not in self._by_faction:
            self._by_faction[faction] = set()
        self._by_faction[faction].add(fid)

    def _remove_from_index(self, fid: str, faction: str):
        if faction in self._by_faction:
            self._by_faction[faction].discard(fid)
            if not self._by_faction[faction]:
                del self._by_faction[faction]

    def clear(self):
        self._fleets.clear()
        self._by_faction.clear()
