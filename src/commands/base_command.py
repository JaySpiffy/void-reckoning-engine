from abc import ABC, abstractmethod
from typing import Any

class Command(ABC):
    """Base interface for all commands."""
    
    @abstractmethod
    def execute(self) -> Any:
        """Execute command."""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Undo command."""
        pass
    
    @abstractmethod
    def can_execute(self) -> bool:
        """Check if command can be executed."""
        return True
