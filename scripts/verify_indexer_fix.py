import sys
import os
import sqlite3

# Add src to path
sys.path.append(os.getcwd())

from src.reporting.indexer import ReportIndexer

def reindex_run(run_path):
    # Determine DB path
    db_path = os.path.join(run_path, "campaign_data.db")
    print(f"Indexing {run_path} into {db_path}...")
    
    # Initialize indexer
    indexer = ReportIndexer(db_path)
    
    # Get universe and run_id
    run_id = os.path.basename(run_path)
    universe = "void_reckoning" # Default
    
    # Trigger indexing
    indexer.index_run(run_path, universe=universe)
    print("Indexing complete.")
    
    # Verify
    cursor = indexer.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM factions")
    f_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resource_transactions")
    r_count = cursor.fetchone()[0]
    
    # Military Verification
    cursor.execute("SELECT COUNT(*) FROM battles")
    b_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM battle_performance")
    bp_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events WHERE event_type != 'text_log' AND event_type != 'log_entry'")
    e_count = cursor.fetchone()[0]
    
    print(f"Found {f_count} faction entries and {r_count} resource transactions.")
    print(f"Found {b_count} battles and {bp_count} performance entries.")
    print(f"Found {e_count} structured events (excluding plain logs).")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        reindex_run(sys.argv[1])
    else:
        # Default to the latest run
        reindex_run("reports/runs/run_1770130901")
