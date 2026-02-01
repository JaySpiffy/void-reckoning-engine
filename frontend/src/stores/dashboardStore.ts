import { create } from 'zustand';
import {
    ConnectionStatus,
    StatusResponse,
    LiveMetricsResponse
} from '../types';

interface DashboardState {
    // Connection State
    connectionStatus: ConnectionStatus;
    wsConnected: boolean;
    lastPingTime: number | null;

    // Dashboard Status
    universe: string;
    runId: string;
    batchId: string;
    paused: boolean;
    telemetryConnected: boolean;
    indexerConnected: boolean;
    streaming: boolean;

    // Turn State
    currentTurn: number;
    maxTurn: number;

    // Live Metrics
    liveMetrics: LiveMetricsResponse | null;

    // Actions
    setConnectionStatus: (status: ConnectionStatus) => void;
    setWebSocketConnected: (connected: boolean) => void;
    setLastPingTime: (time: number) => void;
    setPaused: (paused: boolean) => void;
    updateStatus: (status: StatusResponse) => void;
    updateMetrics: (metrics: LiveMetricsResponse) => void;
    updateTurn: (turn: number) => void;
    setMaxTurn: (turn: number) => void;
    reset: () => void;
}

const initialState = {
    connectionStatus: 'disconnected' as ConnectionStatus,
    wsConnected: false,
    lastPingTime: null,
    universe: 'unknown',
    runId: 'unknown',
    batchId: 'unknown',
    paused: false,
    telemetryConnected: false,
    indexerConnected: false,
    streaming: false,
    currentTurn: 0,
    maxTurn: 0,
    liveMetrics: null,
};

export const useDashboardStore = create<DashboardState>((set) => ({
    ...initialState,

    setConnectionStatus: (connectionStatus) => set({ connectionStatus }),

    setWebSocketConnected: (wsConnected) => set({ wsConnected }),

    setLastPingTime: (lastPingTime) => set({ lastPingTime }),

    setPaused: (paused) => set({ paused }),

    updateStatus: (status) => set({
        universe: status.universe,
        runId: status.run_id,
        batchId: status.batch_id,
        paused: status.paused,
        telemetryConnected: status.telemetry_connected,
        indexerConnected: status.indexer_connected,
        streaming: status.streaming,
    }),

    updateMetrics: (liveMetrics) => set((state) => ({
        liveMetrics,
        currentTurn: liveMetrics.turn ?? state.currentTurn,
    })),

    updateTurn: (currentTurn) => set({ currentTurn }),

    setMaxTurn: (maxTurn) => set({ maxTurn }),

    reset: () => set(initialState),
}));
