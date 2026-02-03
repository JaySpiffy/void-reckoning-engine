import { describe, it, expect, beforeEach } from 'vitest';
import { useFiltersStore } from '../filtersStore';

describe('filtersStore', () => {
    beforeEach(() => {
        useFiltersStore.getState().resetFilters();
    });

    it('initializes with default values', () => {
        const state = useFiltersStore.getState();
        expect(state.filters.faction).toBe('all');
        expect(state.filters.minTurn).toBe(0);
    });

    it('updates faction filter', () => {
        useFiltersStore.getState().setFactionFilter('Imperium');
        expect(useFiltersStore.getState().filters.faction).toBe('Imperium');
    });

    it('updates turn range', () => {
        useFiltersStore.getState().setTurnRange(10, 50);
        expect(useFiltersStore.getState().filters.minTurn).toBe(10);
        expect(useFiltersStore.getState().filters.maxTurn).toBe(50);
    });

    it('resets filters', () => {
        useFiltersStore.getState().setFactionFilter('Chaos');
        useFiltersStore.getState().resetFilters();
        expect(useFiltersStore.getState().filters.faction).toBe('all');
    });
});
