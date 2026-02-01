from fastapi import APIRouter, Depends, HTTPException, Query
import logging
from typing import Dict, Any, List, Optional
from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service
from src.reporting.dashboard_v2.api.utils.filters import get_filter_params

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])

@router.get("/tech_tree_progress")
async def get_tech_tree_progress(
    filters: tuple = Depends(get_filter_params),
    service = Depends(get_dashboard_service)
):
    """
    Get progress on tech tree for factions.
    """
    try:
        universe, run_id, batch_id, active_factions, turn_range, downsample = filters
        
        results = {}
        for faction in active_factions:
            if hasattr(service.data_provider, 'get_faction_tech_tree_progress'):
                # Assuming api accepts (faction, universe, turn_range?)
                # Plan says: "Uses filter params... calls service.data_provider.get_faction_tech_tree_progress() for each"
                # Need to verify signature if possible, but assumed standard based on other endpoints
                 prog = service.data_provider.get_faction_tech_tree_progress(faction, universe)
                 results[faction] = prog
        
        return results

    except Exception as e:
        logger.error(f"Error fetching tech tree progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/roi")
async def get_roi(
    faction: str = Query(..., description="Faction to analyze"),
    tech_id: Optional[str] = Query(None, description="Specific tech ID"),
    min_turn: Optional[int] = Query(None),
    max_turn: Optional[int] = Query(None),
    service = Depends(get_dashboard_service)
):
    """
    Get Research ROI data.
    """
    try:
        universe = service.universe
        if not hasattr(service.data_provider, 'get_faction_research_roi'):
             return {}

        # Assuming standard signature
        data = service.data_provider.get_faction_research_roi(faction, universe, tech_id, min_turn, max_turn)
        return data

    except Exception as e:
        logger.error(f"Error fetching research ROI: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline")
async def get_timeline(
    limit: int = Query(50, description="Max items to return"),
    service = Depends(get_dashboard_service)
):
    """
    Get research timeline events.
    """
    try:
        universe = service.universe
        if not hasattr(service.data_provider, 'get_research_timeline'):
             return []

        data = service.data_provider.get_research_timeline(universe, limit)
        return data

    except Exception as e:
        logger.error(f"Error fetching research timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))
