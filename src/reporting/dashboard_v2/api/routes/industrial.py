import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List

from ..models import (
    IndustrialDensityResponse,
    QueueEfficiencyResponse,
    ConstructionTimelineResponse,
    ResearchTimelineResponse,
    TechProgressResponse,
    ErrorResponse
)
from ..dependencies import get_dashboard_service
from ..utils.filters import get_filter_params, FilterParams

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/industrial", tags=["industrial"])

@router.get("/density", response_model=IndustrialDensityResponse)
async def get_industrial_density(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get industrial density metrics for selected faction(s)."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, turn_range, _ = params
        
        if not requested_factions:
            return {"factions": {}}

        # Logic: If multiple factions, call get_all_factions_industrial_density and filter
        if len(requested_factions) > 1:
            data = service.data_provider.get_all_factions_industrial_density(
                universe, run_id, batch_id, turn_range
            )
            filtered_factions = {f: v for f, v in data.get("factions", {}).items() if f in requested_factions}
            return {"factions": filtered_factions}
        
        # Single faction
        else:
            faction = requested_factions[0]
            # Data provider doesn't have a single-faction density method in the plan?
            # Re-using the all_factions logic filtered down for consistency if needed,
            # or check if get_all_factions_industrial_density is efficient.
            data = service.data_provider.get_all_factions_industrial_density(
                universe, run_id, batch_id, turn_range
            )
            filtered_factions = {f: v for f, v in data.get("factions", {}).items() if f in requested_factions}
            return {"factions": filtered_factions}
            
    except Exception as e:
        logger.error(f"Error in get_industrial_density: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue_efficiency", response_model=QueueEfficiencyResponse)
async def get_queue_efficiency(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get construction queue efficiency for the primary faction."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, turn_range, _ = params
        
        if not requested_factions:
             # Return default empty structure
             return {"turns": [], "efficiency": [], "idle_slots": []}
             
        primary_faction = requested_factions[0]
        data = service.data_provider.get_faction_queue_efficiency(
            universe, run_id, primary_faction, batch_id, turn_range
        )
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_queue_efficiency: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline", response_model=ConstructionTimelineResponse)
async def get_construction_timeline(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params),
    limit: int = Query(50, ge=1, le=200, description="Number of events to retrieve")
):
    """Get recent construction completion events, optionally filtered by faction."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, _, _ = params
        
        data = service.data_provider.get_construction_timeline(
            universe, run_id, batch_id, limit
        )
        
        # Manually filter by faction if requested
        if requested_factions:
            data["events"] = [e for e in data["events"] if e.get("faction") in requested_factions]
        
        return data
        
    except Exception as e:
        logger.error(f"Error in get_construction_timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research_timeline", response_model=ResearchTimelineResponse)
async def get_research_timeline(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params),
    limit: int = Query(50, ge=1, le=200, description="Number of events to retrieve")
):
    """Get recent technological breakthrough events."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, _, _ = params
        
        data = service.data_provider.get_research_timeline(
            universe, run_id, batch_id, limit
        )
        
        # Manually filter by faction if requested
        if requested_factions:
            data["events"] = [e for e in data["events"] if e["faction"] in requested_factions]
            
        return data
        
    except Exception as e:
        logger.error(f"Error in get_research_timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tech_progress", response_model=TechProgressResponse)
async def get_tech_progress(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get tech progression for selected factions."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, turn_range, _ = params
        
        if not requested_factions:
            return {"factions": {}}
            
        # Call data provider for each/all
        # If one faction
        if len(requested_factions) == 1:
            data = service.data_provider.get_faction_tech_tree_progress(
                universe, run_id, requested_factions[0], batch_id, turn_range
            )
            return data
        else:
            data = service.data_provider.get_faction_tech_tree_progress(
                universe, run_id, "all", batch_id, turn_range
            )
            # Filter
            data["factions"] = {f: v for f, v in data["factions"].items() if f in requested_factions}
            return data
            
    except Exception as e:
        logger.error(f"Error in get_tech_progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
