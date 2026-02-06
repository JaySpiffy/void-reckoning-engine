
import sqlite3
import time
import json
import logging
import threading
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class QueryProfiler:
    def __init__(self):
        self.stats = []
        self.is_active = False

    def start_profiling(self):
        self.is_active = True

    def stop_profiling(self):
        self.is_active = False

    def get_stats(self):
        return self.stats

    def log_query(self, query: str, params: tuple, duration_ms: float, plan: str):
        if not self.is_active: return
        self.stats.append({
            "query": query,
            "params": str(params),
            "duration_ms": duration_ms,
            "plan": plan,
            "timestamp": time.time()
        })
        if len(self.stats) > 1000:
            self.stats.pop(0)

class CacheBackend:
    def get(self, key): pass
    def set(self, key, value): pass
    def delete(self, key): pass
    def clear(self): pass

class MemoryCacheBackend(CacheBackend):
    def __init__(self, max_size=500):
        self.cache = {}
        self.max_size = max_size

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        if len(self.cache) >= self.max_size:
            # Simple eviction
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = value

    def delete(self, key):
        self.cache.pop(key, None)

    def clear(self):
        self.cache.clear()

class RedisCacheBackend(CacheBackend):
    def __init__(self, redis_url):
        import redis
        self.client = redis.from_url(redis_url)

    def get(self, key):
        data = self.client.get(key)
        return json.loads(data) if data else None

    def set(self, key, value):
        self.client.set(key, json.dumps(value))

    def delete(self, key):
        self.client.delete(key)

    def clear(self):
        self.client.flushdb()
