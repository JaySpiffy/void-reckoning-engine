import { create } from 'zustand';

import { DiagnosticsResponse, SystemHealthResponse } from '../types';
import { diagnosticsApi } from '../api/client';

interface DiagnosticsState {
    staticDiagnostics: DiagnosticsResponse | null;
    healthStatus: SystemHealthResponse | null;
    isLoading: boolean;
    error: string | null;

    // Actions
    fetchStaticDiagnostics: () => Promise<void>;
    fetchHealthStatus: () => Promise<void>;
    refreshAll: () => Promise<void>;
}

export const useDiagnosticsStore = create<DiagnosticsState>((set, get) => ({

    staticDiagnostics: null,
    healthStatus: null,
    isLoading: false,
    error: null,

    fetchStaticDiagnostics: async () => {
        set({ isLoading: true });
        try {
            const response = await diagnosticsApi.getStatic();
            set({ staticDiagnostics: response.data, isLoading: false, error: null });
        } catch (err) {
            set({
                isLoading: false,
                error: err instanceof Error ? err.message : 'Failed to fetch static diagnostics'
            });
        }
    },

    fetchHealthStatus: async () => {
        set({ isLoading: true });
        try {
            const response = await diagnosticsApi.getHealth();
            set({ healthStatus: response.data, isLoading: false, error: null });
        } catch (err) {
            set({
                isLoading: false,
                error: err instanceof Error ? err.message : 'Failed to fetch health status'
            });
        }
    },

    refreshAll: async () => {
        // Determine checking flow or parallelize
        set({ isLoading: true });
        try {
            const [staticRes, healthRes] = await Promise.all([
                diagnosticsApi.getStatic(),
                diagnosticsApi.getHealth()
            ]);
            set({
                staticDiagnostics: staticRes.data,
                healthStatus: healthRes.data,
                isLoading: false,
                error: null
            });
        } catch (err) {
            set({
                isLoading: false,
                error: err instanceof Error ? err.message : 'Failed to refresh diagnostics'
            });
        }
    },
}));
