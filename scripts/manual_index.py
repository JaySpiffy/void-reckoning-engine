import sys
import os

# Ensure src is in path
sys.path.append(os.getcwd())

from src.reporting.indexer import ReportIndexer

BATCH_PATH = "reports/unknown/batch_20260109_230421"
DB_PATH = "reports/db/index.db"

def main():
    print(f"Indexing batch: {BATCH_PATH}")
    print(f"Target DB: {DB_PATH}")
    
    if not os.path.exists(BATCH_PATH):
        print("Batch path invalid")
        return

    indexer = ReportIndexer(DB_PATH)
    indexer.index_batch(BATCH_PATH)
    print("Indexing complete.")

if __name__ == "__main__":
    main()
