import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any

from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service, get_telemetry_collector
from src.reporting.dashboard_v2.api.models import LiveMetricsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("/live", response_model=LiveMetricsResponse)
async def get_live_metrics(service=Depends(get_dashboard_service)):
    """
    Get current live metrics from telemetry.
    Returns cached real-time performance indicators and current simulation state.
    """
    try:
        data = service.get_live_metrics()
        # The service already handles backwards compatibility for some fields.
        # LiveMetricsResponse will validate the nested structures.
        return data
    except RuntimeError as e:
        logger.error(f"Metrics service unavailable: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching live metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/telemetry/ingest")
async def ingest_telemetry_events(
    batch_id: str = Body(...),
    events: List[Dict[str, Any]] = Body(...),
    service=Depends(get_dashboard_service),
    collector=Depends(get_telemetry_collector)
):
    """
    Ingest a batch of telemetry events from a remote source.
    Synchronizes processing and updates live metrics buffers.
    """
    try:
        # Sync batch_id if it was unknown
        if service.batch_id == "unknown" and batch_id:
            logger.info(f"Dashboard synchronized with batch_id: {batch_id}")
            service.batch_id = batch_id
            
        processed_count = 0
        for event in events:
            try:
                service.process_remote_event(event)
                processed_count += 1
            except Exception as e:
                logger.warning(f"Failed to process remote event: {e}")
                
        return {
            "status": "success",
            "processed": processed_count,
            "total": len(events),
            "batch_id": batch_id
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Telemetry ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
