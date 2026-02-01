from typing import List, Optional, Dict, Any
from src.repositories.base_repository import BaseRepository
from src.models.fleet import Fleet

class FleetRepository(BaseRepository):
    """Repository for managing Fleet entities."""
    
    def __init__(self):
        self._fleets: Dict[str, Fleet] = {}
        
    def get_by_id(self, entity_id: str) -> Optional[Fleet]:
        return self._fleets.get(entity_id)
        
    def get_all(self) -> List[Fleet]:
        return list(self._fleets.values())
        
    def save(self, entity: Fleet) -> None:
        # Use fleet ID if available, otherwise name or identity
        fid = getattr(entity, 'id', str(id(entity)))
        self._fleets[fid] = entity
        
    def delete(self, entity_id: str) -> None:
        if entity_id in self._fleets:
            del self._fleets[entity_id]
            
    def get_by_faction(self, faction_name: str) -> List[Fleet]:
        return [f for f in self._fleets.values() if f.faction == faction_name]

    def clear(self):
        self._fleets.clear()
