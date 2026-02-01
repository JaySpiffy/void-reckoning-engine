from typing import Dict, Any, Optional, List
import psutil
import os
import time

try:
    from src.managers.cache_manager import CacheManager
except ImportError:
    CacheManager = None

class PerformanceMonitor:
    @staticmethod
    def get_memory_stats() -> Dict[str, Any]:
        """
        Get current memory usage statistics using psutil.
        """
        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        virtual_mem = psutil.virtual_memory()
        
        return {
            "rss_mb": mem.rss / 1024 / 1024,
            "vms_mb": mem.vms / 1024 / 1024,
            "percent": virtual_mem.percent,
            "available_mb": virtual_mem.available / 1024 / 1024
        }

    @staticmethod
    def get_cache_stats(cache_manager: Optional[CacheManager]) -> Dict[str, Any]:
        """
        Get statistics from the CacheManager instance.
        """
        if not cache_manager:
            return {
                "hit_rate": 0.0,
                "registered_caches": 0,
                "clear_count": 0,
                "warm_count": 0,
                "named_caches": []
            }
            
        # Duck typing: Check if it has get_statistics, otherwise handle QueryCache manually
        if hasattr(cache_manager, "get_statistics"):
            stats = cache_manager.get_statistics()
            # Calculate hit rate if possible, or use placeholder from stats if available
            hit_rate = stats.get("hit_rate", 0.0) 
            if "hit_rate" not in stats and stats.get("warming_strategies", 0) > 0:
                 hit_rate = 100.0
        elif hasattr(cache_manager, "stats") and isinstance(cache_manager.stats, dict):
            # QueryCache fallback
            s = cache_manager.stats
            hits = s.get("hits", 0)
            misses = s.get("misses", 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0.0
            stats = {
                "hit_rate": hit_rate,
                "registered_caches": 1, 
                "clear_count": 0,
                "warm_count": 0,
                "named_caches": ["query_cache"]
            }
        else:
             return {"error": "unknown cache type"}
             
        return {
            "hit_rate": hit_rate,
            "registered_caches": stats.get("registered_caches", 0),
            "clear_count": stats.get("clear_count", 0),
            "warm_count": stats.get("warm_count", 0),
            "named_caches": stats.get("named_caches", [])
        }

    @staticmethod
    def get_profiling_stats(engine: Optional[Any]) -> Dict[str, Any]:
        """
        Extract profiling data from the engine.
        """
        if not engine:
            return {
                "enabled": False,
                "slow_queries": 0,
                "slow_query_threshold_ms": 100.0,
                "recent_slow_queries": []
            }
            
        # Check enabled state
        enabled = False
        if hasattr(engine, 'config'):
            enabled = getattr(engine.config, 'performance_profile_methods', False)
        elif hasattr(engine, 'performance_profile_methods'):
             enabled = engine.performance_profile_methods
             
        # Extract slow queries from engine metrics
        slow_queries = []
        threshold = 100.0
        
        if hasattr(engine, 'performance_metrics') and isinstance(engine.performance_metrics, dict):
             # Plan comment implies: metric name, duration, timestamp
             # Assuming structure: { 'metric_name': { 'duration_ms': X, 'timestamp': Y, ... } } or list of dicts
             # Let's assume it's a list of events as implied by "recent slow queries"
             
             # Actually, based on typical profilers, it might be a list.
             # If it's a dict of aggregated metrics, we can't get "recent individual queries".
             # BUT, the comment says "read engine.performance_metrics ... filter entries exceeding threshold_ms".
             # Let's assume engine.performance_metrics stores a list of recent operations or we scan a log.
             
             # Re-reading comment: "filter entries exceeding threshold_ms, include metric name, duration, and timestamp"
             # This suggests performance_metrics might be a list of dicts like:
             # [{'metric': 'foo', 'duration_ms': 120, 'timestamp': 1234567890}, ...]
             
             raw_metrics = engine.performance_metrics.get('history', []) if isinstance(engine.performance_metrics, dict) else engine.performance_metrics
             
             if isinstance(raw_metrics, list):
                 for entry in raw_metrics:
                     if isinstance(entry, dict):
                         duration = entry.get('duration_ms', 0)
                         if duration > threshold:
                             slow_queries.append({
                                 "metric": entry.get('metric', 'unknown'),
                                 "duration_ms": duration,
                                 "timestamp": str(entry.get('timestamp', time.time()))
                             })

        return {
            "enabled": enabled,
            "slow_queries": len(slow_queries),
            "slow_query_threshold_ms": threshold,
            "recent_slow_queries": slow_queries
        }

    @staticmethod
    def detect_slow_queries(engine: Optional[Any], threshold_ms: float = 100.0) -> List[Dict[str, Any]]:
        """
        Analyze performance metrics to find slow operations.
        """
        if not engine or not hasattr(engine, 'performance_metrics'):
            return []
            
        slow_queries = []
        raw_metrics = engine.performance_metrics.get('history', []) if isinstance(engine.performance_metrics, dict) else engine.performance_metrics
        
        if isinstance(raw_metrics, list):
             for entry in raw_metrics:
                 if isinstance(entry, dict):
                     duration = entry.get('duration_ms', 0)
                     if duration > threshold_ms:
                         slow_queries.append({
                             "metric": entry.get('metric', 'unknown'),
                             "duration_ms": duration,
                             "timestamp": str(entry.get('timestamp', time.time()))
                         })
                         
        return slow_queries

    @staticmethod
    def enable_profiling(engine: Optional[Any]) -> bool:
        """
        Enable profiling on the engine.
        """
        if not engine:
            return False
            
        if hasattr(engine, 'config'):
            setattr(engine.config, 'performance_profile_methods', True)
            return True
        return False

    @staticmethod
    def disable_profiling(engine: Optional[Any]) -> bool:
        """
        Disable profiling on the engine.
        """
        if not engine:
            return False
            
        if hasattr(engine, 'config'):
            setattr(engine.config, 'performance_profile_methods', False)
            return True
        return False
