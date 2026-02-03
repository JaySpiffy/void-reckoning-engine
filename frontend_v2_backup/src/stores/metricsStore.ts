import { create } from 'zustand';
import {
    BattleMetrics,
    EconomicHealthData,
    UnitsMetrics,
    ConstructionMetrics
} from '../types';

interface MetricsHistoryEntry<T> {
    timestamp: number;
    data: T;
}

interface MetricsState {
    // History
    battleHistory: MetricsHistoryEntry<BattleMetrics>[];
    economicHistory: Record<string, MetricsHistoryEntry<EconomicHealthData>[]>;
    spawnHistory: Record<string, MetricsHistoryEntry<UnitsMetrics>[]>;
    constructionHistory: MetricsHistoryEntry<ConstructionMetrics>[];

    // Settings
    timeWindow: number; // in seconds

    // Actions
    addBattleMetric: (metric: BattleMetrics) => void;
    addEconomicSnapshot: (faction: string, data: EconomicHealthData) => void;
    addSpawnMetric: (metric: UnitsMetrics) => void;
    addConstructionMetric: (metric: ConstructionMetrics) => void;
    setTimeWindow: (seconds: number) => void;
    pruneHistory: () => void;
    clearHistory: () => void;
}

const MAX_HISTORY_POINTS = 100;

export const useMetricsStore = create<MetricsState>((set) => ({
    battleHistory: [],
    economicHistory: {},
    spawnHistory: {},
    constructionHistory: [],
    timeWindow: 60,

    addBattleMetric: (data) => set((state) => ({
        battleHistory: [...state.battleHistory, { timestamp: Date.now(), data }].slice(-MAX_HISTORY_POINTS)
    })),

    addEconomicSnapshot: (faction, data) => set((state) => {
        const history = state.economicHistory[faction] || [];
        return {
            economicHistory: {
                ...state.economicHistory,
                [faction]: [...history, { timestamp: Date.now(), data }].slice(-MAX_HISTORY_POINTS)
            }
        };
    }),

    addSpawnMetric: (data) => set((state) => ({
        spawnHistory: {
            ...state.spawnHistory,
            // Using a global entry for now as spawn_rate in UnitsMetrics is faction-keyed
            "global": [...(state.spawnHistory["global"] || []), { timestamp: Date.now(), data }].slice(-MAX_HISTORY_POINTS)
        }
    })),

    addConstructionMetric: (data) => set((state) => ({
        constructionHistory: [...state.constructionHistory, { timestamp: Date.now(), data }].slice(-MAX_HISTORY_POINTS)
    })),

    setTimeWindow: (timeWindow) => set({ timeWindow }),

    pruneHistory: () => set((state) => {
        const cutoff = Date.now() - (state.timeWindow * 1000);
        const prune = <T>(list: MetricsHistoryEntry<T>[]) => list.filter(e => e.timestamp > cutoff);

        const newEconomicHistory: Record<string, MetricsHistoryEntry<EconomicHealthData>[]> = {};
        Object.keys(state.economicHistory).forEach(f => {
            newEconomicHistory[f] = prune(state.economicHistory[f]);
        });

        const newSpawnHistory: Record<string, MetricsHistoryEntry<UnitsMetrics>[]> = {};
        Object.keys(state.spawnHistory).forEach(f => {
            newSpawnHistory[f] = prune(state.spawnHistory[f]);
        });

        return {
            battleHistory: prune(state.battleHistory),
            economicHistory: newEconomicHistory,
            spawnHistory: newSpawnHistory,
            constructionHistory: prune(state.constructionHistory)
        };
    }),

    clearHistory: () => set({
        battleHistory: [],
        economicHistory: {},
        spawnHistory: {},
        constructionHistory: []
    }),
}));
