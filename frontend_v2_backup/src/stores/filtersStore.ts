import { create } from 'zustand';

interface FiltersState {
    selectedFactions: string[];
    turnRange: { min: number; max: number };
    visibleMetrics: {
        battles: boolean;
        units: boolean;
        economy: boolean;
        construction: boolean;
        research: boolean;
    };
    comparisonMode: boolean;
    liveMode: boolean;

    // Actions
    toggleFaction: (faction: string) => void;
    setFactions: (factions: string[]) => void;
    setTurnRange: (min: number, max: number) => void;
    toggleMetricVisibility: (metric: keyof FiltersState['visibleMetrics']) => void;
    setComparisonMode: (enabled: boolean) => void;
    setLiveMode: (enabled: boolean) => void;
    reset: () => void;
}

const initialState = {
    selectedFactions: [],
    turnRange: { min: 0, max: 0 },
    visibleMetrics: {
        battles: true,
        units: true,
        economy: true,
        construction: true,
        research: true,
    },
    comparisonMode: false,
    liveMode: true,
};

export const useFiltersStore = create<FiltersState>((set) => ({
    ...initialState,

    toggleFaction: (faction) => set((state) => ({
        selectedFactions: state.selectedFactions.includes(faction)
            ? state.selectedFactions.filter((f) => f !== faction)
            : [...state.selectedFactions, faction],
    })),

    setFactions: (selectedFactions) => set({ selectedFactions }),

    setTurnRange: (min, max) => set({ turnRange: { min, max } }),

    toggleMetricVisibility: (metric) => set((state) => ({
        visibleMetrics: {
            ...state.visibleMetrics,
            [metric]: !state.visibleMetrics[metric],
        },
    })),

    setComparisonMode: (comparisonMode) => set({ comparisonMode }),

    setLiveMode: (liveMode) => set({ liveMode }),

    reset: () => set(initialState),
}));
