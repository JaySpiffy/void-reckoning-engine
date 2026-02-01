from fastapi import APIRouter, Depends, HTTPException, Body
import logging
from typing import Optional
from fastapi.concurrency import run_in_threadpool
from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service
from src.reporting.dashboard_v2.api.models import ControlStatusResponse, ControlActionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/control", tags=["control"])

@router.post("/pause", response_model=ControlActionResponse)
async def pause_simulation(service = Depends(get_dashboard_service)):
    """
    Pause the simulation.
    """
    try:
        # Assuming service has pause_simulation
        service.pause_simulation()
        return ControlActionResponse(
            status="success",
            action="pause",
            paused=True
        )
    except Exception as e:
        logger.error(f"Error pausing simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resume", response_model=ControlActionResponse)
async def resume_simulation(service = Depends(get_dashboard_service)):
    """
    Resume the simulation.
    """
    try:
        service.resume_simulation()
        return ControlActionResponse(
            status="success",
            action="resume",
            paused=False
        )
    except Exception as e:
        logger.error(f"Error resuming simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/step", response_model=ControlActionResponse)
async def step_simulation(service = Depends(get_dashboard_service)):
    """
    Example single step.
    """
    try:
        service.trigger_step()
        return ControlActionResponse(
            status="success",
            action="step"
        )
    except Exception as e:
        logger.error(f"Error triggering step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=ControlStatusResponse)
async def get_control_status(service = Depends(get_dashboard_service)):
    """
    Get current simulation control status.
    """
    try:
        paused = service.control_paused
        # Assuming service knows if it's 'running' (loop active) - defaulting to True if unspecified
        running = getattr(service, 'running', True) 
        
        return ControlStatusResponse(
            status="paused" if paused else "running",
            paused=paused,
            running=running
        )
    except Exception as e:
        logger.error(f"Error getting control status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/launch")
async def launch_run(
    universe: str = Body(...), 
    config_file: str = Body(...), 
    service = Depends(get_dashboard_service)
):
    """
    Launch a new simulation run.
    """
    try:
        pid = service.launch_simulation(universe, config_file)
        return {"status": "success", "pid": pid, "message": f"Simulation started (PID: {pid})"}
    except Exception as e:
        logger.error(f"Error launching run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configs")
async def list_configs():
    """List available config files."""
    import os
    import glob
    
    try:
        # Search in /app/config or ./config depending on env
        # Since we run from root, ./config is correct
        config_files = glob.glob("config/*.json")
        # Normalize paths
        return {"configs": [f.replace("\\", "/") for f in config_files]}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.post("/switch")
async def switch_run_endpoint(
    payload: dict = Body(...),
    service = Depends(get_dashboard_service)
):
    """
    Switch dashboard context to a specific run.
    """
    run_id = payload.get("run_id")
    if not run_id:
        raise HTTPException(status_code=400, detail="Missing run_id")
        
    try:
        # Offload blocking switch_run to threadpool to prevent event loop freeze
        await run_in_threadpool(service.switch_run, run_id)
        return {"status": "success", "message": f"Switched to run {run_id}", "run_id": run_id}
    except Exception as e:
        logger.error(f"Error switching run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/universes")
async def list_universes_endpoint():
    """List available universes."""
    try:
        from src.core.config import list_available_universes
        return {"universes": list_available_universes()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
