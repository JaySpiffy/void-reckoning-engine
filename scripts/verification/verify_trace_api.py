
import os
import json
import sqlite3
import shutil
from src.reporting.indexing.orchestrator import ReportIndexer
from src.reporting.dashboard_data_provider import DashboardDataProvider

TEST_DB = "test_trace_index.db"

def setup():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def verify_trace_api():
    print(f"Initializing ReportIndexer with {TEST_DB}...")
    indexer = ReportIndexer(TEST_DB)
    
    # 1. Insert Mock Events
    # Causal Chain: Root -> Child -> Grandchild
    events = [
        {
            "id": 1,
            "batch_id": "test_batch",
            "universe": "test_universe",
            "run_id": "run_001",
            "turn": 1,
            "timestamp": "2026-01-01T10:00:00",
            "category": "ai",
            "event_type": "decision",
            "faction": "FactionA",
            "data": {"foo": "bar"},
            "trace_id": "root_01",
            "parent_trace_id": None
        },
        {
            "id": 2,
            "batch_id": "test_batch",
            "universe": "test_universe",
            "run_id": "run_001",
            "turn": 2,
            "timestamp": "2026-01-01T10:05:00",
            "category": "action",
            "event_type": "move",
            "faction": "FactionA",
            "data": {"loc": "Sector1"},
            "trace_id": "child_01",
            "parent_trace_id": "root_01"
        },
        {
            "id": 3,
            "batch_id": "test_batch",
            "universe": "test_universe",
            "run_id": "run_001",
            "turn": 3,
            "timestamp": "2026-01-01T10:10:00",
            "category": "outcome",
            "event_type": "battle",
            "faction": "FactionA",
            "data": {"result": "win"},
            "trace_id": "grandchild_01",
            "parent_trace_id": "child_01"
        }
    ]
    
    # Manually insert since indexer expects files
    print("Inserting mock events directly into DB...")
    cursor = indexer.conn.cursor()
    for e in events:
        cursor.execute("""
            INSERT INTO events (
                batch_id, universe, run_id, turn, timestamp, category, event_type, 
                faction, data_json, trace_id, parent_trace_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            e["batch_id"], e["universe"], e["run_id"], e["turn"], e["timestamp"],
            e["category"], e["event_type"], e["faction"], json.dumps(e["data"]),
            e["trace_id"], e["parent_trace_id"]
        ))
    indexer.conn.commit()
    
    # 2. Test Provider
    print("Testing DashboardDataProvider.get_event_trace...")
    provider = DashboardDataProvider(indexer)
    chain = provider.get_event_trace("test_universe", "run_001", "grandchild_01")
    
    print(f"Chain length: {len(chain)}")
    for i, event in enumerate(chain):
        print(f"[{i}] {event['trace_id']} (Parent: {event.get('parent_trace_id')}) - {event['event_type']}")
        
    # Assertions
    assert len(chain) == 3, f"Expected chain length 3, got {len(chain)}"
    assert chain[0]["trace_id"] == "root_01", "Root event incorrect"
    assert chain[-1]["trace_id"] == "grandchild_01", "Leaf event incorrect"
    
    print("\n[SUCCESS] Trace API Verified Successfully!")
    
    indexer.close()

if __name__ == "__main__":
    try:
        setup()
        verify_trace_api()
    finally:
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except: pass
