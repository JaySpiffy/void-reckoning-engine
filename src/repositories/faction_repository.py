from typing import List, Optional, Dict, Any
from src.repositories.base_repository import BaseRepository
from src.models.faction import Faction

class FactionRepository(BaseRepository):
    """Repository for managing Faction entities."""
    
    def __init__(self):
        self._factions: Dict[str, Faction] = {}
        
    def get_by_id(self, entity_id: str) -> Optional[Faction]:
        return self._factions.get(entity_id)
        
    def get_all(self) -> List[Faction]:
        return list(self._factions.values())
        
    def save(self, entity: Faction) -> None:
        self._factions[entity.name] = entity
        
    def delete(self, entity_id: str) -> None:
        if entity_id in self._factions:
            del self._factions[entity_id]
            
    def get_living_factions(self) -> List[Faction]:
        return [f for f in self._factions.values() if f.is_alive]

    def clear(self):
        self._factions.clear()
