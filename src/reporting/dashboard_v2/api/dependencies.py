from fastapi import Depends, HTTPException
import sys
import os

# Add project root to path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from src.reporting.indexing import ReportIndexer
from src.reporting.telemetry import TelemetryCollector
from src.reporting.dashboard_v2.services.dashboard_service import DashboardService
from src.reporting.dashboard_v2.api.config import settings
from src.core.config import REPORTS_DIR

_service_instance: DashboardService = None
_global_universe: str = None
_global_run_id: str = None

def set_global_context(universe: str, run_id: str = None):
    global _global_universe, _global_run_id
    _global_universe = universe
    _global_run_id = run_id

# ... imports ...

from src.reporting.dashboard_v2.api.utils.discovery import discover_latest_run

async def get_dashboard_service() -> DashboardService:
    """Dependency for DashboardService singleton."""
    global _service_instance
    if _service_instance is None:
        try:
            # Use global context if available, otherwise defaults
            # This mirrors how the old dashboard passed CLI args down
            service = DashboardService()
            
            target_universe = _global_universe or settings.UNIVERSE
            target_run_id = _global_run_id or settings.RUN_ID
            
            # Auto-Discovery: If default run implies no specific user intent, try to find latest
            # Or if the target run is empty, look for something better.
            batch_id, latest_run_id, latest_run_path = discover_latest_run(target_universe)
            
            run_path = None
            
            if latest_run_id and (not target_run_id or target_run_id == settings.RUN_ID):
                 print(f"Auto-Discovered newer run: {latest_run_id} (using as target)")
                 target_run_id = latest_run_id
                 run_path = latest_run_path
            elif target_run_id:
                # Attempt to find path for specific run
                # Using simple glob strategy matching DashboardService logic
                import glob
                base_search = f"reports/{target_universe}/batch_*/{target_run_id}"
                matches = glob.glob(base_search)
                if matches:
                    run_path = matches[0]
                else:
                    # Fallback to reports/runs
                    flat_path = f"reports/runs/{target_run_id}"
                    if os.path.exists(flat_path):
                        run_path = flat_path
            
            # Fallback path if none found (prevents crash, but data will be missing)
            if not run_path:
                print(f"Warning: Could not resolve path for run {target_run_id}")
                run_path = os.path.join(REPORTS_DIR, "runs", target_run_id)
                
            # Construct DB Path
            db_path = os.path.join(run_path, "campaign_data.db")
            print(f"Initializing Indexer at: {db_path}")

            # Initialize core components
            # Using /app/reports based on docker-compose volume
            indexer = ReportIndexer(db_path=db_path)
            telemetry = TelemetryCollector(
                log_dir=run_path, 
                universe_name=target_universe
            )
            
            service.attach_indexer(indexer)
            service.attach_telemetry(telemetry)
            
            if latest_run_id == target_run_id and latest_run_path:
                 # Check directly if we need to index (synchronous for now to ensure data availability)
                 # In production this might be slow, but essential for user experience "it just works"
                 print(f"Indexing auto-discovered run: {latest_run_path}...")
                 indexer.index_run(latest_run_path, universe=target_universe)
            
            service.initialize(
                universe=target_universe,
                run_id=target_run_id,
                batch_id=batch_id or "unknown"
            )
            
            # Only assign if successful
            _service_instance = service
            
        except Exception as e:
            # Catch ALL exceptions during init to prevent broken state
            print(f"Dashboard Service Initialization Failed: {e}")
            raise HTTPException(status_code=503, detail=f"Dashboard Initialization Failed: {str(e)}")
            
    return _service_instance

async def get_telemetry_collector(service=Depends(get_dashboard_service)):
    """Dependency for TelemetryCollector from service singleton."""
    if not service.telemetry:
        raise HTTPException(status_code=503, detail="TelemetryCollector not initialized in DashboardService")
    return service.telemetry

async def get_indexer(service=Depends(get_dashboard_service)):
    """Dependency for ReportIndexer from service singleton."""
    if not service.indexer:
        raise HTTPException(status_code=503, detail="ReportIndexer not initialized in DashboardService")
    return service.indexer

async def get_alert_manager():
    """Dependency for AlertManager singleton."""
    try:
        from src.reporting.alert_manager import AlertManager
        return AlertManager()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AlertManager not available: {str(e)}")
