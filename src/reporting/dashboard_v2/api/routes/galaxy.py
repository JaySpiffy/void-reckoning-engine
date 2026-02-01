import logging
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import Dict, Any, List

from ..models import (
    GalaxyTopologyResponse,
    ErrorResponse
)
from ..dependencies import get_dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/galaxy", tags=["galaxy"])

@router.get("/topology", response_model=GalaxyTopologyResponse)
async def get_galaxy_topology(
    service=Depends(get_dashboard_service)
):
    """
    Fetch the complete galaxy topology including systems, lanes, and boundaries.
    """
    try:
        if not service.data_provider:
            raise HTTPException(status_code=503, detail="Dashboard Data Provider not initialized")
            
        # Get topology from centralized service method
        topology = service.get_galaxy_topology()
        if not topology or "systems" not in topology or not topology["systems"]:
            # Ensure proper structure for empty topology
            if not topology:
                topology = {}
            if "systems" not in topology:
                topology["systems"] = []
            if "lanes" not in topology:
                topology["lanes"] = []
            if "bounds" not in topology:
                # Default bounds
                topology["bounds"] = {"width": 1000, "height": 1000, "min_x": -500, "min_y": -500}
        
        return topology
        
    except Exception as e:
        logger.error(f"Error fetching galaxy topology: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch topology: {str(e)}")

@router.post("/update")
async def update_galaxy_topology(
    topology: Dict[str, Any] = Body(...),
    service=Depends(get_dashboard_service)
):
    """
    Update galaxy topology (attach/modify galaxy structure).
    """
    try:
        if hasattr(service, 'attach_galaxy'):
            service.attach_galaxy(topology)
            return {"status": "success", "message": "Galaxy topology updated"}
        else:
            raise HTTPException(status_code=501, detail="Attach galaxy not implemented in service")
    except Exception as e:
        logger.error(f"Error updating galaxy topology: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/star_system")
async def get_star_system_details(
    universe: str,
    run_id: str,
    system_name: str = Query(..., alias="name"),
    turn: int = Query(None),
    service=Depends(get_dashboard_service)
):
    """
    Get detailed information about a specific star system.
    """
    try:
        # Placeholder implementation until data provider has specific method
        # Can rely on galaxy snapshot or specific query
        snapshot = service.data_provider.get_galaxy_snapshot(universe, run_id)
        
        system_info = next((s for s in snapshot.get("systems", []) if s.get("name") == system_name), None)
        
        if not system_info:
            # Try efficient look up if snapshot is too heavy or incomplete
            # For now return 404 if not found
             raise HTTPException(status_code=404, detail="System not found")
             
        # Enhance with ownership info if available
        # logic to find owner from snapshot["factions"] or planets
        
        return system_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching system details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
