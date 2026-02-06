
import sqlite3
import threading
import logging
import time
import os
from typing import Optional, Dict, List, Any

from .schema import IndexerSchema
from .cache import QueryProfiler, MemoryCacheBackend, RedisCacheBackend
from .query_manager import QueryManagerMixin
from .event_indexer import EventIndexerMixin

logger = logging.getLogger(__name__)

try:
    import psutil
except ImportError:
    psutil = None

class ReportIndexer(QueryManagerMixin, EventIndexerMixin):
    """
    Core indexing engine for simulation reports.
    Orchestrates ingestion, schema management, and analytical queries.
    """
    def __init__(self, db_path: str, redis_url: Optional[str] = None, enable_profiling: bool = False):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Components
        self.profiler = QueryProfiler()
        self._enable_profiling = enable_profiling
        if enable_profiling:
            self.profiler.start_profiling()
            
        # Cache Init
        try:
            if redis_url:
                self.cache_backend = RedisCacheBackend(redis_url)
            else:
                self.cache_backend = MemoryCacheBackend()
        except:
            self.cache_backend = MemoryCacheBackend()
            
        # Initialize Schema
        IndexerSchema.create_schema(self.conn)
        IndexerSchema.migrate_schema(self.conn)

    @property
    def enable_profiling(self) -> bool:
        return self._enable_profiling

    @enable_profiling.setter
    def enable_profiling(self, value: bool):
        self._enable_profiling = value
        if value: self.profiler.start_profiling()
        else: self.profiler.stop_profiling()

    def _execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Wrapper around cursor.execute() with profiling support."""
        cursor = self.conn.cursor()
        if not self._enable_profiling:
            cursor.execute(query, params)
            return cursor

        start = time.perf_counter()
        plan = ""
        try:
            plan_cursor = self.conn.cursor()
            plan_cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
            plan = "\n".join([str(row) for row in plan_cursor.fetchall()])
        except: plan = "Could not obtain plan"

        cursor.execute(query, params)
        duration = (time.perf_counter() - start) * 1000
        self.profiler.log_query(query, params, duration, plan)
        return cursor

    def get_query_count(self, table: str, where_clause: str, params: list) -> int:
        query = f"SELECT COUNT(*) FROM {table} {where_clause}"
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()[0]

    def get_memory_usage(self) -> Dict[str, float]:
        if psutil is None: return {"rss_mb": 0.0, "vms_mb": 0.0, "percent": 0.0}
        process = psutil.Process()
        mem = process.memory_info()
        return {"rss_mb": mem.rss / 1e6, "vms_mb": mem.vms / 1e6, "percent": process.memory_percent()}

    def vacuum_database(self):
        self.conn.execute("VACUUM")

    def rebuild_fts_index(self):
        self.conn.execute("INSERT INTO events_fts(events_fts) VALUES('rebuild')")

    def analyze_tables(self):
        self.conn.execute("ANALYZE")

    def check_integrity(self):
        return self.conn.execute("PRAGMA integrity_check").fetchall()

    def close(self):
        self.conn.close()

    def set_gold_standard_run(self, universe: str, run_id: str, batch_id: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE runs SET is_gold_standard = 0 WHERE universe = ?", (universe,))
            cursor.execute("UPDATE runs SET is_gold_standard = 1 WHERE universe = ? AND run_id = ? AND batch_id = ?", (universe, run_id, batch_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error setting gold standard: {e}")
            return False

    def clear_gold_standard(self, universe: str) -> bool:
        try:
            self.conn.execute("UPDATE runs SET is_gold_standard = 0 WHERE universe = ?", (universe,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error clearing gold standard: {e}")
            return False

    def _query_cached(self, query: str, params: tuple) -> Any:
        import hashlib
        key = hashlib.md5(f"{query}|{params}".encode()).hexdigest()
        data = self.cache_backend.get(key)
        if data is not None: return data
        
        cursor = self._execute_query(query, params)
        # Convert rows to serializable format
        results = [dict(row) for row in cursor.fetchall()]
        self.cache_backend.set(key, results)
        return results
