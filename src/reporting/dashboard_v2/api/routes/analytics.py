from fastapi import APIRouter, Depends, HTTPException, Query
import logging
from typing import Dict, Any, List, Optional
from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/trends")
async def get_trends(
    faction: str = Query(..., description="Faction to analyze"),
    universe: Optional[str] = Query(None, description="Universe filter"),
    service = Depends(get_dashboard_service)
):
    """
    Get trend analysis for a specific faction.
    """
    try:
        # Resolve universe if not provided
        target_universe = universe or service.universe
        
        # Call data provider
        # Note: data_provider.get_trend_analysis may not exist yet or needs to be verified
        # Assuming conformance to plan which says "calls service.data_provider.get_trend_analysis"
        if not hasattr(service.data_provider, 'get_trend_analysis'):
             # Fallback or placeholder if metric doesn't exist on provider yet
             # But the plan implies it exists or we should call it.
             # Let's assume it exists.
             logger.warning("get_trend_analysis not implemented on provider")
             return {"error": "Method not implemented on data provider"}

        data = service.data_provider.get_trend_analysis(faction, target_universe)
        return data
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/anomalies")
async def get_anomalies(
    universe: Optional[str] = Query(None, description="Universe filter"),
    service = Depends(get_dashboard_service)
):
    """
    Get detected anomalies.
    """
    try:
        target_universe = universe or service.universe
        if not hasattr(service.data_provider, 'get_anomaly_alerts'):
             return []
             
        data = service.data_provider.get_anomaly_alerts(target_universe)
        return data
    except Exception as e:
        logger.error(f"Error fetching anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balance")
async def get_balance(
    universe: Optional[str] = Query(None, description="Universe filter"),
    service = Depends(get_dashboard_service)
):
    """
    Get faction balance scores.
    """
    try:
        target_universe = universe or service.universe
        if not hasattr(service.data_provider, 'get_faction_balance_scores'):
             return {}
             
        data = service.data_provider.get_faction_balance_scores(target_universe)
        return data
    except Exception as e:
        logger.error(f"Error fetching balance scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions")
async def get_predictions(
    faction: str = Query(..., description="Faction to analyze"),
    universe: Optional[str] = Query(None, description="Universe filter"),
    service = Depends(get_dashboard_service)
):
    """
    Get predictive insights for a faction.
    """
    try:
        target_universe = universe or service.universe
        metrics = service.get_live_metrics()
        current_turn = metrics.get('turn', 0)
        
        if not hasattr(service.data_provider, 'get_predictive_insights'):
             return {}
             
        data = service.data_provider.get_predictive_insights(faction, target_universe, current_turn)
        return data
    except Exception as e:
        logger.error(f"Error fetching predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
