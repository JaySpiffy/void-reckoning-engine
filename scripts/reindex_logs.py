
import os
import sys
sys.path.append(os.getcwd())

from src.reporting.indexer import ReportIndexer

# Configuration
DB_PATH = "reports/campaign_data.db"
# Configuration
DB_PATH = "reports/campaign_data.db"
RUN_PATH = r"reports/eternal_crusade/batch_20260112_114125/run_1768218085"
UNIVERSE = "eternal_crusade"
# BATCH_ID unused in index_run usually, but good for context
BATCH_ID = "batch_20260112_114125"
RUN_ID = "run_1768218085"

def reindex_logs():
    print(f"Connecting to {DB_PATH}...")
    indexer = ReportIndexer(db_path=DB_PATH)
    
    if not os.path.exists(RUN_PATH):
        print(f"Run path not found: {RUN_PATH}")
        return

    print(f"Indexing FULL run from {RUN_PATH}...")
    try:
        # Full indexing of JSON events + logs
        indexer.index_run(RUN_PATH, universe=UNIVERSE)
        print("Full run indexing complete!")
        
        # Verify count
        cursor = indexer.conn.cursor()
        cursor.execute("SELECT count(*) FROM events WHERE run_id=?", (RUN_ID,))
        count = cursor.fetchone()[0]
        print(f"Total entries in events table for text_log: {count}")
        
    except Exception as e:
        print(f"Failed to index logs: {e}")

if __name__ == "__main__":
    reindex_logs()
