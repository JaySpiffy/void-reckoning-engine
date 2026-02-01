from typing import List, Optional, Dict, Any
from src.repositories.base_repository import BaseRepository
from src.combat.data.data_loader import DataLoader

class UnitRepository(BaseRepository):
    """Repository for unit data, currently backed by DataLoader."""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._is_loaded = False
        
    def _ensure_loaded(self):
        if not self._is_loaded:
            all_units = DataLoader.load_all_units()
            # Flatten into a single dict by blueprint_id or name
            for faction, units in all_units.items():
                for u in units:
                    key = getattr(u, 'blueprint_id', u.name)
                    self._cache[key] = u
            self._is_loaded = True

    def get_by_id(self, entity_id: str) -> Optional[Any]:
        self._ensure_loaded()
        return self._cache.get(entity_id)
    
    def get_all(self) -> List[Any]:
        self._ensure_loaded()
        return list(self._cache.values())
    
    def save(self, entity: Any) -> None:
        key = getattr(entity, 'blueprint_id', entity.name)
        self._cache[key] = entity
    
    def delete(self, entity_id: str) -> None:
        if entity_id in self._cache:
            del self._cache[entity_id]
            
    def get_by_faction(self, faction_name: str) -> List[Any]:
        self._ensure_loaded()
        return [u for u in self._cache.values() if u.faction == faction_name]
