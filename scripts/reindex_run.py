
import os
import sys
from src.reporting.indexer import ReportIndexer

# Configuration
DB_PATH = "reports/campaign_data.db"
BATCH_PATH = "reports/eternal_crusade/batch_20260118_004019"
RUN_ID = "run_1768696819"  # The run we saw in recent directory
RUN_PATH = os.path.join(BATCH_PATH, RUN_ID)
UNIVERSE = "eternal_crusade"

def reindex():
    if not os.path.exists(RUN_PATH):
        print(f"Run path not found: {RUN_PATH}")
        return

    print("Initializing ReportIndexer...")
    indexer = ReportIndexer(DB_PATH)
    
    print(f"Indexing run at: {RUN_PATH}")
    indexer.index_run(RUN_PATH, universe=UNIVERSE)
    
    print("Re-indexing complete.")

if __name__ == "__main__":
    reindex()
