import { create } from 'zustand';

import { PerformanceStatsResponse, ProfilingStats } from '../types';
import { performanceApi } from '../api/client';

interface PerformanceState {
    stats: PerformanceStatsResponse | null;
    isLoading: boolean;
    error: string | null;
    isExpanded: boolean;
    pollingInterval: number | null;

    // Actions
    fetchStats: () => Promise<void>;
    enableProfiling: () => Promise<void>;
    disableProfiling: () => Promise<void>;
    toggleProfiling: () => Promise<void>;
    startPolling: (intervalMs?: number) => void;
    stopPolling: () => void;
    toggleExpanded: () => void;
    reset: () => void;
}

export const usePerformanceStore = create<PerformanceState>((set, get) => ({

    stats: null,
    isLoading: false,
    error: null,
    isExpanded: false,
    pollingInterval: null,

    fetchStats: async () => {
        set({ isLoading: true });
        try {
            const response = await performanceApi.getStats();
            set({ stats: response.data, isLoading: false, error: null });
        } catch (err) {
            set({
                isLoading: false,
                error: err instanceof Error ? err.message : 'Failed to fetch performance stats'
            });
        }
    },

    enableProfiling: async () => {
        try {
            await performanceApi.enableProfiling();
            // Refetch stats to update UI
            await get().fetchStats();
        } catch (err) {
            set({ error: err instanceof Error ? err.message : 'Failed to enable profiling' });
        }
    },

    disableProfiling: async () => {
        try {
            await performanceApi.disableProfiling();
            // Refetch stats to update UI
            await get().fetchStats();
        } catch (err) {
            set({ error: err instanceof Error ? err.message : 'Failed to disable profiling' });
        }
    },

    toggleProfiling: async () => {
        const { stats } = get();
        if (!stats) return;

        if (stats.profiling_enabled) {
            await get().disableProfiling();
        } else {
            await get().enableProfiling();
        }
    },

    startPolling: (intervalMs = 5000) => {
        const existingInterval = get().pollingInterval;
        if (existingInterval) return;

        // Initial fetch
        get().fetchStats();

        const interval = window.setInterval(() => {
            get().fetchStats();
        }, intervalMs);

        set({ pollingInterval: interval });
    },

    stopPolling: () => {
        const interval = get().pollingInterval;
        if (interval) {
            window.clearInterval(interval);
            set({ pollingInterval: null });
        }
    },

    toggleExpanded: () => {
        const { isExpanded, startPolling, stopPolling } = get();
        const newExpanded = !isExpanded;
        set({ isExpanded: newExpanded });

        if (newExpanded) {
            startPolling();
        } else {
            stopPolling();
        }
    },

    reset: () => {
        get().stopPolling();
        set({
            stats: null,
            isLoading: false,
            error: null,
            isExpanded: false,
            pollingInterval: null
        });
    }
}));
