import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any

from ..models import (
    AlertResponse,
    AlertListResponse,
    AlertSummaryResponse,
    AlertSeverityEnum
)
from ..dependencies import get_alert_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("/active", response_model=List[AlertResponse])
async def get_active_alerts(manager=Depends(get_alert_manager)):
    """
    Get all active (unacknowledged and unresolved) alerts.
    """
    try:
        alerts = manager.get_active_alerts()
        return [a.to_dict() for a in alerts]
    except Exception as e:
        logger.error(f"Error fetching active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=AlertListResponse)
async def get_alert_history(
    severity: Optional[List[AlertSeverityEnum]] = Query(None),
    alert_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    manager=Depends(get_alert_manager)
):
    """
    Get paginated alert history with optional severity and type filtering.
    """
    try:
        alerts = manager.history.alerts
        
        # Filter by severity (support multiple)
        if severity:
            severity_values = [s.value for s in severity]
            alerts = [a for a in alerts if a.severity.value in severity_values]

        # Filter by type (substring match on rule_name or context)
        if alert_type and alert_type != 'ALL':
            term = alert_type.lower()
            alerts = [
                a for a in alerts 
                if term in a.rule_name.lower() or 
                   term in str(a.context).lower()
            ]
            
        # Sort by timestamp (newest first)
        alerts = sorted(alerts, key=lambda x: x.timestamp, reverse=True)
        
        total = len(alerts)
        start = (page - 1) * page_size
        end = start + page_size
        
        items = [a.to_dict() for a in alerts[start:end]]
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }
    except Exception as e:
        logger.error(f"Error fetching alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", response_model=AlertSummaryResponse)
async def get_alert_summary(manager=Depends(get_alert_manager)):
    """
    Get alert summary statistics.
    """
    try:
        alerts = manager.history.alerts
        active = manager.get_active_alerts()
        
        by_severity = {
            "info": 0,
            "warning": 0,
            "error": 0,
            "critical": 0
        }
        
        for a in alerts:
            by_severity[a.severity.value] += 1
            
        return {
            "total": len(alerts),
            "active": len(active),
            "by_severity": by_severity
        }
    except Exception as e:
        logger.error(f"Error fetching alert summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, manager=Depends(get_alert_manager)):
    """
    Acknowledge a specific alert.
    """
    try:
        # Search in history
        found = False
        for a in manager.history.alerts:
            if a.id == alert_id:
                a.acknowledged = True
                found = True
                break
        
        if not found:
            raise HTTPException(status_code=404, detail="Alert not found")
            
        return {"status": "success", "message": f"Alert {alert_id} acknowledged"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, manager=Depends(get_alert_manager)):
    """
    Mark a specific alert as resolved.
    """
    try:
        # Search in history
        found = False
        for a in manager.history.alerts:
            if a.id == alert_id:
                a.resolved = True
                found = True
                break
        
        if not found:
            raise HTTPException(status_code=404, detail="Alert not found")
            
        return {"status": "success", "message": f"Alert {alert_id} resolved"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
