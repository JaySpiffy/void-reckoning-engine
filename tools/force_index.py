
import os
import logging
from src.reporting.indexer import ReportIndexer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_index():
    logger.info("Starting manual index...")
    indexer = ReportIndexer("/app/reports/campaign_data.db")
    
    # Target Run
    run_path = "/app/reports/eternal_crusade/batch_20260114_071548/run_1768374948"
    
    if not os.path.exists(run_path):
        logger.error(f"Run path does not exist: {run_path}")
        return

    logger.info(f"Indexing run at: {run_path}")
    try:
        indexer.index_run(run_path)
        logger.info("Index command finished.")
    except Exception as e:
        logger.error(f"Failed to index: {e}")

if __name__ == "__main__":
    force_index()
