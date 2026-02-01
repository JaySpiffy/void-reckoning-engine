from abc import ABC, abstractmethod
from typing import List, Optional, Any

class BaseRepository(ABC):
    """Base repository interface."""
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def get_all(self) -> List[Any]:
        pass
    
    @abstractmethod
    def save(self, entity: Any) -> None:
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> None:
        pass
