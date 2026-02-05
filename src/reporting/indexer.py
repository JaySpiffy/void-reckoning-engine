import threading
import sqlite3
import json
import os
import glob
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Setup Logger
logger = logging.getLogger(__name__)

try:
    import psutil
except ImportError:
    psutil = None

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None

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
        self.stats.append({
            "query": query,
            "params": params,
            "duration_ms": duration_ms,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })
        # Cap stats to prevent memory leaks
        if len(self.stats) > 200:
            self.stats = self.stats[-200:]
        # Log to file
        try:
            log_dir = "reports/db"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "query_profile.log"), "a", encoding='utf-8') as f:
                f.write(f"[{datetime.now().isoformat()}] {duration_ms:.2f}ms | Query: {query} | Plan: {plan}\n")
        except:
            pass

# Removed duplicate ReportIndexer definition


class CacheBackend:
    def get(self, key): raise NotImplementedError
    def set(self, key, value): raise NotImplementedError
    def delete(self, key): raise NotImplementedError
    def clear(self): raise NotImplementedError

class MemoryCacheBackend(CacheBackend):
    def __init__(self, max_size=500):
        self.cache = {}
        self.max_size = max_size
    def get(self, key): return self.cache.get(key)
    def set(self, key, value):
        # Basic eviction if full
        if len(self.cache) >= self.max_size:
            # Clear everything or pop first? Pop first is better but dict order varies.
            # Simple approach: clear half if full to avoid frequent re-evictions
            keys = list(self.cache.keys())
            for k in keys[:len(keys)//2]:
                self.cache.pop(k, None)
        self.cache[key] = value
    def delete(self, key): self.cache.pop(key, None)
    def clear(self): self.cache.clear()

class RedisCacheBackend(CacheBackend):
    def __init__(self, redis_url):
        import redis
        self.client = redis.from_url(redis_url)
    def get(self, key):
        data = self.client.get(key)
        return json.loads(data) if data else None
    def set(self, key, value):
        self.client.setex(key, 300, json.dumps(value))
    def delete(self, key): self.client.delete(key)
    def clear(self): self.client.flushdb()

class ReportIndexer:
    """
    Core indexing engine for simulation reports.

    Database Schema:
    - events: Telemetry events with full-text search support
    - factions: Per-turn faction statistics including economic health metrics
      - New columns: upkeep_total, gross_income, net_profit, research_points,
        idle_construction_slots, idle_research_slots
    - battles: Combat engagement summaries
    - runs: Simulation run metadata
    - resource_transactions: Fine-grained economic transaction tracking
      - Tracks income/expense by category (Trade/Tax/Mining/Conquest/Upkeep/etc.)
    - battle_performance: Per-faction battle performance metrics
      - Includes Combat Effectiveness Ratio (CER) and force composition

    Features:
    - Automatic schema migration for backward compatibility
    - FTS5 full-text search on events
    - Pandas integration for analytics
    - Real-time event streaming support
    - Performance-optimized indices for turn-based queries
    """
    def __init__(self, db_path: str, redis_url: Optional[str] = None, enable_profiling: bool = False):
        self.db_path = db_path
        # Ensure DB directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        # Option B: SQLite concurrency safeguards
        self.conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._lock = threading.RLock() # Thread safety
        self._create_schema()
        
        # Init Profiling
        self._enable_profiling = enable_profiling
        self.profiler = QueryProfiler() if enable_profiling else None
        
        # Init Cache
        self.cache = self.QueryCache(redis_url=redis_url)

    @property
    def enable_profiling(self):
        return self._enable_profiling

    @enable_profiling.setter
    def enable_profiling(self, value):
        self._enable_profiling = value
        if value and self.profiler is None:
            self.profiler = QueryProfiler()
        if self.profiler:
            if value:
                self.profiler.start_profiling()
            else:
                self.profiler.stop_profiling()

    def _create_schema(self):
        cursor = self.conn.cursor()
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                universe TEXT,
                run_id TEXT,
                turn INTEGER,
                timestamp TEXT,
                category TEXT,
                event_type TEXT,
                faction TEXT,
                location TEXT,
                entity_type TEXT,
                entity_name TEXT,
                data_json TEXT,
                keywords TEXT
            )
        """)
        
        # Factions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS factions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                universe TEXT,
                run_id TEXT,
                turn INTEGER,
                faction TEXT,
                requisition INTEGER,
                promethium REAL,
                upkeep_total INTEGER DEFAULT 0,
                gross_income INTEGER DEFAULT 0,
                net_profit INTEGER DEFAULT 0,
                research_points INTEGER DEFAULT 0,
                idle_construction_slots INTEGER DEFAULT 0,
                idle_research_slots INTEGER DEFAULT 0,
                planets_controlled INTEGER,
                fleets_count INTEGER,
                units_recruited INTEGER,
                units_lost INTEGER,
                battles_fought INTEGER,
                battles_won INTEGER,
                damage_dealt REAL,
                construction_efficiency REAL DEFAULT 0,
                military_building_count INTEGER DEFAULT 0,
                economy_building_count INTEGER DEFAULT 0,
                research_building_count INTEGER DEFAULT 0,
                research_delta_requisition INTEGER DEFAULT 0,
                data_json TEXT
            )
        """)
        
        # Resource Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                universe TEXT,
                run_id TEXT,
                turn INTEGER,
                faction TEXT,
                category TEXT,
                amount INTEGER,
                source_planet TEXT,
                timestamp TEXT,
                FOREIGN KEY (universe, batch_id, run_id) REFERENCES runs(universe, batch_id, run_id)
            )
        """)

        # Battle Performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                universe TEXT,
                run_id TEXT,
                turn INTEGER,
                battle_id TEXT,
                faction TEXT,
                damage_dealt REAL,
                resources_lost REAL,
                combat_effectiveness_ratio REAL,
                force_composition TEXT,
                attrition_rate REAL,
                timestamp TEXT,
                FOREIGN KEY (universe, batch_id, run_id) REFERENCES runs(universe, batch_id, run_id)
            )
        """)
        
        # Battles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                universe TEXT,
                run_id TEXT,
                turn INTEGER,
                location TEXT,
                factions_involved TEXT,
                winner TEXT,
                duration_rounds INTEGER,
                total_damage REAL,
                units_destroyed INTEGER,
                data_json TEXT
            )
        """)
        
        # Runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                batch_id TEXT,
                universe TEXT,
                run_id TEXT,
                started_at TEXT,
                finished_at TEXT,
                winner TEXT,
                turns_taken INTEGER,
                metadata_json TEXT,
                is_gold_standard BOOLEAN DEFAULT 0,
                PRIMARY KEY (universe, batch_id, run_id)
            )
        """)
        # self.conn.commit()
        # self.conn.execute("ANALYZE")
        
        self.conn.commit()
        self.conn.execute("ANALYZE")
        
        # FTS5 Virtual Table for events
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events_fts'")
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE VIRTUAL TABLE events_fts USING fts5(
                        content='events',
                        content_rowid='id',
                        category,
                        event_type,
                        faction,
                        location,
                        keywords
                    )
                """)
                
                # Triggers to keep FTS in sync
                cursor.execute("""
                    CREATE TRIGGER events_ai AFTER INSERT ON events BEGIN
                      INSERT INTO events_fts(rowid, category, event_type, faction, location, keywords)
                      VALUES (new.id, new.category, new.event_type, new.faction, new.location, new.keywords);
                    END
                """)
                cursor.execute("""
                    CREATE TRIGGER events_ad AFTER DELETE ON events BEGIN
                      INSERT INTO events_fts(events_fts, rowid, category, event_type, faction, location, keywords)
                      VALUES('delete', old.id, old.category, old.event_type, old.faction, old.location, old.keywords);
                    END
                """)
                cursor.execute("""
                    CREATE TRIGGER events_au AFTER UPDATE ON events BEGIN
                      INSERT INTO events_fts(events_fts, rowid, category, event_type, faction, location, keywords)
                      VALUES('delete', old.id, old.category, old.event_type, old.faction, old.location, old.keywords);
                      INSERT INTO events_fts(rowid, category, event_type, faction, location, keywords)
                      VALUES (new.id, new.category, new.event_type, new.faction, new.location, new.keywords);
                    END
                """)
        except sqlite3.OperationalError as e:
            print(f"Warning: FTS5 not available or error creating virtual table: {e}")

        # Migration Step: Ensure new columns exist before creating indices that reference them
        self._migrate_schema()

        # Performance Indices (Step 15)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_gold_standard ON runs(universe, is_gold_standard)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_universe_run_turn ON events(universe, run_id, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_factions_universe_run_turn ON factions(universe, run_id, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_battles_universe_location_turn ON battles(universe, location, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resource_trans_faction_turn ON resource_transactions(faction, universe, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_battle_perf_faction_turn ON battle_performance(faction, universe, turn)")

        # Indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_run ON events(universe, batch_id, run_id, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_faction ON events(faction)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_universe ON events(universe)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_factions_run ON factions(universe, batch_id, run_id, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_battles_run ON battles(universe, batch_id, run_id, turn)")
        
        # Indices for resource_transactions
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resource_transactions_run ON resource_transactions(universe, batch_id, run_id, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resource_transactions_faction ON resource_transactions(faction, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resource_transactions_category ON resource_transactions(category)")

        # Indices for battle_performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_battle_performance_run ON battle_performance(universe, batch_id, run_id, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_battle_performance_faction ON battle_performance(faction, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_battle_performance_battle ON battle_performance(battle_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_battle_perf_attrition ON battle_performance(faction, attrition_rate)")

        # Composite index for economic analysis
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_factions_economic ON factions(faction, turn, gross_income, upkeep_total)")
        
        self.conn.commit()
        
        # Ensure advanced views exist
        self.create_advanced_views()

    def _migrate_schema(self):
        """Ensures existing databases are updated with new columns BEFORE index creation."""
        cursor = self.conn.cursor()
        
        tables = ["events", "factions", "battles", "runs"]
        for table in tables:
            try:
                # Check if table exists first
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    continue

                cursor.execute(f"PRAGMA table_info({table})")
                columns = [info[1] for info in cursor.fetchall()]
                if "universe" not in columns:
                    print(f"  > [DATABASE] Migrating table '{table}': adding 'universe' column")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN universe TEXT")
            except Exception as e:
                print(f"  > [WARNING] Failed to migrate table {table}: {e}")

        # Migration: Add promethium to factions
        try:
            cursor.execute("PRAGMA table_info(factions)")
            columns = {info[1] for info in cursor.fetchall()}
            
            if "promethium" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN promethium REAL")
            if "upkeep_total" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN upkeep_total INTEGER DEFAULT 0")
            if "gross_income" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN gross_income INTEGER DEFAULT 0")
            if "net_profit" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN net_profit INTEGER DEFAULT 0")
            if "research_points" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN research_points INTEGER DEFAULT 0")
            if "idle_construction_slots" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN idle_construction_slots INTEGER DEFAULT 0")
            if "idle_research_slots" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN idle_research_slots INTEGER DEFAULT 0")
            
            # Phase 42b: Industrial & Research Metrics
            if "construction_efficiency" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN construction_efficiency REAL DEFAULT 0")
            if "military_building_count" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN military_building_count INTEGER DEFAULT 0")
            if "economy_building_count" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN economy_building_count INTEGER DEFAULT 0")
            if "research_building_count" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN research_building_count INTEGER DEFAULT 0")
            if "research_delta_requisition" not in columns:
                cursor.execute("ALTER TABLE factions ADD COLUMN research_delta_requisition INTEGER DEFAULT 0")
                
        except Exception as e:
            print(f"  > [WARNING] Failed to migrate factions table: {e}")

        
        # Migration: Add economic health columns to factions
        # (Already handled in previous step)
        
        # Migration: Add is_gold_standard to runs
        try:
            cursor.execute("PRAGMA table_info(runs)")
            columns = {info[1] for info in cursor.fetchall()}
            if "is_gold_standard" not in columns:
                print("  > [DATABASE] Migrating table 'runs': adding 'is_gold_standard' column")
                cursor.execute("ALTER TABLE runs ADD COLUMN is_gold_standard BOOLEAN DEFAULT 0")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_gold_standard ON runs(universe, is_gold_standard)")
        except Exception as e:
            print(f"  > [WARNING] Failed to migrate runs table: {e}")
        new_columns = {
            "upkeep_total": "INTEGER DEFAULT 0",
            "gross_income": "INTEGER DEFAULT 0",
            "net_profit": "INTEGER DEFAULT 0",
            "research_points": "INTEGER DEFAULT 0",
            "idle_construction_slots": "INTEGER DEFAULT 0",
            "idle_research_slots": "INTEGER DEFAULT 0"
        }

        try:
            cursor.execute("PRAGMA table_info(factions)")
            existing_columns = [info[1] for info in cursor.fetchall()]
            
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    print(f"  > [DATABASE] Migrating table 'factions': adding '{col_name}' column")
                    cursor.execute(f"ALTER TABLE factions ADD COLUMN {col_name} {col_type}")
        except Exception as e:
            print(f"  > [WARNING] Failed to migrate factions table for economic columns: {e}")

        # Migration: Ensure resource_transactions table exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resource_transactions'")
            if not cursor.fetchone():
                print("  > [DATABASE] Creating 'resource_transactions' table")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS resource_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id TEXT,
                        universe TEXT,
                        run_id TEXT,
                        turn INTEGER,
                        faction TEXT,
                        category TEXT,
                        amount INTEGER,
                        source_planet TEXT,
                        timestamp TEXT,
                        FOREIGN KEY (universe, batch_id, run_id) REFERENCES runs(universe, batch_id, run_id)
                    )
                """)
        except Exception as e:
            print(f"  > [WARNING] Failed to create resource_transactions table: {e}")

        # Migration: Ensure battle_performance table exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='battle_performance'")
            if not cursor.fetchone():
                print("  > [DATABASE] Creating 'battle_performance' table")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS battle_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id TEXT,
                        universe TEXT,
                        run_id TEXT,
                        turn INTEGER,
                        battle_id TEXT,
                        faction TEXT,
                        damage_dealt REAL,
                        resources_lost REAL,
                        combat_effectiveness_ratio REAL,
                        force_composition TEXT,
                        attrition_rate REAL,
                        timestamp TEXT,
                        FOREIGN KEY (universe, batch_id, run_id) REFERENCES runs(universe, batch_id, run_id)
                    )
                """)
            cursor.execute("PRAGMA table_info(battle_performance)")
            cols = [c[1] for c in cursor.fetchall()]
            if cols and "attrition_rate" not in cols:
                print("  > [DATABASE] Adding 'attrition_rate' column to 'battle_performance'")
                cursor.execute("ALTER TABLE battle_performance ADD COLUMN attrition_rate REAL")
                
        except Exception as e:
            print(f"  > [WARNING] Migration failed for battle_performance: {e}")

        self.conn.commit()

    def index_batch(self, batch_path: str):
        """Crawler for entire batch directory."""
        if not os.path.exists(batch_path):
            print(f"Error: Batch path {batch_path} does not exist.")
            return

        batch_id = os.path.basename(batch_path)
        universe = os.path.basename(os.path.dirname(batch_path)) # reports/universe/batch
        
        run_dirs = [os.path.join(batch_path, d) for d in os.listdir(batch_path) 
                    if os.path.isdir(os.path.join(batch_path, d)) and d.startswith("run_")]
        
        for run_dir in run_dirs:
            self.index_run(run_dir, universe)

    def index_event(self, event: Dict[str, Any], batch_id: str, run_id: str, universe: str = "unknown"):
        """Index a single real-time event."""
        if not event:
            return
            
        with self._lock:
            self._insert_events(batch_id, run_id, [event], universe)
            self.conn.commit()
            
            # Simple cache invalidation on write (could be optimized)
            if hasattr(self, 'cache'):
                self.cache.invalidate()

    def index_run(self, run_path: str, universe: str = "unknown"):
        """Index a single simulation run safely with incremental updates."""
        run_id = os.path.basename(run_path)
        batch_dir = os.path.dirname(run_path)
        batch_id = os.path.basename(batch_dir)
        
        # ONE-TIME INDEXING (Metadata & Logs)
        # We rely on _is_indexed ONLY for the static parts (logs/metadata).
        is_indexed = self._is_indexed(batch_id, run_id, universe)
        print(f"DEBUG_INDEX: Checking is_indexed for {run_id}: {is_indexed}", flush=True)
        if not is_indexed:
            self._insert_run_metadata(batch_id, run_id, run_path, universe)

            # 0. Load Run Manifest
            run_manifest_path = os.path.join(run_path, "manifest.json")
            try:
                 if os.path.exists(run_manifest_path):
                     with open(run_manifest_path, "r", encoding="utf-8") as f:
                         # We could update run metadata here if needed
                         pass 
            except:
                 pass

            # 1. Parse telemetry files
            telemetry_files = glob.glob(os.path.join(run_path, "telemetry_*.json"))
            events_json = os.path.join(run_path, "events.json")
            if os.path.exists(events_json):
                telemetry_files.append(events_json)
                
            for tel_file in telemetry_files:
                events = self._parse_telemetry_file(tel_file)
                if events:
                    self._insert_events(batch_id, run_id, events, universe)
            
            # 2.5 Index Full Campaign Log (Or Campaign JSON)
            try:
                log_path = os.path.join(run_path, "full_campaign_log.txt")
                if os.path.exists(log_path):
                    self._index_text_log(batch_id, run_id, log_path, universe=universe)
                else:
                    json_log_path = os.path.join(run_path, "campaign.json")
                    if os.path.exists(json_log_path):
                        self._index_text_log(batch_id, run_id, json_log_path, universe=universe)
            except Exception as e:
                pass
        else:
            # SAFETY CHECK: Run is 'indexed', but did we miss the galaxy data?
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1 FROM events WHERE run_id=? AND event_type='galaxy_generated'", (run_id,))
                has_galaxy = cursor.fetchone() is not None
                
                if not has_galaxy:
                    # WARNING: excessive re-indexing causes timeouts. Temporarily disabled auto-reindex.
                    print(f"DEBUG_INDEX: Run {run_id} indexed but missing galaxy data. Skipping forced re-index to prevent lock.", flush=True)
                    # json_log_path = os.path.join(run_path, "campaign.json")
                    # if os.path.exists(json_log_path):
                    #     self._index_text_log(batch_id, run_id, json_log_path, universe=universe)
            except Exception as e:
                print(f"DEBUG_INDEX: Error in galaxy data safety check: {e}", flush=True)

        # INCREMENTAL UPDATE (Turns: Factions, Battles)
        existing_turns = set()
        try:
            rows = self.conn.execute("SELECT DISTINCT turn FROM factions WHERE run_id=?", (run_id,)).fetchall()
            existing_turns = {r[0] for r in rows}
        except:
            pass

        turn_dirs = [os.path.join(run_path, d) for d in os.listdir(run_path) 
                     if os.path.isdir(os.path.join(run_path, d)) and d.startswith("turn_")]
        
        max_turn = 0
        updated_state = False
        
        for turn_dir in turn_dirs:
            try:
                turn_num = int(os.path.basename(turn_dir).split("_")[1])
                max_turn = max(max_turn, turn_num)
                
                if turn_num in existing_turns:
                    continue # Skip already indexed
                
                updated_state = True
                
                # Factions (Legacy: Nested)
                factions_root = os.path.join(turn_dir, "factions")
                if os.path.exists(factions_root):
                    for f_name in os.listdir(factions_root):
                        f_summary_path = os.path.join(factions_root, f_name, "summary.json")
                        if os.path.exists(f_summary_path):
                            faction_data = self._parse_faction_summary(f_summary_path)
                            if faction_data:
                                self._insert_faction_stats(batch_id, run_id, turn_num, faction_data, universe)
                
                # Battles (Legacy: Nested)
                battles_root = os.path.join(turn_dir, "battles")
                if os.path.exists(battles_root):
                    combat_logs = glob.glob(os.path.join(battles_root, "Combat_T*.json"))
                    for combat_log in combat_logs:
                        battle_data = self._parse_combat_log(combat_log)
                        if battle_data:
                            self._insert_battle(batch_id, run_id, turn_num, battle_data, universe)
                            
            except (IndexError, ValueError):
                continue

        # MODERM: Scan root factions/ and battles/ directories
        import re
        
        # 1. Root Factions
        root_factions_dir = os.path.join(run_path, "factions")
        if os.path.exists(root_factions_dir):
            for f_file in os.listdir(root_factions_dir):
                if f_file.endswith(".json") and "_turn_" in f_file:
                    match = re.search(r"_turn_(\d+)\.json", f_file)
                    if match:
                        turn_num = int(match.group(1))
                        max_turn = max(max_turn, turn_num)
                        
                        f_path = os.path.join(root_factions_dir, f_file)
                        faction_data = self._parse_faction_summary(f_path)
                        if faction_data:
                            # Use IGNORE to avoid double indexing if legacy also found it
                            try:
                                self._insert_faction_stats(batch_id, run_id, turn_num, faction_data, universe)
                                updated_state = True
                            except sqlite3.IntegrityError:
                                pass # Already indexed

        # 2. Root Battles
        root_battles_dir = os.path.join(run_path, "battles")
        if os.path.exists(root_battles_dir):
            combat_logs = glob.glob(os.path.join(root_battles_dir, "Combat_T*.json"))
            for combat_log in combat_logs:
                # Combat_T001_p_Aurelia.json
                match = re.search(r"Combat_T(\d+)", os.path.basename(combat_log))
                if match:
                    turn_num = int(match.group(1))
                    max_turn = max(max_turn, turn_num)
                    
                    battle_data = self._parse_combat_log(combat_log)
                    if battle_data:
                        try:
                            self._insert_battle(batch_id, run_id, turn_num, battle_data, universe)
                            updated_state = True
                        except sqlite3.IntegrityError:
                            pass # Already indexed
        
        # 3. Finalize run entry (Updates status/turns)
        # Load metadata only if updated or needed
        run_manifest_path = os.path.join(run_path, "manifest.json")
        run_metadata = {}
        try:
             if os.path.exists(run_manifest_path):
                 with open(run_manifest_path, "r", encoding="utf-8") as f:
                     run_metadata = json.load(f)
        except:
             pass

        summary = run_metadata.get("summary", {})
        self._insert_run_info(
            batch_id, 
            run_id, 
            run_path, 
            max_turn,
            started_at=run_metadata.get("started_at"),
            finished_at=run_metadata.get("finished_at"),
            winner=summary.get("winner"),
            turns_taken=summary.get("turns_taken") or max_turn,
            metadata=run_metadata.get("metadata", {}),
            universe=universe
        )
        
        self.conn.commit()
        if hasattr(self, 'cache'):
            self.cache.invalidate()

    def _is_indexed(self, batch_id: str, run_id: str, universe: str) -> bool:
        """Check if a run is already indexed."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM runs WHERE batch_id = ? AND run_id = ? AND universe = ?", (batch_id, run_id, universe))
        return cursor.fetchone() is not None

    def _parse_telemetry_file(self, path: str) -> List[Dict[str, Any]]:
        events = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error parsing telemetry {path}: {e}")
        return events

    def _parse_faction_summary(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error parsing faction summary {path}: {e}")
            return None

    def _parse_combat_log(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error parsing combat log {path}: {e}")
            return None

    def _extract_keywords(self, event: Dict[str, Any]) -> str:
        words = []
        words.append(str(event.get("event_type", "")))
        words.append(str(event.get("category", "")))
        
        if event.get("faction"):
            words.append(str(event["faction"]))
            
        data = event.get("data", {})
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, str):
                    words.append(v)
                elif isinstance(v, (list, tuple)):
                    for item in v:
                        if isinstance(item, str):
                            words.append(item)
                        
        return " ".join(set([w for w in words if w]))

    def _index_text_log(self, batch_id: str, run_id: str, log_path: str, universe: str = "unknown"):
        """
        Indexes lines from the full campaign log.
        Supports 'Hybrid Mode': If a line is valid JSON and contains 'event_type', 
        it is indexed as a structured event. Otherwise, it is indexed as a text log.
        """
        events_to_insert = []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    
                    # Hybrid Parsing Logic
                    is_structured = False
                    structured_event = {}
                    
                    # Try to parse as JSON first
                    try:
                        json_data = json.loads(line)
                        if isinstance(json_data, dict):
                            # Case A: Direct Telemetry Format (Top-level event_type)
                            if "event_type" in json_data:
                                is_structured = True
                                structured_event = json_data
                            
                            # Case B: GameLogger Format (event_type valid in context)
                            elif "context" in json_data and isinstance(json_data["context"], dict):
                                ctx = json_data["context"]
                                
                                # Deep search for event_type in ctx or ctx['extra']
                                event_type = ctx.get("event_type")
                                extra = ctx.get("extra", {})
                                if not event_type and isinstance(extra, dict):
                                    event_type = extra.get("event_type")
                                
                                if event_type:
                                    is_structured = True
                                    # Flatten for consistent handling
                                    structured_event = json_data.copy()
                                    structured_event["event_type"] = event_type
                                    # Use context data if available, else empty dict
                                    structured_event["data"] = ctx.get("data", extra.get("data", {}))
                                    # Prefer context values for specific fields as they are more granular
                                    if "faction" in ctx: structured_event["faction"] = ctx["faction"]
                                    elif "faction" in extra: structured_event["faction"] = extra["faction"]
                                    
                                    if "category" in ctx: 
                                        structured_event["category"] = ctx["category"]
                                    elif "event_category" in ctx:
                                        structured_event["category"] = ctx["event_category"]
                                    elif "category" in extra:
                                        structured_event["category"] = extra["category"]
                                        
                                    if "location" in ctx: structured_event["location"] = ctx["location"]
                                    elif "location" in extra: structured_event["location"] = extra["location"]
                                    
                                    # Timestamp and turn usually match top-level but ensure availability
                                    if "turn" in ctx and structured_event.get("turn") is None:
                                        structured_event["turn"] = ctx["turn"]
                                    elif "turn" in extra and structured_event.get("turn") is None:
                                        structured_event["turn"] = extra["turn"]
                            
                            # Case C: JSON embedded in message (Common in legacy logs)
                            if not is_structured and "message" in json_data and isinstance(json_data["message"], str):
                                msg = json_data["message"]
                                if msg.startswith("{") and msg.endswith("}"):
                                    try:
                                        nested_json = json.loads(msg)
                                        if isinstance(nested_json, dict) and "event_type" in nested_json:
                                            is_structured = True
                                            structured_event = nested_json
                                            if "timestamp" not in structured_event:
                                                structured_event["timestamp"] = json_data.get("timestamp")
                                    except: pass

                    except json.JSONDecodeError:
                        pass
                    
                    if is_structured:
                         # Map JSON fields to Event Schema
                         # Loggers usually output: timestamp, level, message, event_type, data
                         
                         # Data extraction: prefer 'data' dict, else use whole object
                         payload = structured_event.get("data", structured_event)
                         
                         events_to_insert.append({
                            "batch_id": batch_id,
                            "universe": universe,
                            "run_id": run_id,
                            "turn": structured_event.get("turn"), # Might be null
                            "timestamp": structured_event.get("timestamp"),
                            "category": structured_event.get("category", "log"),
                            "event_type": structured_event.get("event_type", "text_log"),
                            "faction": structured_event.get("faction"),
                            "location": structured_event.get("location"),
                            "entity_type": structured_event.get("entity_type"),
                            "entity_name": structured_event.get("entity_name"),
                            "data_json": json.dumps(payload),
                            "keywords": self._extract_keywords(structured_event)
                         })
                    else:
                        # Fallback to Text Log
                        events_to_insert.append({
                            "batch_id": batch_id,
                            "universe": universe, 
                            "run_id": run_id,
                            "turn": None,
                            "timestamp": None,
                            "category": "log",
                            "event_type": "text_log",
                            "faction": None,
                            "location": None,
                            "entity_type": None,
                            "entity_name": None,
                            "data_json": json.dumps({"text": line}),
                            "keywords": line
                        })
                    
                    if len(events_to_insert) >= 500:
                        self._bulk_insert_pseudo_events(events_to_insert, universe)
                        events_to_insert = []
                        
            if events_to_insert:
                self._bulk_insert_pseudo_events(events_to_insert, universe)
        except Exception as e:
            print(f"Error indexing text log {log_path}: {e}")

    def _bulk_insert_pseudo_events(self, events: List[Dict[str, Any]], universe: str = "unknown"):
        cursor = self.conn.cursor()
        batch_data = [(
            e["batch_id"], e.get("universe", universe), e["run_id"], e["turn"], e["timestamp"],
            e["category"], e["event_type"], e["faction"], e["location"],
            e["entity_type"], e["entity_name"], e["data_json"], e["keywords"]
        ) for e in events]
        
        cursor.executemany("""
            INSERT INTO events (
                batch_id, universe, run_id, turn, timestamp, category, event_type, 
                faction, location, entity_type, entity_name, data_json, keywords
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)

    def index_realtime_events(self, batch_id: str, run_id: str, events: List[Dict[str, Any]], universe: str):
        """Public wrapper for real-time event ingestion."""
        if not events: return
        try:
            self._insert_events(batch_id, run_id, events, universe)
            self.conn.commit()
        except Exception as e:
            print(f"Error indexing realtime events: {e}")

    def index_realtime_resource_transactions(self, batch_id: str, run_id: str, 
                                              transactions: List[Dict[str, Any]], universe: str):
        """Public wrapper for real-time resource transaction ingestion."""
        if not transactions: return
        try:
            with self._lock:
                self._bulk_insert_resource_transactions(transactions, universe)
                self.conn.commit()
        except Exception as e:
            print(f"Error indexing realtime resource transactions: {e}")

    def index_realtime_battle_performance(self, batch_id: str, run_id: str,
                                           performances: List[Dict[str, Any]], universe: str):
        """Public wrapper for real-time battle performance ingestion."""
        if not performances: return
        try:
            with self._lock:
                self._bulk_insert_battle_performance(performances, universe)
                self.conn.commit()
        except Exception as e:
            print(f"Error indexing realtime battle performance: {e}")

    def _insert_events(self, batch_id: str, run_id: str, events: List[Dict[str, Any]], universe: str):
        cursor = self.conn.cursor()
        batch_data = []
        resource_transactions = []
        battles = []
        
        for e in events:
            data = e.get("data", {})
            if not isinstance(data, dict):
                data = {"raw": data}
            
            # 1. Prepare Generic Event Data
            batch_data.append((
                batch_id,
                universe,
                run_id,
                e.get("turn"),
                e.get("timestamp"),
                e.get("category"),
                e.get("event_type"),
                e.get("faction"),
                data.get("location") or data.get("planet") or data.get("system"),
                data.get("entity_type"),
                data.get("entity_name") or data.get("unit") or data.get("fleet"),
                json.dumps(data),
                self._extract_keywords(e)
            ))

            # 2. Route to specialized tables
            event_type = e.get("event_type")
            
            # Economics & Construction
            if event_type in ["income_collected", "construction_started", "construction_complete", "research_complete", "unit_recruited"]:
                amount = 0
                cat = "other"
                
                if event_type == "income_collected":
                    breakdown = data.get("breakdown", {})
                    if breakdown:
                        for b_cat, b_amt in breakdown.items():
                             if b_amt > 0:
                                 # Normalize category casing
                                 norm_cat = b_cat.title() if isinstance(b_cat, str) else str(b_cat)
                                 resource_transactions.append({
                                    "batch_id": batch_id,
                                    "universe": universe,
                                    "run_id": run_id,
                                    "turn": e.get("turn"),
                                    "faction": e.get("faction"),
                                    "category": norm_cat, 
                                    "amount": b_amt,
                                    "source_planet": data.get("planet") or data.get("location"),
                                    "timestamp": e.get("timestamp")
                                })
                        # Don't add base 'income' if breakdown exists to avoid double counting
                        amount = 0 
                    else:
                        amount = data.get("net", 0)
                        cat = "Income"

                elif event_type in ["construction_started", "construction_complete"]:
                    amount = -data.get("cost", 0) # Cost is negative
                    cat = "Construction"
                elif event_type == "research_complete":
                     amount = -data.get("cost", 0)
                     cat = "Research"
                elif event_type == "unit_recruited":
                    amount = -data.get("cost", 0)
                    cat = "Recruitment"

                if amount != 0:
                    resource_transactions.append({
                        "batch_id": batch_id,
                        "universe": universe,
                        "run_id": run_id,
                        "turn": e.get("turn"),
                        "faction": e.get("faction"),
                        "category": cat,
                        "amount": amount,
                        "source_planet": data.get("planet") or data.get("location"),
                        "timestamp": e.get("timestamp")
                    })

            # Battles
            elif event_type == "battle_end" or event_type == "combat_finished":
                # Ensure data has necessary summary fields before inserting
                 if "summary" in data:
                     self._insert_battle(batch_id, run_id, e.get("turn"), data, universe)

            # Detailed Faction Stats (New Source of Truth)
            elif event_type == "faction_stats":
                self._insert_faction_stats(batch_id, run_id, e.get("turn"), data, universe)

            # Direct Resource Transactions (New Telemetry)
            elif event_type == "resource_transaction":
                raw_cat = data.get("category", "Other")
                norm_cat = raw_cat.title() if isinstance(raw_cat, str) else str(raw_cat)
                resource_transactions.append({
                    "batch_id": batch_id,
                    "universe": universe,
                    "run_id": run_id,
                    "turn": e.get("turn"),
                    "faction": e.get("faction"),
                    "category": norm_cat,
                    "amount": data.get("amount"),
                    "source_planet": data.get("planet") or data.get("location"),
                    "timestamp": e.get("timestamp")
                })

        # Bulk Insert Generic Events
        cursor.executemany("""
            INSERT INTO events (
                batch_id, universe, run_id, turn, timestamp, category, event_type, 
                faction, location, entity_type, entity_name, data_json, keywords
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)
        
        # Bulk Insert Resource Transactions
        if resource_transactions:
            self._bulk_insert_resource_transactions(resource_transactions, universe)

    def _insert_faction_stats(self, batch_id: str, run_id: str, turn: int, data: Dict[str, Any], universe: str):
        cursor = self.conn.cursor()
        
        econ = data.get("economy", {})
        mil = data.get("military", {})
        terr = data.get("territory", {})
        deltas = data.get("deltas", {})
        
        # New Telemetry Data Extraction
        construction = data.get("construction_activity", {})
        research = data.get("research_impact", {})
        tech_data = data.get("tech_depth", {})
        
        # Extract metrics
        idle_slots = construction.get("avg_idle_slots", 0)
        research_points = tech_data.get("unlocked_count", 0) if tech_data else econ.get("research_points", 0)
        
        # New Metrics
        const_efficiency = construction.get("avg_queue_efficiency", 0.0)
        b_types = construction.get("building_types", {})
        mil_b = b_types.get("Military", 0)
        eco_b = b_types.get("Economy", 0)
        res_b = b_types.get("Research", 0)
        
        res_delta_req = research.get("latest_deltas", {}).get("requisition", 0)

        cursor.execute("""
            INSERT INTO factions (
                batch_id, universe, run_id, turn, faction, requisition, promethium,
                upkeep_total, gross_income, net_profit, research_points,
                idle_construction_slots, idle_research_slots,
                planets_controlled, fleets_count, units_recruited, units_lost,
                battles_fought, battles_won, damage_dealt, 
                construction_efficiency, military_building_count, 
                economy_building_count, research_building_count, 
                research_delta_requisition,
                data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, universe, run_id, turn, data.get("faction"),
            deltas.get("requisition", 0),
            econ.get("promethium", 0),
            econ.get("upkeep_total", 0),
            econ.get("gross_income", 0),
            econ.get("net_profit", 0),
            research_points,
            int(idle_slots),
            econ.get("idle_research_slots", 0),
            terr.get("total_controlled", 0),
            deltas.get("fleets_count", 0),
            mil.get("units_recruited", 0),
            mil.get("units_lost", 0),
            mil.get("battles_fought", 0),
            mil.get("battles_won", 0),
            mil.get("damage_dealt", 0),
            const_efficiency, mil_b, eco_b, res_b, res_delta_req,
            json.dumps(data)
        ))

    def _insert_battle(self, batch_id: str, run_id: str, turn: int, data: Dict[str, Any], universe: str):
        cursor = self.conn.cursor()
        summary = data.get("summary", {})
        
        factions = list(summary.get("factions", {}).keys())
        total_dmg = sum(f.get("damage", 0) for f in summary.get("factions", {}).values())
        
        cursor.execute("""
            INSERT INTO battles (
                batch_id, universe, run_id, turn, location, factions_involved,
                winner, duration_rounds, total_damage, units_destroyed, data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id,
            universe,
            run_id,
            turn,
            data.get("location") or data.get("planet"),
            ",".join(factions),
            summary.get("winner"),
            summary.get("total_rounds"),
            total_dmg,
            summary.get("total_kills"),
            json.dumps(data)
        ))

        # KEY FIX: Also populate battle_performance for each participating faction
        battle_id = data.get("id", f"BATTLE_{turn}_{run_id[-4:]}")
        factions_involved = summary.get("factions", {})
        
        for f_name, f_stats in factions_involved.items():
            try:
                # Calculate combat performance metrics
                # Structure: {"damage": X, "losses": Y, "force": {...}}
                damage = f_stats.get("damage", 0.0)
                losses = f_stats.get("losses", 0.0)
                composition = f_stats.get("force", {})
                
                # Simple attrition rate
                total_force = sum(composition.values()) if composition else 1
                attrition = losses / total_force if total_force > 0 else 0.0
                
                # CE ratio (simple damage/losses ratio or similar)
                # Normalizing damage vs losses
                cer = damage / max(1, losses) 
                
                self._insert_battle_performance(
                    batch_id=batch_id,
                    run_id=run_id,
                    turn=turn,
                    battle_id=battle_id,
                    faction=f_name,
                    damage_dealt=damage,
                    resources_lost=losses,
                    force_composition=composition,
                    attrition_rate=attrition,
                    universe=universe
                )
            except Exception as e:
                print(f"ERROR: Failed to insert performance for {f_name}: {e}", flush=True)


    def _insert_resource_transaction(self, batch_id: str, run_id: str, turn: int, 
                                      faction: str, category: str, amount: int, 
                                      source_planet: str = None, universe: str = "unknown"):
        """Insert a resource transaction record for economic tracking."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO resource_transactions (
                batch_id, universe, run_id, turn, faction, category, 
                amount, source_planet, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id,
            universe,
            run_id,
            turn,
            faction,
            category,
            amount,
            source_planet,
            datetime.now().isoformat()
        ))

    def _bulk_insert_resource_transactions(self, transactions: List[Dict[str, Any]], universe: str = "unknown"):
        """Bulk insert resource transactions for better performance."""
        cursor = self.conn.cursor()
        batch_data = [(
            t["batch_id"], universe, t["run_id"], t["turn"], t["faction"],
            t["category"], t["amount"], t.get("source_planet"), 
            t.get("timestamp", datetime.now().isoformat())
        ) for t in transactions]
        
        cursor.executemany("""
            INSERT INTO resource_transactions (
                batch_id, universe, run_id, turn, faction, category,
                amount, source_planet, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)

    def _insert_battle_performance(self, batch_id: str, run_id: str, turn: int,
                                    battle_id: str, faction: str, damage_dealt: float,
                                    resources_lost: float, force_composition: Dict[str, int],
                                    attrition_rate: float = 0.0, universe: str = "unknown"):
        """Insert battle performance metrics for military analysis."""
        cursor = self.conn.cursor()
        
        # Calculate Combat Effectiveness Ratio (CER)
        cer = damage_dealt / resources_lost if resources_lost > 0 else 0.0
        
        cursor.execute("""
            INSERT INTO battle_performance (
                batch_id, universe, run_id, turn, battle_id, faction,
                damage_dealt, resources_lost, combat_effectiveness_ratio,
                force_composition, attrition_rate, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id,
            universe,
            run_id,
            turn,
            battle_id,
            faction,
            damage_dealt,
            resources_lost,
            cer,
            json.dumps(force_composition),
            attrition_rate,
            datetime.now().isoformat()
        ))

    def _bulk_insert_battle_performance(self, performances: List[Dict[str, Any]], universe: str = "unknown"):
        """Bulk insert battle performance records."""
        cursor = self.conn.cursor()
        batch_data = []
        
        for p in performances:
            cer = p["damage_dealt"] / p["resources_lost"] if p["resources_lost"] > 0 else 0.0
            batch_data.append((
                p["batch_id"], universe, p["run_id"], p["turn"], p["battle_id"],
                p["faction"], p["damage_dealt"], p["resources_lost"], cer,
                json.dumps(p["force_composition"]), 
                p.get("attrition_rate", 0.0),
                p.get("timestamp", datetime.now().isoformat())
            ))
        
        cursor.executemany("""
            INSERT INTO battle_performance (
                batch_id, universe, run_id, turn, battle_id, faction,
                damage_dealt, resources_lost, combat_effectiveness_ratio,
                force_composition, attrition_rate, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)

    def _insert_run_metadata(self, batch_id: str, run_id: str, run_path: str, universe: str = "unknown"):
        """Initial insertion of run metadata to ensure primary key existence."""
        cursor = self.conn.cursor()
        
        # Check if already exists to avoid overwriting start time if called multiple times
        cursor.execute("SELECT 1 FROM runs WHERE universe = ? AND run_id = ? AND batch_id = ?", (universe, run_id, batch_id))
        if cursor.fetchone():
            return

        cursor.execute("""
            INSERT INTO runs (
                batch_id, universe, run_id, started_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            batch_id,
            universe,
            run_id,
            datetime.now().isoformat(),
            json.dumps({"path": run_path})
        ))
        # self.conn.commit() # Commit handled by caller or bulk operation

    def _insert_run_info(self, batch_id: str, run_id: str, run_path: str, max_turn: int, 
                        started_at=None, finished_at=None, winner=None, turns_taken=None, metadata=None, universe: str = "unknown"):
        cursor = self.conn.cursor()
        
        # Metadata
        meta = {"path": run_path}
        if metadata:
            meta.update(metadata)
            
        # Priority: Passed arg > Metadata > Default
        final_universe = universe
        if not final_universe or final_universe == "unknown":
            if metadata:
                final_universe = metadata.get("universe", "unknown")
        
        cursor.execute("""
            INSERT OR REPLACE INTO runs (
                batch_id, universe, run_id, started_at, finished_at, winner, turns_taken, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id,
            final_universe,
            run_id,
            started_at or datetime.now().isoformat(), 
            finished_at or datetime.now().isoformat(),
            winner, 
            turns_taken if turns_taken is not None else max_turn,
            json.dumps(meta)
        ))

    # --- Analytics Queries ---

    def create_analytics_views(self):
        """Creates SQL views for common analytics queries."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS faction_performance_summary AS
            SELECT faction, universe, 
                   AVG(requisition) as avg_req,
                   MAX(planets_controlled) as peak_planets,
                   SUM(battles_won) as total_wins,
                   SUM(battles_fought) as total_battles
            FROM factions
            GROUP BY faction, universe;
        """)
        self.conn.commit()

    def get_query_count(self, table: str, where_clause: str, params: list) -> int:
        """Helper method that runs SELECT COUNT(*) with same filters."""
        query = f"SELECT COUNT(*) FROM {table} {where_clause}"
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()[0]

    def _execute_query(self, query: str, params: Any = ()) -> sqlite3.Cursor:
        """Wrapper around cursor.execute() with profiling logic."""
        cursor = self.conn.cursor()
        if not getattr(self, 'enable_profiling', False):
            cursor.execute(query, params)
            return cursor

        start = time.perf_counter()
        # Get query plan
        plan = ""
        try:
            plan_cursor = self.conn.cursor()
            plan_cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
            plan = "\n".join([str(row) for row in plan_cursor.fetchall()])
        except:
            plan = "Could not obtain plan"

        cursor.execute(query, params)
        duration = (time.perf_counter() - start) * 1000
        if self.profiler:
            self.profiler.log_query(query, params, duration, plan)
        return cursor

    def get_memory_usage(self) -> Dict[str, float]:
        """Track memory consumption (Step 14)."""
        if psutil is None:
            return {"rss_mb": 0.0, "vms_mb": 0.0, "percent": 0.0}
            
        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            "rss_mb": mem_info.rss / 1024 / 1024,
            "vms_mb": mem_info.vms / 1024 / 1024,
            "percent": process.memory_percent()
        }

    def query_faction_time_series(self, faction: str, universe: str, metrics: List[str], page: Optional[int] = None, page_size: int = 100) -> Any:
        """Returns time-series data for a faction as a DataFrame."""
        cols = ", ".join(metrics)
        where_clause = "WHERE faction = ? AND universe = ?"
        params = [faction, universe]
        
        query = f"SELECT turn, {cols} FROM factions {where_clause} ORDER BY turn"
        
        if page is not None:
            total_count = self.get_query_count("factions", where_clause, params)
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"
            
            # For time series, we often want the full DF for analytics, 
            # but if paginated, we return a dict
            df = pd.read_sql_query(query, self.conn, params=params)
            return {
                "data": df.to_dict(orient='records'),
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        try:
            if pd is None: return None
            return pd.read_sql_query(query, self.conn, params=params)
        except Exception as e:
            print(f"Error querying time series: {e}")
            if pd: return pd.DataFrame()
            return None

    def query_battle_statistics(self, universe: str) -> 'pd.DataFrame':
        """Returns aggregated battle statistics."""
        query = """
            SELECT turn, location as planet, duration_rounds as rounds, total_damage, units_destroyed, winner
            FROM battles
            WHERE universe = ?
            ORDER BY turn
        """
        try:
            if pd is None: return None
            return pd.read_sql_query(query, self.conn, params=(universe,))
        except Exception as e:
            print(f"Error querying battle stats: {e}")
            if pd: return pd.DataFrame()
            return None

    def query_latest_faction_stats(self, universe: str) -> 'pd.DataFrame':
        """Returns the latest stats for all factions in the universe."""
        query = """
            SELECT faction, planets_controlled, requisition, battles_won
            FROM factions
            WHERE universe = ? AND turn = (SELECT MAX(turn) FROM factions WHERE universe = ?)
        """
        try:
            if pd is None: return None
            return pd.read_sql_query(query, self.conn, params=(universe, universe))
        except Exception as e:
            if pd: return pd.DataFrame()
            return None
            
    def query_faction_snapshot(self, faction: str, universe: str, turn: int) -> Dict[str, Any]:
        """Returns a single snapshot dict for ML input."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT planets_controlled, requisition, fleets_count, battles_won
            FROM factions
            WHERE faction = ? AND universe = ? AND turn = ?
        """, (faction, universe, turn))
        row = cursor.fetchone()
        if not row: return {}
        return {
            "planets_controlled": row[0],
            "requisition": row[1],
            "military_power": row[2] * 1000, # Proxy logic
            "tech_count": 0 # Not tracked in factions table yet, would need Events query
        }

    def query_tech_progression(self, faction: str, universe: str, run_id: str = None) -> 'pd.DataFrame':
        """Aggregates tech unlocks per turn."""
        # Note: Using events_fts for partial match on 'unlock' if needed, or exact match on category 'technology'
        
        params = [faction, universe]
        filter_clause = ""
        if run_id:
            filter_clause = "AND run_id = ?"
            params.append(run_id)
            
        query = f"""
            SELECT turn, COUNT(*) as tech_unlocks
            FROM events
            WHERE faction = ? AND universe = ? {filter_clause} AND event_type LIKE '%unlock%'
            GROUP BY turn
            ORDER BY turn
        """
        try:
            if pd is None: return None
            df = pd.read_sql_query(query, self.conn, params=tuple(params))
            if not df.empty:
                df['cumulative_techs'] = df['tech_unlocks'].cumsum()
            return df
        except Exception as e:
            if pd: return pd.DataFrame()
            return None

    def query_ai_action_patterns(self, faction: str, universe: str) -> 'pd.DataFrame':
        """Aggregates event types to analyze AI behavior patterns."""
        query = """
            SELECT turn, event_type, COUNT(*) as count
            FROM events
            WHERE faction = ? AND universe = ? 
            AND event_type IN ('construction_complete', 'unit_recruited', 'diplomacy_action', 'fleet_move')
            GROUP BY turn, event_type
            ORDER BY turn
        """
        try:
            if pd is None: return None
            df = pd.read_sql_query(query, self.conn, params=(faction, universe))
            if df.empty: return df
            # Pivot for easier Z-score analysis: index=turn, columns=event_type
            return df.pivot(index='turn', columns='event_type', values='count').fillna(0)
        except Exception as e:
            if pd: return pd.DataFrame()
            return None

    def query_portal_usage(self, universe: str) -> 'pd.DataFrame':
        """Tracks portal transit events."""
        query = """
            SELECT turn, faction, location, 1 as count
            FROM events
            WHERE universe = ? AND event_type = 'portal_transit'
        """
        try:
            if pd is None: return None
            return pd.read_sql_query(query, self.conn, params=(universe,))
        except Exception as e:
            if pd: return pd.DataFrame()
            return None

    def index_realtime_events(self, batch_id: str, run_id: str, events: List[Dict[str, Any]], universe: str):
        """Public wrapper for real-time event ingestion."""
        if not events: return
        try:
            with self._lock:
                self._insert_events(batch_id, run_id, events, universe)
                self.conn.commit()
        except Exception as e:
            print(f"Error indexing realtime events: {e}")

    def query_telemetry(
        self, 
        run_id: Optional[str] = None,
        category: Optional[str] = None, 
        event_type: Optional[str] = None,
        faction: Optional[Any] = None,
        universe: Optional[str] = None,
        limit: Optional[int] = None,
        batch_id: Optional[str] = None,
        turn_range: Optional[tuple] = None,
        page: Optional[int] = None,
        page_size: int = 100
    ) -> Any:
        """
        Generic telemetry query method supporting dynamic filtering.
        Wrapper around raw SQL query on the events table.
        """
        conditions = []
        params = []
        
        if batch_id and batch_id != "unknown":
            conditions.append("batch_id = ?")
            params.append(batch_id)

        if run_id:
            conditions.append("run_id = ?")
            params.append(run_id)
            
        if category:
            conditions.append("category = ?")
            params.append(category)
            
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
            
        if faction:
            if isinstance(faction, str) and "," in faction:
                f_list = [f.strip() for f in faction.split(",")]
                placeholders = ",".join("?" * len(f_list))
                conditions.append(f"faction IN ({placeholders})")
                params.extend(f_list)
            elif isinstance(faction, (list, tuple)):
                placeholders = ",".join("?" * len(faction))
                conditions.append(f"faction IN ({placeholders})")
                params.extend(faction)
            else:
                conditions.append("faction = ?")
                params.append(faction)
            
        if universe:
            conditions.append("universe = ?")
            params.append(universe)

        if turn_range:
            conditions.append("turn BETWEEN ? AND ?")
            params.extend(turn_range)
            
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        limit_clause = ""
        if page is not None:
            # Note: get_query_count must also be locked or safe
            with self._lock:
                total_count = self.get_query_count("events", where_clause, params)
            offset = (page - 1) * page_size
            limit_clause = f"LIMIT {page_size} OFFSET {offset}"
        elif limit:
            limit_clause = f"LIMIT {int(limit)}"
            
        query = f"""
            SELECT turn, timestamp, category, event_type, faction, location, data_json
            FROM events
            {where_clause}
            ORDER BY turn ASC, timestamp ASC
            {limit_clause}
        """
        
        results = []
        try:
            with self._lock:
                cursor = self._execute_query(query, params)
                rows = cursor.fetchall()
            
            for row in rows:
                try:
                    data = json.loads(row[6]) if row[6] else {}
                except json.JSONDecodeError:
                    data = {}
                    
                results.append({
                    "turn": row[0],
                    "timestamp": row[1],
                    "category": row[2],
                    "event_type": row[3],
                    "faction": row[4],
                    "location": row[5],
                    "data": data
                })

        except Exception as e:
            # Check parameter count mismatch
            param_count = len(params)
            placeholder_count = query.count('?')
            if "bad parameter" in str(e) or param_count != placeholder_count:
                 print(f"[DEBUG] API Query Error: {e}")
                 print(f"[DEBUG] Query: {query}")
                 print(f"[DEBUG] Params ({param_count} vs {placeholder_count} placeholders): {params}")
                 print(f"[DEBUG] Types: {[type(p) for p in params]}")
            else:
                 print(f"Error querying telemetry: {e}")
            
        if page is not None:
            return {
                "data": results,
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        return results

    def query_resource_transactions(self, faction: str = None, universe: str = None, 
                                     category: str = None, turn_range: tuple = None, 
                                     page: Optional[int] = None, page_size: int = 100) -> Any:
        """Query resource transactions with optional filters."""
        conditions = []
        params = []
        
        if faction:
            conditions.append("faction = ?")
            params.append(faction)
        if universe:
            conditions.append("universe = ?")
            params.append(universe)
        if category:
            conditions.append("category = ?")
            params.append(category)
        if turn_range:
            conditions.append("turn BETWEEN ? AND ?")
            params.extend(turn_range)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else "WHERE 1=1"
        query = f"SELECT * FROM resource_transactions {where_clause} ORDER BY turn"
        
        if page is not None:
            total_count = self.get_query_count("resource_transactions", where_clause, params)
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"
            
        cursor = self._execute_query(query, params)
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        if page is not None:
            return {
                "data": data,
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        return data

    def query_battle_performance(self, faction: str = None, universe: str = None,
                                  turn_range: tuple = None, page: Optional[int] = None, 
                                  page_size: int = 100) -> Any:
        """Query battle performance metrics with optional filters."""
        conditions = []
        params = []
        
        if faction:
            conditions.append("faction = ?")
            params.append(faction)
        if universe:
            conditions.append("universe = ?")
            params.append(universe)
        if turn_range:
            conditions.append("turn BETWEEN ? AND ?")
            params.extend(turn_range)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else "WHERE 1=1"
        query = f"SELECT * FROM battle_performance {where_clause} ORDER BY turn"
        
        if page is not None:
            total_count = self.get_query_count("battle_performance", where_clause, params)
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"
            
        cursor = self._execute_query(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            result = dict(zip(columns, row))
            if result.get("force_composition"):
                result["force_composition"] = json.loads(result["force_composition"])
            results.append(result)
        
        if page is not None:
            return {
                "data": results,
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        return results

    def get_latest_batch_id(self, universe: str, run_id: str) -> Optional[str]:
        """Identifies the most recent batch_id for the given run context."""
        try:
            with self._lock:
                cursor = self.conn.cursor()
                # Order by timestamp desc to get latest activity
                cursor.execute("""
                    SELECT batch_id FROM events 
                    WHERE universe=? AND run_id=? 
                    ORDER BY timestamp DESC LIMIT 1
                """, (universe, run_id))
                row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"Error resolving latest batch: {e}")
            print(f"[DEBUG] Query: SELECT ... WHERE universe={universe} AND run_id={run_id}")
            return None

    def query_diplomacy_events(self, universe: str) -> List[tuple]:
        """Returns list of (turn, factions_involved) for network graph."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT turn, data_json 
            FROM events 
            WHERE universe = ? AND category = 'diplomacy'
        """, (universe,))
        
        edges = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[1])
                # Assuming data has 'target_faction' or similar. 
                # Or extracting from keywords/text if structured data missing.
                # For now assuming data={'target_faction': 'X', ...}
                tgt = data.get('target_faction')
                src = data.get('faction') # Faction column in events table not selected here but could be
                # If we need source faction, query it:
            except:
                continue
        
        # Better query selecting faction column:
        cursor.execute("""
            SELECT faction, data_json 
            FROM events 
            WHERE universe = ? AND category = 'diplomacy'
        """, (universe,))
        
        for row in cursor.fetchall():
            src = row[0]
            try:
                data = json.loads(row[1])
                tgt = data.get('target_faction') or data.get('other_faction')
                if src and tgt:
                    edges.append((src, tgt))
            except:
                pass
        return edges
    # --- Phase 4 Modifications ---

    def get_run_max_turn(self, universe: str, run_id: str) -> int:
        """Returns the highest turn number indexed for a run."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(turn) FROM events WHERE universe = ? AND run_id = ?", (universe, run_id))
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0

    def query_galaxy_snapshot(self, universe: str, run_id: str, turn: int) -> Dict[str, Any]:
        """
        Reconstructs the galaxy and faction state at a specific turn.
        """
        cursor = self.conn.cursor()
        
        # 1. Get Latest Faction Stats at or before turn
        # Logic: For each faction, find the row with the max turn <= target_turn
        cursor.execute("""
            SELECT f.faction, f.requisition, f.promethium, f.planets_controlled, f.fleets_count, f.data_json
            FROM factions f
            INNER JOIN (
                SELECT faction, MAX(turn) as max_turn
                FROM factions
                WHERE universe = ? AND run_id = ? AND turn <= ?
                GROUP BY faction
            ) latest ON f.faction = latest.faction AND f.turn = latest.max_turn
            WHERE f.universe = ? AND f.run_id = ?
        """, (universe, run_id, turn, universe, run_id))
        
        factions = {}
        for row in cursor.fetchall():
            try:
                raw_data = json.loads(row[5]) if row[5] else {}
            except:
                raw_data = {}
                
            factions[row[0]] = {
                "requisition": row[1],
                "promethium": row[2],
                "planets_count": row[3],
                "fleets_count": row[4],
                "summary": raw_data
            }
            
        # 2. Get Planet Ownership Snapshot
        # Priority 1: Latest 'planet_update' event (contains ALL planets)
        cursor.execute("""
            SELECT data_json 
            FROM events
            WHERE universe = ? AND run_id = ? AND event_type = 'planet_update' AND turn <= ?
            ORDER BY turn DESC, timestamp DESC
            LIMIT 1
        """, (universe, run_id, turn))
        
        row = cursor.fetchone()
        planets = {}
        if row:
            try:
                data = json.loads(row[0])
                for p in data.get("planets", []):
                    planets[p["name"]] = {
                        "owner": p["owner"],
                        "status": p.get("status", "Stable"),
                        "is_sieged": p.get("is_sieged", False),
                        "system": p.get("system") # Include system for grouping
                    }
            except:
                pass
        
        # Priority 2: Patch with individual 'planet_captured' style events if needed 
        # (Though planet_update should be authoritative if it exists)
                 
        return {
            "turn": turn,
            "factions": factions,
            "planets": planets
        }

    # --- Phase 4 Modifications ---

    def create_advanced_views(self):
        """Creates materialized views for advanced analytics."""
        cursor = self.conn.cursor()
        
        # Faction win rate by universe
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS faction_win_rates AS
            SELECT faction, universe, 
                   COUNT(*) as total_battles,
                   SUM(CASE WHEN winner = faction THEN 1 ELSE 0 END) as wins,
                   ROUND(100.0 * SUM(CASE WHEN winner = faction THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate
            FROM battles
            GROUP BY faction, universe;
        """)

        # Resource efficiency (resources per planet)
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS resource_efficiency AS
            SELECT faction, universe, turn,
                   ROUND(requisition * 1.0 / NULLIF(planets_controlled, 0), 2) as req_per_planet,
                   ROUND(promethium * 1.0 / NULLIF(planets_controlled, 0), 2) as prom_per_planet
            FROM factions
            WHERE planets_controlled > 0;
        """)

        # Tech unlock velocity (techs per turn)
        # Note: Using event_type LIKE '%tech%unlock%' requires consistent event naming
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS tech_velocity AS
            SELECT faction, universe, turn,
                   COUNT(*) as techs_unlocked,
                   SUM(COUNT(*)) OVER (PARTITION BY faction, universe ORDER BY turn) as cumulative_techs
            FROM events
            WHERE event_type LIKE '%tech%unlock%'
            GROUP BY faction, universe, turn;
        """)

        # Battle intensity heatmap data
        cursor.execute("DROP VIEW IF EXISTS battle_intensity")
        cursor.execute("""
            CREATE VIEW battle_intensity AS
            SELECT universe, location, turn, COUNT(*) as battle_count,
                   SUM(total_damage) as total_damage,
                   AVG(duration_rounds) as avg_duration
            FROM battles
            GROUP BY universe, location, turn;
        """)

        # AI decision patterns
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS ai_decision_frequency AS
            SELECT faction, universe, event_type, COUNT(*) as frequency
            FROM events
            WHERE category IN ('strategy', 'diplomacy', 'construction')
            GROUP BY faction, universe, event_type;
        """)
        
        self.conn.commit()

    # --- Query Caching ---
    
    class QueryCache:
        def __init__(self, redis_url=None):
            self.stats = {"hits": 0, "misses": 0, "hit_rate": 0.0}
            try:
                if redis_url:
                    self.backend = RedisCacheBackend(redis_url)
                else:
                    self.backend = MemoryCacheBackend()
            except:
                self.backend = MemoryCacheBackend()

        def _get_key(self, query: str, params: tuple) -> str:
            import hashlib
            s = f"{query}|{str(params)}"
            return hashlib.md5(s.encode()).hexdigest()

        def get(self, query: str, params: tuple, ttl: int = 300) -> Optional[Any]:
            key = self._get_key(query, params)
            data = self.backend.get(key)
            if data is not None:
                self.stats["hits"] += 1
                self._update_stats()
                return data
            self.stats["misses"] += 1
            self._update_stats()
            return None

        def set(self, query: str, params: tuple, data: Any):
            key = self._get_key(query, params)
            # Handle pandas DF serialization for memory backend
            serializable_data = data.to_dict(orient='records') if pd and isinstance(data, pd.DataFrame) else data
            self.backend.set(key, serializable_data)

        def invalidate(self):
            self.backend.clear()
            
        def _update_stats(self):
            total = self.stats["hits"] + self.stats["misses"]
            if total > 0:
                self.stats["hit_rate"] = self.stats["hits"] / total

        def get_stats(self):
            return self.stats

        def get_cache_stats(self):
            return self.get_stats()

    def _query_cached(self, query: str, params: tuple) -> 'pd.DataFrame':
        """Internal wrapper to check cache before DB."""
        if not hasattr(self, 'cache'):
            # Lazy init or if not inited in __init__
            self.cache = self.QueryCache()
            
        data = self.cache.get(query, params)
        if data is not None and pd is not None:
             # reconstitute DataFrame
             return pd.DataFrame(data)
             
        if pd is None: return None
        
        df = pd.read_sql_query(query, self.conn, params=params)
        self.cache.set(query, params, df)
        return df

    # --- Aggregation Queries ---

    def query_faction_comparison(self, factions: List[str], universe: str, metrics: List[str]) -> 'pd.DataFrame':
        """Compare multiple factions on specific metrics over time."""
        if not factions or not metrics: return pd.DataFrame() if pd else None
        
        valid_metrics = {'requisition', 'promethium', 'planets_controlled', 'battles_won', 'units_recruited'}
        selected_metrics = [m for m in metrics if m in valid_metrics]
        
        cols = ", ".join(selected_metrics)
        placeholders = ",".join("?" * len(factions))
        query = f"""
            SELECT turn, faction, {cols}
            FROM factions
            WHERE universe = ? AND faction IN ({placeholders})
            ORDER BY turn, faction
        """
        try:
            return self._query_cached(query, tuple([universe] + factions))
        except Exception as e:
            print(f"Error in comparison query: {e}")
            return pd.DataFrame() if pd else None

    def query_battle_heatmap(self, universe: str) -> 'pd.DataFrame':
        """Location-based battle intensity."""
        query = """
            SELECT location, SUM(total_damage) as total_damage, SUM(battle_count) as battles
            FROM battle_intensity
            WHERE universe = ?
            GROUP BY location
        """
        try:
            return self._query_cached(query, (universe,))
        except:
            return pd.DataFrame() if pd else None

    # --- Maintenance & Incremental Indexing ---

    def index_incremental(self, batch_path: str):
        """Indexes only new runs or runs with updates."""
        # 1. Inspect runs
        # 2. Check last modified vs indexed metadata
        # For MVP, we'll just rely on _is_indexed check which is by ID.
        # To truly support updates, we'd need timestamp check.
        # The existing index_run calls _is_indexed which checks existence.
        # So essentially `index_batch` IS incremental if run IDs are unique/stable.
        self.index_batch(batch_path)

    def vacuum_database(self):
        self.conn.execute("VACUUM")

    def rebuild_fts_index(self):
        self.conn.execute("INSERT INTO events_fts(events_fts) VALUES('rebuild')")

    def analyze_tables(self):
        self.conn.execute("ANALYZE")    
    
    def check_integrity(self):
        cursor = self.conn.execute("PRAGMA integrity_check")
        return cursor.fetchall()

    def close(self):
        self.conn.close()

    def set_gold_standard_run(self, universe: str, run_id: str, batch_id: str) -> bool:
        """Sets a specific run as the gold standard for its universe."""
        try:
            cursor = self.conn.cursor()
            # Clear existing
            cursor.execute("UPDATE runs SET is_gold_standard = 0 WHERE universe = ?", (universe,))
            # Set new
            cursor.execute("""
                UPDATE runs SET is_gold_standard = 1 
                WHERE universe = ? AND run_id = ? AND batch_id = ?
            """, (universe, run_id, batch_id))
            
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error setting gold standard: {e}")
            return False

    def get_gold_standard_run(self, universe: str) -> Optional[Dict[str, Any]]:
        """Retrieves the gold standard run for the universe."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT run_id, batch_id, winner, turns_taken, finished_at 
                FROM runs 
                WHERE universe = ? AND is_gold_standard = 1 
                LIMIT 1
            """, (universe,))
            row = cursor.fetchone()
            if row:
                return {
                    "run_id": row[0],
                    "batch_id": row[1],
                    "winner": row[2],
                    "turns_taken": row[3],
                    "timestamp": row[4]
                }
            return None
        except Exception as e:
            print(f"Error getting gold standard: {e}")
            return None

    def clear_gold_standard(self, universe: str) -> bool:
        """Removes gold standard designation."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE runs SET is_gold_standard = 0 WHERE universe = ?", (universe,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error clearing gold standard: {e}")
            return False

    def compare_runs(self, universe: str, current_run_id: str, current_batch_id: str, baseline_run_id: str, baseline_batch_id: str) -> Dict[str, Any]:
        """Compares two runs across key metrics."""
        if pd is None:
             return {"error": "Comparison features require pandas installed."}
        
        def fetch_run_data(r_id, b_id):
            data = {}
            try:
                # Factions
                df_factions = pd.read_sql_query(
                    "SELECT * FROM factions WHERE universe = ? AND run_id = ? AND batch_id = ? ORDER BY turn",
                    self.conn, params=(universe, r_id, b_id)
                )
                data['factions'] = df_factions
                
                # Resources
                df_res = pd.read_sql_query(
                    "SELECT amount, category, faction FROM resource_transactions WHERE universe = ? AND run_id = ? AND batch_id = ?",
                    self.conn, params=(universe, r_id, b_id)
                )
                data['resources'] = df_res
                
                # Metadata
                cursor = self.conn.cursor()
                cursor.execute("SELECT turns_taken, winner FROM runs WHERE universe = ? AND run_id = ? AND batch_id = ?", (universe, r_id, b_id))
                meta = cursor.fetchone()
                data['metadata'] = {"turns_taken": meta[0], "winner": meta[1]} if meta else {}
                
            except Exception as e:
                print(f"Error fetching comparison data for {r_id}: {e}")
                data['error'] = str(e)
            return data

        current = fetch_run_data(current_run_id, current_batch_id)
        baseline = fetch_run_data(baseline_run_id, baseline_batch_id)
        
        if 'error' in current or 'error' in baseline:
            return {"error": "Failed to load run data"}
            
        # Calculate Deltas
        deltas = {}
        
        # Victory Delta
        c_turns = current['metadata'].get('turns_taken', 0) or 0
        b_turns = baseline['metadata'].get('turns_taken', 0) or 0
        deltas['victory'] = {
            "turns_delta": int(c_turns - b_turns),
            "winner_changed": current['metadata'].get('winner') != baseline['metadata'].get('winner')
        }
        
        # Economic Delta (Global Avg)
        def get_avg_metric(df, col):
            if df is None or df.empty or col not in df.columns: return 0.0
            return float(df[col].mean())
            
        deltas['economic'] = {
            "gross_income_delta": get_avg_metric(current['factions'], 'gross_income') - get_avg_metric(baseline['factions'], 'gross_income'),
            "net_profit_delta": get_avg_metric(current['factions'], 'net_profit') - get_avg_metric(baseline['factions'], 'net_profit')
        }
        
        # Industrial & Research
        deltas['industrial'] = {
            "efficiency_delta": get_avg_metric(current['factions'], 'construction_efficiency') - get_avg_metric(baseline['factions'], 'construction_efficiency'),
            "idle_slots_delta": get_avg_metric(current['factions'], 'idle_construction_slots') - get_avg_metric(baseline['factions'], 'idle_construction_slots')
        }
        
        deltas['research'] = {
            "research_points_delta": get_avg_metric(current['factions'], 'research_points') - get_avg_metric(baseline['factions'], 'research_points')
        }
        
        # Helper to convert DF to JSON-friendly dict (limited)
        def snapshot(data_dict, run_id, batch_id):
            return {
                "run_id": run_id,
                "batch_id": batch_id,
                "metadata": data_dict['metadata'],
                "summary": {
                    "avg_income": get_avg_metric(data_dict['factions'], 'gross_income'),
                    "avg_efficiency": get_avg_metric(data_dict['factions'], 'construction_efficiency')
                }
            }

        return {
            "current": snapshot(current, current_run_id, current_batch_id),
            "baseline": snapshot(baseline, baseline_run_id, baseline_batch_id),
            "deltas": deltas
        }
