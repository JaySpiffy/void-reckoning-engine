/**
 * Comprehensive TypeScript interfaces for the Dashboard API.
 * Matching FastAPI Pydantic models exactly.
 */

// --- Error Models ---

export interface ErrorResponse {
    error: string;
    details?: string;
    type?: string;
}

// --- Status Models ---

export interface StatusResponse {
    status: string;
    universe: string;
    run_id: string;
    batch_id: string;
    paused: boolean;
    telemetry_connected: boolean;
    indexer_connected: boolean;
    streaming: boolean;
}

export interface HealthComponentStatus {
    status: string;
    error?: string;
    latency_ms?: string;
}

export interface HealthSystemMemory {
    rss_mb: number;
    vms_mb: number;
}

export interface HealthSystemInfo {
    memory: HealthSystemMemory | null;
    active_threads: number;
}

export interface HealthContextInfo {
    universe: string;
    run_id: string;
}

export interface HealthResponse {
    status: string;
    timestamp: number;
    components: Record<string, any>;
    system: HealthSystemInfo;
    context: HealthContextInfo;
    detailed_checks?: Record<string, any>;
}

export interface MaxTurnResponse {
    max_turn: number;
    warning?: string;
}

export interface WebSocketHealthResponse {
    status: string;
    streaming_thread: boolean;
    connection_count: number;
    async_mode: string;
    ping_interval: number;
}

// --- Galaxy Models ---

export interface GalaxySystem {
    name: string;
    x: number;
    y: number;
    owner: string;
    control: Record<string, number>;
    total_planets: number;
    node_count: number;
}

export interface GalaxyLane {
    source: string;
    target: string;
}

export interface GalaxyBounds {
    width: number;
    height: number;
    min_x: number;
    min_y: number;
}

export interface GalaxyTopologyResponse {
    systems: GalaxySystem[];
    lanes: GalaxyLane[];
    bounds: GalaxyBounds;
}

// --- Metrics Models ---

export interface BattleMetrics {
    rate: number;
    total: number;
}

export interface UnitRates {
    navy: number;
    army: number;
}

export interface UnitsMetrics {
    spawn_rate: Record<string, UnitRates>;
    loss_rate: Record<string, UnitRates>;
    total_spawned: number;
    total_lost: number;
}

export interface ConstructionMetrics {
    rate: Record<string, number>;
    total: number;
}

export interface EconomyMetrics {
    flow_rate: Record<string, number>;
    total_revenue: number;
    upkeep_breakdown: Record<string, number>;
}

export interface EconomicHealthData {
    net_profit: number;
    gross_income: number;
    total_upkeep: number;
    stockpile_velocity: number;
    revenue_breakdown: Record<string, number>;
}

export interface BattlePerformanceData {
    avg_cer: number;
    latest_composition: Record<string, number>;
    latest_attrition: number;
    recent_battle_count: number;
}

export interface ConstructionActivityData {
    building_types: Record<string, number>;
    avg_idle_slots: number;
    avg_queue_efficiency: number;
}

export interface ResearchImpactData {
    latest_tech: string;
    latest_deltas: Record<string, number>;
    recent_count: number;
}

export interface LiveMetricsResponse {
    battles?: BattleMetrics;
    units?: UnitsMetrics;
    construction?: ConstructionMetrics;
    economy?: EconomyMetrics;
    economic_health?: EconomicHealthData;
    battle_performance?: BattlePerformanceData;
    construction_activity?: ConstructionActivityData;
    research_impact?: ResearchImpactData;
    turn?: number;
    faction_status?: Record<string, any>;
    planet_status?: Record<string, any>;

    // Backwards Compatibility Fields
    battles_per_sec?: number;
    spawn_rates_per_sec?: Record<string, any>;
    loss_rates_per_sec?: Record<string, any>;
}

// --- WebSocket Message Models ---

export type WSMessageType =
    | 'status_update'
    | 'snapshot'
    | 'metrics_update'
    | 'event_stream'
    | 'battle_event'
    | 'resource_event'
    | 'tech_event'
    | 'construction_event'
    | 'system_event'
    | 'movement_event'
    | 'campaign_event'
    | 'strategy_event'
    | 'doctrine_event'
    | 'alert_triggered'
    | 'error_notification'
    | 'ping'
    | 'pong'
    | 'response';

export interface WSMessage<T = any> {
    type: WSMessageType;
    timestamp: number;
    data?: T;
}

export interface WSStatusUpdate extends WSMessage<StatusResponse> {
    type: 'status_update';
}

export interface WSMetricsUpdate extends WSMessage<LiveMetricsResponse> {
    type: 'metrics_update';
}

export interface WSEventStream extends WSMessage<TelemetryEvent> {
    type: 'event_stream' | 'battle_event' | 'resource_event' | 'tech_event' | 'construction_event' | 'system_event';
}

export interface WSAlertTriggered extends WSMessage<Alert> {
    type: 'alert_triggered';
}

export interface TelemetryEvent {
    timestamp: number;
    universe: string;
    category: string;
    event_type: string;
    turn: number | null;
    faction: string | null;
    data: Record<string, any>;
}

export type EventCategory =
    | 'combat'
    | 'economy'
    | 'technology'
    | 'construction'
    | 'system'
    | 'diplomacy'
    | 'movement'
    | 'campaign'
    | 'strategy'
    | 'doctrine';

export interface EventIcon {
    type: string;
    icon: string;
    color: string;
}

export interface EventFilterOptions {
    categories: EventCategory[];
    factions: string[];
    minTurn: number;
    maxTurn: number;
}

export interface TechUnlockEvent extends TelemetryEvent {
    tech_id: string;
    cost?: number;
    description?: string;
}

// --- Internal Hook/State Types ---

export type ConnectionStatus = 'connected' | 'disconnected' | 'reconnecting' | 'connecting' | 'error';

export interface ApiResponse<T> {
    data: T;
    status: number;
    statusText: string;
}

// --- Analytical Support Models ---

// Economic interfaces
export interface NetProfitData {
    gross_income: number[];
    upkeep: number[];
    net_profit: number[];
}

export interface NetProfitResponse {
    turns: number[];
    factions: Record<string, NetProfitData>;
}

export interface RevenueBreakdownResponse {
    turns: number[];
    income: Record<string, number[]>;
    expenses: Record<string, number[]>;
}

export interface StockpileVelocityData {
    stockpile: number[];
    velocity: number[];
}

export interface StockpileVelocityResponse {
    turns: number[];
    factions: Record<string, StockpileVelocityData>;
}

export interface ResourceROIResponse {
    roi_data: Array<Record<string, any>>;
}

// Military interfaces
export interface CombatEffectivenessResponse {
    factions: Record<string, { cer: number }>;
}

export interface CombatEffectivenessTimeSeriesResponse {
    turns: number[];
    values: number[];
}

export interface ForceCompositionResponse {
    composition: Record<string, number>;
}

export interface AttritionRateData {
    turns: number[];
    attrition: number[];
}

export interface AttritionRateResponse {
    factions: Record<string, AttritionRateData>;
}

export interface BattleHeatmapEntry {
    system: string;
    faction: string;
    cer: number;
    battle_count: number;
}

export interface BattleHeatmapResponse {
    heatmap: BattleHeatmapEntry[];
}

// Industrial interfaces
export interface IndustrialDensityData {
    building_counts: Record<string, number>;
}

export interface IndustrialDensityResponse {
    factions: Record<string, IndustrialDensityData>;
}

export interface QueueEfficiencyResponse {
    turns: number[];
    efficiency: number[];
    idle_slots: number[];
}

export interface ConstructionEvent {
    turn: number;
    faction: string;
    building: string;
    planet: string;
}

export interface ConstructionTimelineResponse {
    events: ConstructionEvent[];
}

export interface FleetPowerData {
    turns: number[];
    power: number[];
}

export interface FleetPowerResponse {
    factions: Record<string, FleetPowerData>;
}

export interface ResearchEvent {
    turn: number;
    faction: string;
    tech: string;
}

export interface ResearchTimelineResponse {
    events: ResearchEvent[];
}

export interface TechProgressResponse {
    factions: Record<string, Record<string, any>>;
}

// --- Alert Models ---

export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical';

export interface Alert {
    id: string;
    timestamp: string;
    severity: AlertSeverity;
    rule_name: string;
    message: string;
    context: Record<string, any>;
    acknowledged: boolean;
    resolved: boolean;
}

export interface AlertSummary {
    total: number;
    active: number;
    by_severity: Record<AlertSeverity, number>;
}

export interface AlertListResponse {
    total: number;
    page: number;
    page_size: number;
    items: Alert[];
}

// --- Export & Bookmark Models ---

export type ExportFormat = 'csv' | 'excel' | 'pdf';
export type ExportStatus = 'idle' | 'preparing' | 'generating' | 'downloading' | 'complete' | 'error';

export interface ExportRequest {
    universe: string;
    run_id: string;
    batch_id: string;
    factions: string[];
    turn_range: { min: number; max: number };
    metrics: string[];
    format: ExportFormat;
}

export interface ExportProgress {
    status: ExportStatus;
    progress: number;
    message: string;
}

export interface Bookmark {
    id: string;
    name: string;
    timestamp: string;
    filters: {
        selectedFactions: string[];
        turnRange: { min: number; max: number };
        visibleMetrics: Record<string, boolean>;
        comparisonMode: boolean;
        liveMode: boolean;
    };
}

export interface BookmarkExportData {
    version: string;
    exported_at: string;
    bookmarks: Bookmark[];
}
// --- Performance & Diagnostics Models ---

export interface MemoryStats {
    rss_mb: number;
    vms_mb: number;
    percent: number;
    available_mb: number;
}

export interface CacheStats {
    hit_rate: number;
    registered_caches: number;
    clear_count: number;
    warm_count: number;
    named_caches: string[];
}

export interface SlowQuery {
    metric: string;
    duration_ms: number;
    timestamp: string;
}

export interface ProfilingStats {
    enabled: boolean;
    slow_queries: number;
    slow_query_threshold_ms: number;
    recent_slow_queries: SlowQuery[];
}

export interface PerformanceStatsResponse {
    memory: MemoryStats;
    cache: CacheStats;
    profiling: ProfilingStats;
    profiling_enabled: boolean;
}

export interface FileDiagnostics {
    exists: boolean;
    size: number;
    readable: boolean;
}

export interface DiagnosticsResponse {
    static_folder: string;
    static_url_path: string;
    files: Record<string, FileDiagnostics>;
}

export interface ComponentHealthStatus {
    component: string;
    status: 'healthy' | 'degraded' | 'error';
    message: string;
    details: Record<string, any>;
}

export interface SystemHealthResponse {
    overall_status: 'healthy' | 'degraded' | 'error';
    components: ComponentHealthStatus[];
    timestamp: number;
}
