from typing import Dict, Callable, List, Any
from src.utils.game_logging import GameLogger

class CacheManager:
    """
    Centralized registry for cache management.
    Allows for clearing all registered caches efficiently at turn end.
    """
    def __init__(self, logger: GameLogger = None):
        self._caches: List[Callable] = []
        self._named_caches: Dict[str, Callable] = {}
        self._warming_strategies: List[Callable] = []
        self.logger = logger
        self._clear_count = 0
        self._warm_count = 0

    def register_cache(self, clear_func: Callable, name: str = None) -> None:
        """
        Registers a cache clearing function.
        clear_func: A callable that clears the specific cache (e.g. lru_cache.cache_clear or dict.clear)
        """
        self._caches.append(clear_func)
        if name:
            self._named_caches[name] = clear_func
            
    def refresh_all(self, engine: Any) -> None:
        """Central turn-boundary hook: Clears then Warms all caches."""
        self.clear_all()
        self.warm_all(engine)
            
    def clear_all(self) -> None:
        """Clears all registered caches."""
        if self.logger:
            self.logger.debug(f"Clearing {len(self._caches)} turn-based caches...")
            
        for func in self._caches:
            try:
                func()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to clear cache: {e}")
                else:
                    print(f"Error clearing cache: {e}")
        
        self._clear_count += 1

    def register_warming_strategy(self, warm_func: Callable) -> None:
        """
        Registers a function for pre-calculating frequently used data.
        warm_func: Callable taking (engine) as argument.
        """
        self._warming_strategies.append(warm_func)

    def warm_all(self, engine: Any) -> None:
        """Executes all registered warming strategies."""
        if self.logger:
             self.logger.debug(f"Warming {len(self._warming_strategies)} system caches...")
             
        for func in self._warming_strategies:
            try:
                func(engine)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to warm cache: {e}")
                    
        self._warm_count += 1

    def get_statistics(self) -> Dict[str, any]:
        """Returns statistics about the cache manager."""
        return {
            "registered_caches": len(self._caches),
            "warming_strategies": len(self._warming_strategies),
            "clear_count": self._clear_count,
            "warm_count": self._warm_count,
            "named_caches": list(self._named_caches.keys())
        }
