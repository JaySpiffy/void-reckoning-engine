import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
    StatusResponse,
    HealthResponse,
    MaxTurnResponse,
    WebSocketHealthResponse,
    LiveMetricsResponse,
    GalaxyTopologyResponse,
    Alert,
    AlertSummary,
    AlertListResponse,
    ExportRequest,
    PerformanceStatsResponse,
    SlowQuery,
    DiagnosticsResponse,
    SystemHealthResponse
} from '../types';

/**
 * API client for interacting with the FastAPI backend.
 */
const apiClient: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 20000,
});

// ... (lines 30-76)

switchRun: (runId: string) => apiClient.post<{ status: string; message: string }>('/control/switch', { run_id: runId }, { timeout: 60000 }),

    // Interceptor for responses to handle common error patterns
    apiClient.interceptors.response.use(
        (response) => response,
        (error) => {
            console.error('API Error:', error.response?.data || error.message);
            return Promise.reject(error);
        }
    );

// Status endpoints
export const getStatus = (): Promise<AxiosResponse<StatusResponse>> =>
    apiClient.get<StatusResponse>('/status');

export const getHealth = (detailed = false): Promise<AxiosResponse<HealthResponse>> =>
    apiClient.get<HealthResponse>(`/health${detailed ? '?detailed=true' : ''}`);

export const getMaxTurn = (universe?: string, runId?: string): Promise<AxiosResponse<MaxTurnResponse>> => {
    let url = '/run/max_turn';
    const params = new URLSearchParams();
    if (universe) params.append('universe', universe);
    if (runId) params.append('run_id', runId);
    if (params.toString()) url += `?${params.toString()}`;
    return apiClient.get<MaxTurnResponse>(url);
};

export const getWebSocketHealth = (): Promise<AxiosResponse<WebSocketHealthResponse>> =>
    apiClient.get<WebSocketHealthResponse>('/websocket/health');

// Metrics endpoints
export const getLiveMetrics = (): Promise<AxiosResponse<LiveMetricsResponse>> =>
    apiClient.get<LiveMetricsResponse>('/metrics/live');

// Galaxy endpoints (Planned)
export const getGalaxyTopology = (): Promise<AxiosResponse<GalaxyTopologyResponse>> =>
    apiClient.get<GalaxyTopologyResponse>('/galaxy/topology');

// Simulation Controls
export const controlApi = {
    getStatus: () => apiClient.get<{ paused: boolean; running: boolean }>('/control/status'),
    pause: () => apiClient.post<{ status: string; paused: boolean }>('/control/pause'),
    resume: () => apiClient.post<{ status: string; paused: boolean }>('/control/resume'),
    step: () => apiClient.post<{ status: string; action: string }>('/control/step'),
    // Launch Controls
    getConfigs: () => apiClient.get<{ configs: string[] }>('/control/configs'),
    getUniverses: () => apiClient.get<{ universes: string[] }>('/control/universes'),
    launch: (universe: string, configFile: string) => apiClient.post<{ status: string; pid: number }>('/control/launch', { universe, config_file: configFile }),
    // Run Switching
    getRuns: (universe?: string) => apiClient.get<any[]>('/runs', { params: { universe } }),
    switchRun: (runId: string) => apiClient.post<{ status: string; message: string }>('/control/switch', { run_id: runId }, { timeout: 60000 }),
};

// Economic endpoints
export const economicApi = {
    getNetProfit: (params: any) => apiClient.get('/economic/net_profit', { params }),
    getRevenueBreakdown: (params: any) => apiClient.get('/economic/revenue_breakdown', { params }),
    getStockpileVelocity: (params: any) => apiClient.get('/economic/stockpile_velocity', { params }),
    getResourceROI: (params: any) => apiClient.get('/economic/resource_roi', { params })
};

// Military endpoints
export const militaryApi = {
    getCombatEffectiveness: (params: any) => apiClient.get('/military/combat_effectiveness', { params }),
    getForceComposition: (params: any) => apiClient.get('/military/force_composition', { params }),
    getAttritionRate: (params: any) => apiClient.get('/military/attrition_rate', { params }),
    getBattleHeatmap: (params: any) => apiClient.get('/military/battle_heatmap', { params }),
    getFleetPower: (params: any) => apiClient.get('/military/fleet_power', { params })
};

// Industrial endpoints
export const industrialApi = {
    getIndustrialDensity: (params: any) => apiClient.get('/industrial/density', { params }),
    getQueueEfficiency: (params: any) => apiClient.get('/industrial/queue_efficiency', { params }),
    getConstructionTimeline: (params: any) => apiClient.get('/industrial/timeline', { params }),
    getResearchTimeline: (params: any) => apiClient.get('/industrial/research_timeline', { params }),
    getTechProgress: (params: any) => apiClient.get('/industrial/tech_progress', { params }),
};

// Alert endpoints
export const alertsApi = {
    getActive: () => apiClient.get<Alert[]>('/alerts/active'),
    getHistory: (params: { severity?: string[], alert_type?: string, page?: number, page_size?: number } | any) =>
        apiClient.get<AlertListResponse>('/alerts/history', {
            params,
            paramsSerializer: {
                indexes: null // Format array params as severity=info&severity=warning
            }
        }),
    getSummary: () => apiClient.get<AlertSummary>('/alerts/summary'),
    acknowledge: (id: string) => apiClient.post(`/alerts/${id}/acknowledge`),
    resolve: (id: string) => apiClient.post(`/alerts/${id}/resolve`)
};

// Export endpoints
export const exportApi = {
    exportMetrics: (payload: ExportRequest) => {
        const endpoint = payload.format === 'pdf'
            ? '/reports/export/metrics/pdf'
            : '/reports/export/metrics';

        return apiClient.post(endpoint, payload, {
            responseType: 'blob',
            timeout: 60000, // 60 seconds for large exports
        });
    }
};

// Performance endpoints
export const performanceApi = {
    getStats: () => apiClient.get<PerformanceStatsResponse>('/performance/stats'),
    enableProfiling: () => apiClient.post('/performance/profiling/enable'),
    disableProfiling: () => apiClient.post('/performance/profiling/disable'),
    getSlowQueries: (params?: any) => apiClient.get<SlowQuery[]>('/performance/slow_queries', { params })
};

// Diagnostics endpoints
export const diagnosticsApi = {
    getStatic: () => apiClient.get<DiagnosticsResponse>('/diagnostics/static'),
    getHealth: () => apiClient.get<SystemHealthResponse>('/diagnostics/health')
};

export default apiClient;
