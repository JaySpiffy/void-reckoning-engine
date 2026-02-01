from typing import Any, Callable, Dict, Optional, Type

class DIContainer:
    """Simple dependency injection container."""
    
    _instance: Optional['DIContainer'] = None
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
    
    @classmethod
    def get_instance(cls) -> 'DIContainer':
        if cls._instance is None:
            cls._instance = DIContainer()
        return cls._instance
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance."""
        self._services[name] = instance
        self._singletons[name] = instance
    
    def register_transient(self, name: str, factory: Callable[[], Any]) -> None:
        """Register a transient factory."""
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """Resolve a dependency by name."""
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]
        
        # Check services
        if name in self._services:
            return self._services[name]
        
        # Check factories
        if name in self._factories:
            instance = self._factories[name]()
            return instance
        
        raise ValueError(f"Dependency '{name}' not found in container")
