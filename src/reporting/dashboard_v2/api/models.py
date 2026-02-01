from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import time

# --- Error Models ---

class ErrorResponse(BaseModel):
    """Generic error response model."""
    error: str
    details: Optional[str] = None
    type: Optional[str] = None

# --- Status Models ---

class StatusResponse(BaseModel):
    """Response model for /api/status."""
    status: str
    universe: str
    run_id: str
    batch_id: str
    paused: bool
    telemetry_connected: bool
    indexer_connected: bool
    streaming: bool

class HealthComponentStatus(BaseModel):
    """Status information for an individual system component."""
    status: str
    error: Optional[str] = None
    latency_ms: Optional[str] = None

class HealthSystemMemory(BaseModel):
    """Memory usage information."""
    rss_mb: float
    vms_mb: float

class HealthSystemInfo(BaseModel):
    """System resource information."""
    memory: Optional[HealthSystemMemory] = None
    active_threads: int

class HealthContextInfo(BaseModel):
    """Dashboard context information."""
    universe: str
    run_id: str

class HealthResponse(BaseModel):
    """Response model for /api/health."""
    status: str
    timestamp: float
    components: Dict[str, Any] # Flexible as it can contain dynamic components
    system: HealthSystemInfo
    context: HealthContextInfo
    detailed_checks: Optional[Dict[str, Any]] = None

class MaxTurnResponse(BaseModel):
    """Response model for /api/run/max_turn."""
    max_turn: int
    warning: Optional[str] = None

class WebSocketHealthResponse(BaseModel):
    """Response model for /api/websocket/health."""
    status: str
    streaming_thread: bool
    async_mode: str
    ping_interval: Any # Can be int or "unknown"

# --- Galaxy Models ---

class GalaxySystem(BaseModel):
    """System information for the galaxy map."""
    name: str
    x: float
    y: float
    owner: str
    control: Dict[str, int]
    total_planets: int
    node_count: int

class GalaxyLane(BaseModel):
    """Link between two systems."""
    source: str
    target: str

class GalaxyBounds(BaseModel):
    """Map boundaries."""
    width: float
    height: float
    min_x: float = 0.0
    min_y: float = 0.0

class GalaxyTopologyResponse(BaseModel):
    """Response model for galaxy topology."""
    systems: List[GalaxySystem]
    lanes: List[GalaxyLane]
    bounds: GalaxyBounds

# --- Metrics Models ---

class BattleMetrics(BaseModel):
    """Metrics for battles."""
    rate: float
    total: int

class UnitRates(BaseModel):
    """Rates for unit types, keyed by faction."""
    navy: float = 0.0
    army: float = 0.0

class UnitsMetrics(BaseModel):
    """Metrics for units."""
    spawn_rate: Dict[str, UnitRates]
    loss_rate: Dict[str, UnitRates]
    total_spawned: int
    total_lost: int

class ConstructionMetrics(BaseModel):
    """Metrics for construction."""
    rate: Dict[str, float]
    total: int

class EconomyMetrics(BaseModel):
    """Metrics for economy."""
    flow_rate: Dict[str, float]
    total_revenue: float
    upkeep_breakdown: Dict[str, float]

class EconomicHealthData(BaseModel):
    """Detailed economic health indicators."""
    net_profit: Optional[float] = 0.0
    gross_income: Optional[float] = 0.0
    total_upkeep: Optional[float] = 0.0
    stockpile_velocity: Optional[float] = 0.0
    revenue_breakdown: Optional[Dict[str, float]] = Field(default_factory=dict)

class BattlePerformanceData(BaseModel):
    """Metrics for battle performance."""
    avg_cer: Optional[float] = 0.0
    latest_composition: Optional[Dict[str, int]] = Field(default_factory=dict)
    latest_attrition: Optional[float] = 0.0
    recent_battle_count: Optional[int] = 0

class ConstructionActivityData(BaseModel):
    """Detailed construction activity."""
    building_types: Optional[Dict[str, int]] = Field(default_factory=dict)
    avg_idle_slots: Optional[float] = 0.0
    avg_queue_efficiency: Optional[float] = 0.0

class ResearchImpactData(BaseModel):
    """Metrics for research impact."""
    latest_tech: Optional[str] = "None"
    latest_deltas: Optional[Dict[str, float]] = Field(default_factory=dict)
    recent_count: Optional[int] = 0

class LiveMetricsResponse(BaseModel):
    """Comprehensive live metrics response."""
    battles: Optional[BattleMetrics] = None
    units: Optional[UnitsMetrics] = None
    construction: Optional[ConstructionMetrics] = None
    economy: Optional[EconomyMetrics] = None
    economic_health: Optional[EconomicHealthData] = None
    battle_performance: Optional[BattlePerformanceData] = None
    construction_activity: Optional[ConstructionActivityData] = None
    research_impact: Optional[ResearchImpactData] = None
    turn: Optional[int] = None
    faction_status: Optional[Any] = None # Union[Dict, List] to handle empty list
    planet_status: Optional[Any] = None # Union[Dict, List] to handle empty list
    
    # Backwards Compatibility Fields
    battles_per_sec: Optional[float] = None
    spawn_rates_per_sec: Optional[Dict[str, Any]] = None
    loss_rates_per_sec: Optional[Dict[str, Any]] = None

# --- Economic Analysis Models ---

class NetProfitData(BaseModel):
    """Profit metrics for a single faction."""
    gross_income: List[float]
    upkeep: List[float]
    net_profit: List[float]

class NetProfitResponse(BaseModel):
    """Response model for /api/economic/net_profit."""
    turns: List[int]
    factions: Dict[str, NetProfitData]

class RevenueBreakdownResponse(BaseModel):
    """Response model for /api/economic/revenue_breakdown."""
    turns: List[int]
    income: Dict[str, List[float]]
    expenses: Dict[str, List[float]]

class StockpileVelocityData(BaseModel):
    """Stockpile and velocity metrics for a single faction."""
    stockpile: List[float]
    velocity: List[float]

class StockpileVelocityResponse(BaseModel):
    """Response model for /api/economic/stockpile_velocity."""
    turns: List[int]
    factions: Dict[str, StockpileVelocityData]

class ResourceROIResponse(BaseModel):
    """Response model for /api/economic/resource_roi."""
    roi_data: List[Dict[str, Any]]

# --- Military Analysis Models ---

class CombatEffectivenessData(BaseModel):
    """Combat effectiveness metrics."""
    cer: float

class CombatEffectivenessResponse(BaseModel):
    """Response model for /api/military/combat_effectiveness (multi-faction)."""
    factions: Dict[str, CombatEffectivenessData]

class CombatEffectivenessTimeSeriesResponse(BaseModel):
    """Response model for /api/military/combat_effectiveness (single-faction)."""
    turns: List[int]
    values: List[float]

class ForceCompositionResponse(BaseModel):
    """Response model for /api/military/force_composition."""
    composition: Dict[str, int]

class AttritionRateData(BaseModel):
    """Attrition rate time series for a single faction."""
    turns: List[int]
    attrition: List[float]

class AttritionRateResponse(BaseModel):
    """Response model for /api/military/attrition_rate."""
    factions: Dict[str, AttritionRateData]

class BattleHeatmapEntry(BaseModel):
    """A single entry in the battle efficiency heatmap."""
    system: str
    faction: str
    cer: float
    battle_count: int

class BattleHeatmapResponse(BaseModel):
    """Response model for /api/military/battle_heatmap."""
    heatmap: List[BattleHeatmapEntry]

class FleetPowerData(BaseModel):
    """Fleet power time series for a single faction."""
    turns: List[int]
    power: List[float]

class FleetPowerResponse(BaseModel):
    """Response model for /api/military/fleet_power."""
    factions: Dict[str, FleetPowerData]

# --- Industrial Analysis Models ---

class IndustrialDensityData(BaseModel):
    """Building type distribution for a single faction."""
    building_counts: Dict[str, int]

class IndustrialDensityResponse(BaseModel):
    """Response model for /api/industrial/density."""
    factions: Dict[str, IndustrialDensityData]

class QueueEfficiencyResponse(BaseModel):
    """Response model for /api/industrial/queue_efficiency."""
    turns: List[int]
    efficiency: List[float]
    idle_slots: List[float]

class ConstructionEvent(BaseModel):
    """A single construction timeline event."""
    turn: int
    faction: str
    building: str
    planet: str

class ConstructionTimelineResponse(BaseModel):
    """Response model for /api/industrial/timeline."""
    events: List[ConstructionEvent]

class ResearchEvent(BaseModel):
    """A single research timeline event."""
    turn: int
    faction: str
    tech: str

class ResearchTimelineResponse(BaseModel):
    """Response model for /api/industrial/research_timeline."""
    events: List[ResearchEvent]

class TechProgressResponse(BaseModel):
    """Response model for /api/industrial/tech_progress."""
    factions: Dict[str, Dict[str, Any]]

class WSMessage(BaseModel):
    """Base model for all WebSocket messages."""
    type: str
    timestamp: float = Field(default_factory=time.time)
    data: Optional[Dict[str, Any]] = None

class WSStatusUpdate(WSMessage):
    """Event for dashboard status updates."""
    type: str = "status_update"
    data: StatusResponse

class WSSnapshot(WSMessage):
    """Event for full dashboard state snapshot."""
    type: str = "snapshot"
    data: Dict[str, Any]

class WSMetricsUpdate(WSMessage):
    """Periodic event for live metrics updates."""
    type: str = "metrics_update"
    data: LiveMetricsResponse

class WSEventStream(WSMessage):
    """Event for streaming telemetry events."""
    type: str = Field(default="event_stream")
    data: Dict[str, Any]

class WSErrorNotification(WSMessage):
    """Event for broadcasting errors to clients."""
    type: str = "error_notification"
    data: ErrorResponse

class WSPingPong(WSMessage):
    """Message for connection health checks."""
    type: str = "ping" # or "pong"

class WSRequest(BaseModel):
    """Client-initiated request via WebSocket."""
    type: str
    request_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class WSResponse(BaseModel):
    """Server response to a client-initiated request."""
    type: str = "response"
    request_id: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    
# --- Alert Models ---

class AlertSeverityEnum(str, Enum):
    """Enumeration of alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertResponse(BaseModel):
    """Response model for a single alert."""
    id: str
    timestamp: datetime
    severity: AlertSeverityEnum
    rule_name: str
    message: str
    context: Dict[str, Any] = {}
    acknowledged: bool = False
    resolved: bool = False

class AlertListResponse(BaseModel):
    """Response model for alert list/history."""
    total: int
    page: int
    page_size: int
    items: List[AlertResponse]

class AlertSummaryResponse(BaseModel):
    """Response model for alert summary statistics."""
    total: int
    active: int
    by_severity: Dict[str, int]

class WSAlertTriggered(WSMessage):
    """WebSocket event for a newly triggered alert."""
    type: str = "alert_triggered"
    data: AlertResponse

# --- Performance & Diagnostics Models ---

class MemoryStats(BaseModel):
    """Memory usage statistics."""
    rss_mb: float
    vms_mb: float
    percent: float
    available_mb: float

class CacheStats(BaseModel):
    """Cache performance statistics."""
    hit_rate: float
    registered_caches: int
    clear_count: int
    warm_count: int
    named_caches: List[str]

class SlowQuery(BaseModel):
    """Details of a slow query operation."""
    metric: str
    duration_ms: float
    timestamp: str

class ProfilingStats(BaseModel):
    """Query profiling status and statistics."""
    enabled: bool
    slow_queries: int
    slow_query_threshold_ms: float
    recent_slow_queries: List[SlowQuery]

class PerformanceStatsResponse(BaseModel):
    """Aggregate performance dashboard data."""
    memory: MemoryStats
    cache: CacheStats
    profiling: ProfilingStats
    profiling_enabled: bool

class DiagnosticsResponse(BaseModel):
    """Application diagnostics information."""
    static_folder: str
    static_url_path: str
    files: Dict[str, Any]

class ComponentHealthStatus(BaseModel):
    """Health status of a specific component."""
    component: str
    status: str # healthy, degraded, error
    message: str
    details: Optional[Dict[str, Any]] = None

class SystemHealthResponse(BaseModel):
    """Comprehensive system health report."""
    overall_status: str # healthy, degraded, error
    components: List[ComponentHealthStatus]
    timestamp: float = Field(default_factory=time.time)
class ControlStatusResponse(BaseModel):
    status: str
    paused: bool
    running: bool

class ControlActionResponse(BaseModel):
    status: str
    action: str
    paused: Optional[bool] = None
