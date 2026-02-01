
import os
import glob
import logging
from typing import Optional, Tuple
from src.core.config import REPORTS_DIR

logger = logging.getLogger(__name__)

def discover_latest_run(universe: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Finds the most recent batch and run for a given universe.
    Returns (batch_id, run_id, run_path)
    """
    universe_dir = os.path.join(REPORTS_DIR, universe)
    if not os.path.exists(universe_dir):
        return None, None, None
        
    # Find all batch directories
    all_batches = glob.glob(os.path.join(universe_dir, "batch_*"))
    
    # Filter out "unknown_batch" and ensure we only get valid timestamped batches
    batch_dirs = [
        b for b in all_batches 
        if os.path.isdir(b) 
        and os.path.basename(b) != "unknown_batch"
        and "unknown" not in os.path.basename(b)
    ]
    
    if not batch_dirs:
        logger.warning(f"No batch directories found in {universe_dir}")
        return None, None, None
        
    # Sort by timestamp (batch_YYYYMMDD_HHMMSS)
    batch_dirs.sort(reverse=True)
    latest_batch_dir = batch_dirs[0]
    batch_id = os.path.basename(latest_batch_dir)
    # logger.info(f"Found latest batch: {batch_id}")
    
    # Find runs in the latest batch
    run_dirs = glob.glob(os.path.join(latest_batch_dir, "run_*"))
    if not run_dirs:
        return None, None, None
        
    # Sort runs (if named run_TIMESTAMP or run_ID)
    # If run_1, run_2, simple string sort might fail, but decent enough for now
    # Ideally check manifest start time, but directory sort is faster
    run_dirs.sort(reverse=True)
    latest_run_dir = run_dirs[0]
    run_id = os.path.basename(latest_run_dir)
    
    return batch_id, run_id, latest_run_dir

def discover_all_runs(universe: Optional[str] = None) -> list:
    """
    Scans the reports directory for all available runs across all universes/batches.
    Returns: List of Dicts with run metadata.
    """
    from src.core.config import REPORTS_DIR
    import json
    import os
    import glob
    from datetime import datetime
    
    runs = []
    
    # If universe is specified, only look there. Otherwise look in all subfolders.
    if universe:
        universes = [universe]
    else:
        # List all subdirectories in REPORTS_DIR that contain matches
        universes = [d for d in os.listdir(REPORTS_DIR) if os.path.isdir(os.path.join(REPORTS_DIR, d))]
        
    for u in universes:
        universe_dir = os.path.join(REPORTS_DIR, u)
        if not os.path.exists(universe_dir): continue
        
        # Pattern: reports/universe/ANY_BATCH/run_*
        run_paths = glob.glob(os.path.join(universe_dir, "*", "run_*"))
        
        for rp in run_paths:
            run_id = os.path.basename(rp)
            batch_dir = os.path.dirname(rp)
            batch_id = os.path.basename(batch_dir)
            
            # Filter out unknown_batch
            if "unknown_batch" in batch_id or "unknown" in batch_id:
                continue
            
            # Try to get metadata from manifest.json
            manifest_path = os.path.join(rp, "manifest.json")
            started_at = None
            turns_taken = 0
            winner = None
            
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        started_at = meta.get("started_at") or meta.get("timestamp")
                        # Check multiple manifest locations for turn count
                        turns_taken = meta.get("turns_taken") or meta.get("metadata", {}).get("turns") or 0
                        winner = meta.get("winner")
                except:
                    pass
            
            # Fallback/Validation: Count turn_* directories for actual progress if manifest is stale or incomplete
            if turns_taken == 0:
                try:
                    t_dirs = glob.glob(os.path.join(rp, "turn_*"))
                    if t_dirs:
                        turns_taken = len(t_dirs)
                except:
                    pass
            
            # Fallback for started_at using directory timestamp if possible
            if not started_at:
                try:
                    # run_1768705625 -> timestamp
                    ts_part = run_id.replace("run_", "")
                    if ts_part.isdigit():
                        started_at = datetime.fromtimestamp(int(ts_part)).isoformat()
                    else:
                        started_at = datetime.fromtimestamp(os.path.getctime(rp)).isoformat()
                except:
                    started_at = "Unknown"

            runs.append({
                "run_id": run_id,
                "batch_id": batch_id,
                "universe": u,
                "started_at": started_at,
                "turns_taken": turns_taken,
                "winner": winner,
                "path": rp
            })
            
    # Sort by started_at DESC
    return sorted(runs, key=lambda x: str(x.get("started_at", "")), reverse=True)

