import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, Dict, Any

from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service
from src.reporting.dashboard_v2.api.models import (
    StatusResponse, HealthResponse, MaxTurnResponse, WebSocketHealthResponse, ErrorResponse
)
from src.reporting.dashboard_v2.api.config import settings
from src.reporting.dashboard_v2.api.utils.health_checks import (
    check_database_schema, check_static_files, 
    check_data_provider_queries, check_telemetry_connection
)

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from src.reporting.dashboard_v2.api.websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["status"])

@router.get("/status", response_model=StatusResponse)
async def get_status(service=Depends(get_dashboard_service)):
    """Return current dashboard status."""
    try:
        status = service.get_status()
        status["streaming"] = service.telemetry is not None
        return status
    except RuntimeError as e:
        logger.error(f"Service not initialized: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error in /api/status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def get_health(detailed: bool = Query(False), service=Depends(get_dashboard_service)):
    """Diagnostic health check for the dashboard and its components."""
    try:
        health = service.get_health_status()
        
        if detailed:
            details = {}
            
            # Static Files
            s_status, s_msg, s_det = check_static_files(settings.STATIC_FOLDER)
            details["static_files"] = {"status": s_status, "message": s_msg, "details": s_det}
            
            # Database Schema
            if service.indexer and hasattr(service.indexer, 'conn'):
                 d_status, d_msg, d_det = check_database_schema(service.indexer.conn)
                 details["db_schema"] = {"status": d_status, "message": d_msg, "details": d_det}
            
            # Data Provider Queries
            if service.data_provider:
                 dp_status, dp_msg, dp_det = check_data_provider_queries(
                     service.data_provider, service.universe, service.run_id
                 )
                 details["query_perf"] = {"status": dp_status, "message": dp_msg, "details": dp_det}
            
            # Telemetry Connection
            t_status, t_msg, t_det = check_telemetry_connection(service.telemetry)
            details["telemetry"] = {"status": t_status, "message": t_msg, "details": t_det}
            if t_status != "healthy":
                health["status"] = "degraded"
                
            health["detailed_checks"] = details
        
        if health["status"] != "healthy":
            return JSONResponse(
                status_code=503,
                content=jsonable_encoder(health)
            )
            
        return health
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.warning(f"Health check failed (Service uninitialized): {e}")
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "error": str(e)})
    except Exception as e:
        logger.error(f"Health check critical failure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"status": "critical", "error": str(e)})

@router.get("/run/max_turn", response_model=MaxTurnResponse)
async def get_max_turn(
    universe: Optional[str] = None, 
    run_id: Optional[str] = None, 
    service=Depends(get_dashboard_service)
):
    """Get the maximum turn for the specified or current context."""
    try:
        universe = universe or service.universe
        run_id = run_id or service.run_id
        
        if not service.data_provider:
             logger.warning("Max turn requested but Data Provider not initialized")
             return {"max_turn": 0, "warning": "Data provider unavailable"}
             
        max_turn = service.data_provider.get_max_turn(universe, run_id)
        return {"max_turn": max_turn}
    except Exception as e:
        logger.error(f"Error getting max turn: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/websocket/health", response_model=Dict[str, Any])
async def get_websocket_health(service=Depends(get_dashboard_service)):
    """Check health of the WebSocket/Streaming subsystem."""
    try:
        # Check streaming thread (legacy compatibility if exists)
        stream_active = service.stream_thread is not None and service.stream_thread.is_alive()
        
        # New connection count from manager
        conn_count = len(manager.active_connections)
        
        return {
            "status": "healthy" if (stream_active or conn_count >= 0) else "degraded",
            "streaming_thread": stream_active,
            "connection_count": conn_count,
            "async_mode": "FastAPI WebSockets",
            "ping_interval": settings.WEBSOCKET_PING_INTERVAL
        }
    except Exception as e:
        logger.error(f"Error in /api/websocket/health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"status": "error", "error": str(e)})
