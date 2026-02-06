import sys
import os
import json

# Add src to path
sys.path.append(os.getcwd())

from src.reporting.indexing import ReportIndexer
from src.core.config import REPORTS_DIR

def check_history():
    db_path = os.path.join(REPORTS_DIR, "db", "index.db")
    indexer = ReportIndexer(db_path)
    
    # We need to guess the run_id/universe or list them
    print("Finding runs...")
    cursor = indexer.conn.cursor()
    cursor.execute("SELECT DISTINCT run_id, universe, batch_id FROM events")
    runs = cursor.fetchall()
    
    print(f"Found {len(runs)} run/universe/batch combos:")
    for r in runs:
        print(r)
        
    # Pick the most recent one
    # Usually 'run_001', 'eternal_crusade'
    
    run_id = "run_001"
    universe = "eternal_crusade"
    
    print(f"\nQuerying Economy for {run_id} / {universe}...")
    
    events = indexer.query_telemetry(
        run_id=run_id,
        universe=universe,
        category="economy",
        event_type="income_collected",
        limit=10  # check first few
    )
    
    print(f"First 10 events (ordered by Turn):")
    for e in events:
        print(f"Turn: {e['turn']}, Faction: {e['faction']}, Amount: {e['data'].get('amount')}")
        
    # Check simple count
    cursor.execute("SELECT COUNT(*) FROM events WHERE run_id=? AND universe=? AND category='economy'", (run_id, universe))
    count = cursor.fetchone()[0]
    print(f"Total economy events: {count}")

if __name__ == "__main__":
    check_history()
