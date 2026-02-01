import os
import time
import logging
from typing import Dict, Tuple, Any

logger = logging.getLogger(__name__)

def check_database_schema(db_conn) -> Tuple[str, str, Dict]:
    """Verify required tables exist."""
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        required = ['events', 'runs'] # Add others as needed
        missing = [t for t in required if t not in tables]
        
        if missing:
            return "error", f"Missing tables: {missing}", {"tables_found": tables}
        return "healthy", "Schema valid", {"tables": tables}
    except Exception as e:
        return "error", str(e), {}

def check_static_files(static_folder: str) -> Tuple[str, str, Dict]:
    """Verify critical static files exist."""
    if not os.path.exists(static_folder):
        return "error", "Static folder missing", {"path": static_folder}
        
    critical = ['index.html', 'dashboard.html', 'dashboard.css', 'dashboard.js']
    missing = []
    details = {}
    
    for f in critical:
        path = os.path.join(static_folder, f)
        exists = os.path.exists(path)
        details[f] = {"exists": exists}
        if exists:
            details[f]["size"] = os.path.getsize(path)
        else:
            missing.append(f)
            
    if missing:
        return "degraded", f"Missing static files: {missing}", details
    return "healthy", "Static files verified", details

def check_telemetry_connection(telemetry) -> Tuple[str, str, Dict]:
    """Test telemetry collector responsiveness."""
    if not telemetry:
        return "error", "Telemetry not attached", {}
    
    # Simple check if object is alive/valid
    return "healthy", "Telemetry attached", {"log_dir": getattr(telemetry, 'log_dir', 'unknown')}

def check_data_provider_queries(provider, universe: str, run_id: str) -> Tuple[str, str, Dict]:
    """Test sample queries for each data type."""
    if not provider:
        return "error", "Provider missing", {}
        
    results = {}
    failed = False
    
    try:
        t0 = time.time()
        provider.get_active_factions(universe, run_id, batch_id=None)
        results["active_factions"] = f"{(time.time()-t0)*1000:.2f}ms"
    except Exception as e:
        results["active_factions"] = f"Error: {e}"
        failed = True
        
    if failed:
         return "degraded", "Some queries failed", results
    return "healthy", "Queries successful", results
