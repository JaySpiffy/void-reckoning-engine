
import os
import json
import sqlite3
from src.reporting.indexing.orchestrator import ReportIndexer
from src.observability.replay_analyzer import ReplayAnalyzer

TEST_DB = "test_replay_analysis.db"

def setup():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def verify_analysis():
    print(f"Initializing ReportIndexer with {TEST_DB}...")
    indexer = ReportIndexer(TEST_DB)
    
    # 1. Insert Mock Runs (Identical until Turn 5)
    print("Inserting mock runs...")
    
    # Run A (Control)
    run_a = [
        {"turn": 1, "cat": "sys", "type": "init", "fac": "F1", "data": {"val": 10}},
        {"turn": 5, "cat": "decision", "type": "build", "fac": "F1", "data": {"unit": "Fighter"}},
        {"turn": 10, "cat": "outcome", "type": "res_update", "fac": "F1", "data": {"gold": 100}}
    ]
    
    # Run B (Variable - Diverges at Turn 5)
    run_b = [
        {"turn": 1, "cat": "sys", "type": "init", "fac": "F1", "data": {"val": 10}},
        {"turn": 5, "cat": "decision", "type": "build", "fac": "F1", "data": {"unit": "Cruiser"}}, # Divergence!
        {"turn": 10, "cat": "outcome", "type": "res_update", "fac": "F1", "data": {"gold": 50}} # Drift
    ]
    
    cursor = indexer.conn.cursor()
    
    # Insert A
    for e in run_a:
        cursor.execute("INSERT INTO events (universe, run_id, turn, category, event_type, faction, data_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ("univ", "run_a", e["turn"], e["cat"], e["type"], e["fac"], json.dumps(e["data"])))
                      
    # Insert B
    for e in run_b:
        cursor.execute("INSERT INTO events (universe, run_id, turn, category, event_type, faction, data_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ("univ", "run_b", e["turn"], e["cat"], e["type"], e["fac"], json.dumps(e["data"])))
                      
    # Insert Final Stats for Drift
    cursor.execute("INSERT INTO factions (universe, run_id, turn, faction, planets_controlled, fleets_count, gross_income) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  ("univ", "run_a", 10, "F1", 5, 10, 1000))
    cursor.execute("INSERT INTO factions (universe, run_id, turn, faction, planets_controlled, fleets_count, gross_income) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  ("univ", "run_b", 10, "F1", 5, 8, 800))
                  
    indexer.conn.commit()
    
    # 2. Test Analyzer
    print("Running ReplayAnalyzer...")
    analyzer = ReplayAnalyzer(indexer)
    report = analyzer.compare_runs("univ", "run_a", "run_b")
    
    div = report.get("divergence")
    drift = report.get("drift_metrics")
    
    print("\n--- Divergence Report ---")
    print(json.dumps(report, indent=2))
    
    assert div is not None, "Divergence not found"
    assert div["turn"] == 5, f"Expected divergence at Turn 5, got {div['turn']}"
    assert div["event_a"]["data"]["unit"] == "Fighter"
    assert div["event_b"]["data"]["unit"] == "Cruiser"
    
    assert drift["F1"]["income"] == -200, "Drift calculation incorrect"
    
    print("\n[SUCCESS] Replay Analysis Verified!")
    indexer.close()

if __name__ == "__main__":
    try:
        setup()
        verify_analysis()
    finally:
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except: pass
