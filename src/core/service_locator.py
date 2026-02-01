from typing import Any, Optional, Dict
from src.core.di_container import DIContainer

class ServiceLocator:
    """
    Central service locator for accessing managers and services.
    Provides backward compatibility while enabling dependency injection.
    """
    
    _instance: Optional['ServiceLocator'] = None
    _services: Dict[str, Any] = {}
    _di_container: Optional[DIContainer] = None
    
    def __init__(self):
        if ServiceLocator._instance is not None:
            raise RuntimeError("ServiceLocator is a singleton")
        ServiceLocator._instance = self
    
    @classmethod
    def initialize(cls, di_container: Optional[DIContainer] = None) -> None:
        """Initialize with a dependency injection container."""
        cls._instance = cls()
        cls._services = {}
        cls._di_container = di_container if di_container else DIContainer.get_instance()
    
    @classmethod
    def get(cls, service_name: str) -> Any:
        """Get a service by name."""
        if cls._instance is None:
            cls.initialize()
            
        if service_name not in cls._services:
            # Try to resolve from DI container
            if cls._di_container:
                try:
                    service = cls._di_container.get(service_name)
                    cls._services[service_name] = service
                    return service
                except ValueError:
                    pass
            raise ValueError(f"Service '{service_name}' not registered in ServiceLocator or DIContainer")
        return cls._services[service_name]

    @classmethod
    def register(cls, name: str, service: Any) -> None:
        """Manually register a service (for legacy support)."""
        if cls._instance is None:
            cls.initialize()
        cls._services[name] = service
