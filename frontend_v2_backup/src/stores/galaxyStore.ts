import { create } from 'zustand';
import { GalaxySystem, GalaxyLane, GalaxyBounds } from '../types';

interface GalaxyTransform {
    scale: number;
    x: number;
    y: number;
}

interface BattleAnimation {
    id: string;
    x: number;
    y: number;
    startTime: number;
    color: string;
    type: 'battle' | 'capture';
}

interface GalaxyState {
    systems: GalaxySystem[];
    lanes: GalaxyLane[];
    bounds: GalaxyBounds | null;
    transform: GalaxyTransform;
    selectedSystem: string | null;
    hoveredSystem: string | null;
    animations: BattleAnimation[];
    loading: boolean;
    error: string | null;

    // Actions
    setGalaxyData: (data: { systems: GalaxySystem[]; lanes: GalaxyLane[]; bounds: GalaxyBounds }) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    updateTransform: (transform: Partial<GalaxyTransform>) => void;
    selectSystem: (name: string | null) => void;
    setHoveredSystem: (name: string | null) => void;
    addAnimation: (animation: Omit<BattleAnimation, 'id' | 'startTime'>) => void;
    clearExpiredAnimations: () => void;
    updateSystemControl: (systemName: string, control: Record<string, number>, owner: string) => void;
    reset: () => void;
}

export const useGalaxyStore = create<GalaxyState>((set) => ({
    systems: [],
    lanes: [],
    bounds: null,
    transform: { scale: 1, x: 0, y: 0 },
    selectedSystem: null,
    hoveredSystem: null,
    animations: [],
    loading: false,
    error: null,

    setGalaxyData: (data) => set({
        systems: data.systems,
        lanes: data.lanes,
        bounds: data.bounds,
        loading: false
    }),

    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error, loading: false }),

    updateTransform: (transform) => set((state) => ({
        transform: { ...state.transform, ...transform }
    })),

    selectSystem: (name) => set({ selectedSystem: name }),
    setHoveredSystem: (name) => set({ hoveredSystem: name }),

    addAnimation: (anim) => set((state) => ({
        animations: [
            ...state.animations,
            {
                ...anim,
                id: Math.random().toString(36).substr(2, 9),
                startTime: Date.now()
            }
        ]
    })),

    clearExpiredAnimations: () => set((state) => ({
        animations: state.animations.filter(a => Date.now() - a.startTime < 2000)
    })),

    updateSystemControl: (systemName, control, owner) => set((state) => ({
        systems: state.systems.map(s =>
            s.name === systemName ? { ...s, control, owner } : s
        )
    })),

    reset: () => set({
        systems: [],
        lanes: [],
        bounds: null,
        transform: { scale: 1, x: 0, y: 0 },
        selectedSystem: null,
        hoveredSystem: null,
        animations: [],
        loading: false,
        error: null
    })
}));
