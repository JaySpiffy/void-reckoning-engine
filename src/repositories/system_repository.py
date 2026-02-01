from typing import List, Optional, Dict, Any
from src.repositories.base_repository import BaseRepository

class SystemRepository(BaseRepository):
    """Repository for managing star systems."""
    
    def __init__(self):
        self._systems: Dict[str, Any] = {}
        
    def get_by_id(self, entity_id: str) -> Optional[Any]:
        return self._systems.get(entity_id)
        
    def get_all(self) -> List[Any]:
        return list(self._systems.values())
        
    def save(self, entity: Any) -> None:
        self._systems[entity.name] = entity
        
    def delete(self, entity_id: str) -> None:
        if entity_id in self._systems:
            del self._systems[entity_id]

    def clear(self):
        self._systems.clear()
