import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { FilterPanel } from '../FilterPanel';
import * as filtersStoreModule from '../../../stores/filtersStore';

// Mock store
vi.mock('../../../stores/filtersStore', () => ({
    useFiltersStore: vi.fn()
}));

describe('FilterPanel', () => {
    const setFactionFilter = vi.fn();
    const setTurnRange = vi.fn();

    beforeEach(() => {
        vi.spyOn(filtersStoreModule, 'useFiltersStore').mockReturnValue({
            filters: {
                faction: 'all',
                minTurn: 0,
                maxTurn: 100
            },
            setFactionFilter,
            setTurnRange,
            resetFilters: vi.fn(),
            availableFactions: ['Imperium', 'Orks']
        });
    });

    it('renders faction selector', () => {
        render(<FilterPanel />);
        expect(screen.getByText(/Filter by Faction/i)).toBeInTheDocument();
        expect(screen.getByRole('combobox')).toBeInTheDocument(); // Select element
    });

    // Note: Testing interaction with custom selects or complex inputs might require userEvent
    // Simplified trigger test
    it('calls setFactionFilter on change', () => {
        render(<FilterPanel />);
        const select = screen.getByRole('combobox');
        fireEvent.change(select, { target: { value: 'Imperium' } });
        expect(setFactionFilter).toHaveBeenCalledWith('Imperium');
    });
});
