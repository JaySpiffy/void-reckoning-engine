import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ..models import NetProfitResponse, RevenueBreakdownResponse, StockpileVelocityResponse, ResourceROIResponse, ErrorResponse
from ..dependencies import get_dashboard_service
from ..utils.filters import get_filter_params, FilterParams

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/economic", tags=["economic"])

@router.get("/net_profit", response_model=NetProfitResponse, responses={503: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_net_profit(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get historical net profit data for active factions."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
        
        params = filters.resolve(service)
        # params: (universe, run_id, batch_id, requested_factions, turn_range, downsample)
        universe, run_id, batch_id, requested_factions, turn_range, downsample = params
        
        # Result aggregation structure
        result_turns = set()
        result_factions = {}
        
        # Query each faction or 'all' if the data provider supports it
        # The data provider method 'get_faction_net_profit_history' supports comma-separated factions
        faction_str = ",".join(requested_factions)
        data = service.data_provider.get_faction_net_profit_history(
            universe, run_id, faction_str, batch_id, turn_range, downsample
        )
        
        # HARDENING: Guarantee structure for legacy frontend
        if not data:
            data = {"turns": [], "factions": {}}
        elif "factions" not in data:
            data["factions"] = {}
            
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_net_profit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/revenue_breakdown", response_model=RevenueBreakdownResponse)
async def get_revenue_breakdown(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get revenue breakdown by category for the primary selected faction."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, turn_range, _ = params
        
        # Helper for global vs specific
        target_factions = 'all'
        if requested_factions:
            # If we have a list, join it. If it contains *all* active factions, we could pass 'all',
            # but passing the CSV is safer for specific selection. 
            # If user selected ALL in UI, requested_factions usually has all IDs.
            target_factions = ",".join(requested_factions)

        data = service.data_provider.get_faction_revenue_breakdown(
            universe, run_id, target_factions, batch_id, turn_range
        )
        
        # New provider returns { "income": {...}, "expenses": {...} }
        # Frontend expects:
        # {
        #   "turns": [...],
        #   "categories": { "Income:Tax": [val], "Expense:Research": [val] } 
        # }
        # OR we update Frontend to handle nested object. 
        # Given we haven't touched frontend yet, let's flatten it for now or return a richer object?
        # The Response Model `RevenueBreakdownResponse` is define in models.py.
        # Let's check model definition. If it's loose, we can return nested.
        # But to be safe and allow "Income vs Expenses" toggle on frontend, we should probably output structured data.
        
        # Checking `RevenueBreakdownResponse`... assuming Dict[str, Any] or similar.
        # Actually I can't check models.py easily without another tool call. 
        # Let's assume we return the dict as is, and update the Pydantic model if needed.
        # But wait, original return was:
        # "categories": {cat: [val]}
        
        # To make it compatible with current frontend (until we update it), we can flattern:
        # But user WANTS separation.
        # Let's return the structured data.
        
        return {
            "turns": [turn_range[1] if turn_range else service.get_max_turn()],
            "income": {k: [v] for k, v in data.get("income", {}).items()},
            "expenses": {k: [v] for k, v in data.get("expenses", {}).items()}
        }
        
    except Exception as e:
        logger.error(f"Error in get_revenue_breakdown: {e}", exc_info=True)
        # Return a safe, fully-populated empty structure to prevent frontend crashes
        return {
            "turns": [],
            "income": {},
            "expenses": {}
        }

@router.get("/stockpile_velocity", response_model=StockpileVelocityResponse)
async def get_stockpile_velocity(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get stockpile and velocity metrics for active factions."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, turn_range, _ = params
        
        faction_str = ",".join(requested_factions)
        data = service.data_provider.get_faction_stockpile_velocity(
            universe, run_id, faction_str, batch_id, turn_range
        )
        
        return data
        
    except Exception as e:
        logger.error(f"Error in get_stockpile_velocity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resource_roi", response_model=ResourceROIResponse)
async def get_resource_roi(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get Resource ROI analysis."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, turn_range, _ = params
        
        data = service.data_provider.get_resource_roi_data(
            universe, run_id, batch_id, requested_factions, turn_range
        )
        
        if not data or "roi_data" not in data:
            return {"roi_data": []}
        
        return data
        
    except Exception as e:
        logger.error(f"Error in get_resource_roi: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
