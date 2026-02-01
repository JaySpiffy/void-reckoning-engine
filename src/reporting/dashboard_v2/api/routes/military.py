import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Union, List

from ..models import (
    CombatEffectivenessResponse, 
    CombatEffectivenessTimeSeriesResponse,
    ForceCompositionResponse,
    AttritionRateResponse,
    BattleHeatmapResponse,
    BattleHeatmapEntry,
    FleetPowerResponse,
    FleetPowerData,
    ErrorResponse
)
from ..dependencies import get_dashboard_service
from ..utils.filters import get_filter_params, FilterParams

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/military", tags=["military"])

@router.get("/combat_effectiveness", response_model=Union[CombatEffectivenessResponse, CombatEffectivenessTimeSeriesResponse])
async def get_combat_effectiveness(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get combat effectiveness metrics for selected faction(s)."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, turn_range, downsample = params
        
        if not requested_factions:
            return {"turns": [], "values": []}

        # Multi-faction view (Comparison)
        if len(requested_factions) > 1:
            data = service.data_provider.get_all_factions_combat_effectiveness(
                universe, run_id, batch_id, turn_range
            )
            # Filter results to only requested ones
            filtered_factions = {f: v for f, v in data.get("factions", {}).items() if f in requested_factions}
            return {"factions": filtered_factions}
        
        # Single-faction view (TimeSeries)
        else:
            faction = requested_factions[0]
            data = service.data_provider.get_faction_combat_effectiveness(
                universe, run_id, faction, batch_id, turn_range, downsample
            )
            return data
            
    except Exception as e:
        logger.error(f"Error in get_combat_effectiveness: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/force_composition", response_model=ForceCompositionResponse)
async def get_force_composition(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get force composition aggregation for the primary faction."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, turn_range, _ = params
        
        if not requested_factions:
             # Return default empty structure
             return {"composition": {}}
             
        primary_faction = requested_factions[0]
        data = service.data_provider.get_faction_force_composition(
            universe, run_id, primary_faction, batch_id, turn_range
        )
        
        return {"composition": data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_force_composition: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/attrition_rate", response_model=AttritionRateResponse)
async def get_attrition_rate(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get attrition rate over time for active factions."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, turn_range, _ = params
        
        factions_result = {}
        for f in requested_factions:
            data = service.data_provider.get_faction_attrition_rate(
                universe, run_id, f, batch_id, turn_range
            )
            if data["turns"]:
                factions_result[f] = data
                
        return {"factions": factions_result}
        
    except Exception as e:
        logger.error(f"Error in get_attrition_rate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/battle_heatmap", response_model=BattleHeatmapResponse)
async def get_battle_heatmap(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get battle locations and effectiveness for heatmap analysis."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, _, turn_range, _ = params
        
        data = service.data_provider.get_battle_efficiency_heatmap(
            universe, run_id, batch_id, turn_range
        )
        
        return {"heatmap": data}
        
    except Exception as e:
        logger.error(f"Error in get_battle_heatmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fleet_power", response_model=FleetPowerResponse)
async def get_fleet_power(
    service=Depends(get_dashboard_service),
    filters: FilterParams = Depends(get_filter_params)
):
    """Get fleet power over time for active factions."""
    try:
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
             
        params = filters.resolve(service)
        universe, run_id, batch_id, requested_factions, turn_range, _ = params
        
        factions_result = {}
        for f in requested_factions:
            data = service.data_provider.get_faction_fleet_power(
                universe, run_id, f, batch_id, turn_range
            )
            if data["turns"]:
                factions_result[f] = data
                
        return {"factions": factions_result}
        
    except Exception as e:
        logger.error(f"Error in get_fleet_power: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
