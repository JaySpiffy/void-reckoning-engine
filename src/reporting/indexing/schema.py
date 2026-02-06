
import sqlite3
import logging

logger = logging.getLogger(__name__)

class IndexerSchema:
    @staticmethod
    def create_schema(conn: sqlite3.Connection):
        """Creates the initial database schema for the reporting index."""
        cursor = conn.cursor()
        
        # 1. Runs Table (Metadata for each simulation execution)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                batch_id TEXT,
                universe TEXT,
                run_id TEXT,
                started_at TEXT,
                finished_at TEXT,
                winner TEXT,
                turns_taken INTEGER,
                is_gold_standard INTEGER DEFAULT 0,
                metadata_json TEXT,
                PRIMARY KEY (universe, run_id, batch_id)
            )
        """)

        # 2. Factions Table (Cumulative stats per turn)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS factions (
                batch_id TEXT,
                universe TEXT,
                run_id TEXT,
                turn INTEGER,
                faction TEXT,
                requisition INTEGER,
                promethium INTEGER,
                planets_controlled INTEGER,
                fleets_count INTEGER,
                units_recruited INTEGER,
                units_lost INTEGER,
                battles_fought INTEGER,
                battles_won INTEGER,
                damage_dealt REAL,
                upkeep_total INTEGER DEFAULT 0,
                gross_income INTEGER DEFAULT 0,
                net_profit INTEGER DEFAULT 0,
                research_points INTEGER DEFAULT 0,
                idle_construction_slots INTEGER DEFAULT 0,
                idle_research_slots INTEGER DEFAULT 0,
                construction_efficiency REAL DEFAULT 0.0,
                military_building_count INTEGER DEFAULT 0,
                economy_building_count INTEGER DEFAULT 0,
                research_building_count INTEGER DEFAULT 0,
                research_delta_requisition INTEGER DEFAULT 0,
                data_json TEXT,
                PRIMARY KEY (universe, run_id, turn, faction)
            )
        """)

        # 3. Battles Table (Summary of tactical engagements)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battles (
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
                data_json TEXT,
                PRIMARY KEY (universe, run_id, turn, location)
            )
        """)

        # 4. Events Table (Raw telemetry streams)
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

        # 5. Resource Transactions (Specialized economic tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                universe TEXT,
                run_id TEXT,
                turn INTEGER,
                faction TEXT,
                category TEXT,
                amount REAL,
                source_planet TEXT,
                timestamp TEXT
            )
        """)

        # 6. Battle Performance (Military analytics)
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
                timestamp TEXT
            )
        """)

        # Indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_run ON events(universe, run_id, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_factions_run ON factions(universe, run_id, turn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_res_run ON resource_transactions(universe, run_id, faction)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_run ON battle_performance(universe, run_id, faction)")

        # Full-Text Search for Event Keywords
        cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(keywords, content=events, content_rowid=id)")
        
        # FTS Triggers
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS events_ai AFTER INSERT ON events BEGIN
                INSERT INTO events_fts(rowid, keywords) VALUES (new.id, new.keywords);
            END;
        """)
        
        conn.commit()

    @staticmethod
    def migrate_schema(conn: sqlite3.Connection):
        """Ensures existing databases are updated with new columns."""
        cursor = conn.cursor()
        
        # Helper to add column if it doesn't exist
        def add_column(table, col, definition):
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
                logger.info(f"Added column {col} to {table}")
            except sqlite3.OperationalError:
                pass # Column already exists
        
        # 1. Runs Migration
        add_column("runs", "is_gold_standard", "INTEGER DEFAULT 0")

        # 2. Factions Migration
        add_column("factions", "upkeep_total", "INTEGER DEFAULT 0")
        add_column("factions", "gross_income", "INTEGER DEFAULT 0")
        add_column("factions", "net_profit", "INTEGER DEFAULT 0")
        add_column("factions", "research_points", "INTEGER DEFAULT 0")
        add_column("factions", "idle_construction_slots", "INTEGER DEFAULT 0")
        add_column("factions", "idle_research_slots", "INTEGER DEFAULT 0")
        add_column("factions", "construction_efficiency", "REAL DEFAULT 0.0")
        add_column("factions", "military_building_count", "INTEGER DEFAULT 0")
        add_column("factions", "economy_building_count", "INTEGER DEFAULT 0")
        add_column("factions", "research_building_count", "INTEGER DEFAULT 0")
        add_column("factions", "research_delta_requisition", "INTEGER DEFAULT 0")
        
        conn.commit()
