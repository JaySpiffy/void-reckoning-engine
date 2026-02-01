from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service

router = APIRouter(prefix="/api/runs", tags=["runs"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_runs(
    universe: Optional[str] = Query(None, description="Filter by universe"),
    service = Depends(get_dashboard_service)
):
    """
    Get a list of available simulation runs.
    """
    try:
        # Prefer DashboardService internal discovery
        if hasattr(service, 'get_available_runs'):
            return service.get_available_runs(universe)
            
        if not service.data_provider:
             raise HTTPException(status_code=503, detail="Data provider unavailable")
             
        # Use database directly via indexer if data_provider wrapper is missing specific method
        runs = []
        if hasattr(service.data_provider, 'get_runs'):
            runs = service.data_provider.get_runs(universe)
        elif service.indexer:
             # Fallback to direct DB query if provider method missing
             cursor = service.indexer.conn.cursor()
             query = "SELECT run_id, batch_id, universe, started_at, turns_taken, winner FROM runs"
             params = []
             if universe:
                 query += " WHERE universe = ?"
                 params.append(universe)
             query += " ORDER BY started_at DESC"
             
             cursor.execute(query, params)
             columns = [d[0] for d in cursor.description]
             runs = [dict(zip(columns, row)) for row in cursor.fetchall()]
             
        return runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
