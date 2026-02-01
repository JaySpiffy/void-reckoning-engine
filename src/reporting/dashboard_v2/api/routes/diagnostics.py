import os
import time
from fastapi import APIRouter, Depends, HTTPException
from src.reporting.dashboard_v2.api.models import DiagnosticsResponse, SystemHealthResponse, ComponentHealthStatus
from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service
import src.reporting.dashboard_v2.api.utils.health_checks as health

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])

@router.get("/static", response_model=DiagnosticsResponse)
async def get_static_diagnostics():
    """
    Get diagnostics for static files.
    """
    # Locate static folder relative to this file or project root
    # Adjust path logic as needed based on actual project structure
    # This assumes src/reporting/dashboard_v2/api/routes -> ... -> src/reporting/static
    current_dir = os.path.dirname(os.path.abspath(__file__)) # api/routes
    # api/routes -> api -> dashboard_v2 -> reporting -> src (root) -> reporting -> static
    # Or more simply: go up to 'src', then down to 'reporting/static'
    # Current depth: src/reporting/dashboard_v2/api/routes (5 levels deep from root if src is root, or 6)
    # Let's go up 4 levels to 'src/reporting' parent, which is 'src'
    
    # Using pathlib logic for clarity: parents[3] is 'src/reporting', parents[4] is 'src'
    # Actually, if file is: src/reporting/dashboard_v2/api/routes/diagnostics.py
    # dirname: src/reporting/dashboard_v2/api/routes
    # ../ : src/reporting/dashboard_v2/api
    # ../../ : src/reporting/dashboard_v2
    # ../../../ : src/reporting
    
    # We want src/reporting/static.
    # So we go up 3 levels to src/reporting, then join static.
    
    reporting_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) 
    # Verify we are in 'reporting' dir? No, wait.
    # src/reporting/dashboard_v2/api/routes/diagnostics.py
    # 1. routes (current_dir)
    # 2. api
    # 3. dashboard_v2
    # 4. reporting  <-- This is where we want to be to find 'static' alongside 'dashboard_v2' ?
    # No, static is likely in src/reporting/static.
    
    # Let's count parents.
    # 1. os.path.dirname(current_dir) -> api
    # 2. os.path.dirname(...) -> dashboard_v2
    # 3. os.path.dirname(...) -> reporting
    
    reporting_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    static_path = os.path.join(reporting_dir, 'static')
    
    files_info = {}
    critical_files = ['index.html', 'dashboard.html', 'dashboard.css', 'dashboard.js']
    
    for filename in critical_files:
        filepath = os.path.join(static_path, filename)
        exists = os.path.exists(filepath)
        files_info[filename] = {
            'exists': exists,
            'size': os.path.getsize(filepath) if exists else 0,
            'readable': os.access(filepath, os.R_OK) if exists else False
        }
    
    return DiagnosticsResponse(
        static_folder=static_path,
        static_url_path="/static",
        files=files_info
    )

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(service = Depends(get_dashboard_service)):
    """
    Get comprehensive system health status.
    """
    components = []
    overall_status = "healthy"

    # 1. Database Schema Check
    # Assuming service.indexer.conn exists
    if service.indexer and hasattr(service.indexer, 'conn'):
        status, msg, details = health.check_database_schema(service.indexer.conn)
        components.append(ComponentHealthStatus(
            component="database_schema",
            status=status,
            message=msg,
            details=details
        ))
        if status != "healthy":
            overall_status = "degraded" if status == "degraded" else "error"
    
    # 2. Static Files Check
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    static_path = os.path.join(base_dir, 'static')
    status, msg, details = health.check_static_files(static_path)
    components.append(ComponentHealthStatus(
        component="static_assets",
        status=status,
        message=msg,
        details=details
    ))
    if status != "healthy" and overall_status != "error":
         overall_status = "degraded" if status == "degraded" else "error"

    # 3. Telemetry Check
    status, msg, details = health.check_telemetry_connection(service.telemetry)
    components.append(ComponentHealthStatus(
        component="telemetry",
        status=status,
        message=msg,
        details=details
    ))
    if status != "healthy" and overall_status != "error":
        overall_status = "degraded" if status == "degraded" else "error"

    # 4. Data Provider Check
    if service.data_provider:
        status, msg, details = health.check_data_provider_queries(
            service.data_provider, 
            service.universe, 
            service.run_id
        )
        components.append(ComponentHealthStatus(
            component="data_provider",
            status=status,
            message=msg,
            details=details
        ))
        if status != "healthy" and overall_status != "error":
             overall_status = "degraded" if status == "degraded" else "error"

    return SystemHealthResponse(
        overall_status=overall_status,
        components=components,
        timestamp=time.time()
    )
