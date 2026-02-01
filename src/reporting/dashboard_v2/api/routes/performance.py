from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from src.reporting.dashboard_v2.api.models import PerformanceStatsResponse, ProfilingStats, SlowQuery
from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service
from src.reporting.dashboard_v2.api.utils.performance_monitor import PerformanceMonitor

router = APIRouter(prefix="/api/performance", tags=["performance"])

@router.get("/stats", response_model=PerformanceStatsResponse)
async def get_performance_stats(service = Depends(get_dashboard_service)):
    """
    Get aggregated performance statistics.
    """
    try:
        # 1. Get Memory Stats
        memory_stats = PerformanceMonitor.get_memory_stats()
        
        # 2. Get Cache Stats
        # Use service's cache manager if available, otherwise pass None
        # Assuming DashboardService has a cache_manager attribute or access to it
        cache_manager = getattr(service, 'cache_manager', None)
        # Fallback: if service doesn't have it directly, check indexer's cache
        if not cache_manager and getattr(service, 'indexer', None) and hasattr(service.indexer, 'cache'):
            cache_manager = service.indexer.cache
            
        cache_stats = PerformanceMonitor.get_cache_stats(cache_manager)
        
        # 3. Get Profiling Stats
        # Get engine from service. If the engine isn't directly exposed, use indexer as proxy or similar
        engine = getattr(service, 'engine', None)
        if not engine and getattr(service, 'indexer', None):
             engine = service.indexer # Fallback if indexer acts as engine interface
             
        profiling_stats = PerformanceMonitor.get_profiling_stats(engine)
        
        return PerformanceStatsResponse(
            memory=memory_stats,
            cache=cache_stats,
            profiling=profiling_stats,
            profiling_enabled=profiling_stats["enabled"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance stats: {str(e)}")

@router.post("/profiling/enable")
async def enable_profiling(service = Depends(get_dashboard_service)):
    """
    Enable query profiling.
    """
    engine = getattr(service, 'engine', getattr(service, 'indexer', None))
    
    if not engine:
        raise HTTPException(status_code=503, detail="Engine/Indexer not available")
    
    success = PerformanceMonitor.enable_profiling(engine)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to enable profiling")
        
    return {"status": "enabled"}

@router.post("/profiling/disable")
async def disable_profiling(service = Depends(get_dashboard_service)):
    """
    Disable query profiling.
    """
    engine = getattr(service, 'engine', getattr(service, 'indexer', None))
    
    if not engine:
        raise HTTPException(status_code=503, detail="Engine/Indexer not available")
    
    success = PerformanceMonitor.disable_profiling(engine)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to disable profiling")
        
    return {"status": "disabled"}

@router.get("/slow_queries", response_model=List[SlowQuery])
async def get_slow_queries(
    threshold_ms: float = 100.0,
    service = Depends(get_dashboard_service)
):
    """
    Get list of slow queries.
    """
    engine = getattr(service, 'engine', getattr(service, 'indexer', None))
    if not engine:
        return []
        
    queries = PerformanceMonitor.detect_slow_queries(engine, threshold_ms)
    return [SlowQuery(**q) for q in queries]
