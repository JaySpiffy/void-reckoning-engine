
import os
import json
import sqlite3
import pytest
from src.reporting.indexing import ReportIndexer

@pytest.fixture
def indexer(tmp_path):
    db_path = tmp_path / "test_index.db"
    return ReportIndexer(str(db_path))

def test_indexer_initialization(indexer):
    """Verify that the indexer creates the correct schema."""
    conn = indexer.conn
    cursor = conn.cursor()
    
    # Check for core tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ["runs", "factions", "battles", "events", "resource_transactions", "battle_performance"]
    for table in expected_tables:
        assert table in tables, f"Table {table} not created"

def test_event_ingestion(indexer):
    """Verify generic event ingestion."""
    batch_id = "test_batch"
    run_id = "run_001"
    universe = "test_universe"
    
    events = [
        {
            "turn": 1,
            "timestamp": "2026-02-06T12:00:00",
            "category": "test",
            "event_type": "test_event",
            "faction": "TestFaction",
            "data": {"location": "PlanetX", "entity_type": "Ship", "val": 42}
        }
    ]
    
    indexer.index_realtime_events(batch_id, run_id, events, universe)
    
    # Query back
    results = indexer.query_telemetry(run_id=run_id, universe=universe)
    assert len(results) == 1
    assert results[0]["turn"] == 1
    assert results[0]["faction"] == "TestFaction"
    assert results[0]["data"]["val"] == 42

def test_resource_transactions(indexer):
    """Verify economic transaction indexing."""
    batch_id = "batch_1"
    run_id = "run_1"
    universe = "uni_1"
    
    txs = [
        {
            "batch_id": batch_id,
            "run_id": run_id,
            "turn": 5,
            "faction": "MegaCorp",
            "category": "Income",
            "amount": 1000,
            "source_planet": "Earth"
        }
    ]
    
    indexer.index_realtime_resource_transactions(batch_id, run_id, txs, universe)
    
    results = indexer.query_resource_transactions(universe=universe, faction="MegaCorp")
    assert len(results) == 1
    assert results[0]["amount"] == 1000
    assert results[0]["category"] == "Income"

def test_battle_performance(indexer):
    """Verify military performance indexing."""
    batch_id = "b1"
    run_id = "r1"
    universe = "u1"
    
    perf = [
        {
            "batch_id": batch_id,
            "run_id": run_id,
            "turn": 10,
            "battle_id": "B123",
            "faction": "Aggressors",
            "damage_dealt": 5000.5,
            "resources_lost": 1000.0,
            "force_composition": {"Cruiser": 2, "Fighter": 10}
        }
    ]
    
    indexer.index_realtime_battle_performance(batch_id, run_id, perf, universe)
    
    results = indexer.query_battle_performance(universe=universe, faction="Aggressors")
    assert len(results) == 1
    assert results[0]["damage_dealt"] == 5000.5
    assert results[0]["combat_effectiveness_ratio"] == 5.0005
    assert results[0]["force_composition"] == {"Cruiser": 2, "Fighter": 10}

def test_text_log_indexing(indexer, tmp_path):
    """Verify that plain text logs are indexed (legacy fallback)."""
    log_file = tmp_path / "simulation.log"
    log_file.write_text("Turn 1: Faction A moved to Sector 5\n{\"turn\": 2, \"event_type\": \"json_event\", \"message\": \"structured\"}")
    
    indexer._index_text_log("batch_text", "run_text", str(log_file), "uni_text")
    
    # We expect 2 events: one text log and one structured JSON
    results = indexer.query_telemetry(run_id="run_text")
    assert len(results) == 2
    
    types = [r["event_type"] for r in results]
    assert "text_log" in types
    assert "json_event" in types
