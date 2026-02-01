import { describe, it, expect, beforeEach } from 'vitest';
import { useDashboardStore } from '../dashboardStore';

describe('dashboardStore', () => {
    beforeEach(() => {
        useDashboardStore.setState({
            status: {
                universe_name: '',
                run_id: '',
                turn: 0,
                max_turn: 0,
                factions: [],
                status: 'running'
            },
            isConnected: false
        });
    });

    it('updates status', () => {
        const mockStatus = {
            universe_name: 'test_uni',
            run_id: 'run_1',
            turn: 5,
            max_turn: 100,
            factions: ['F1'],
            status: 'paused'
        };

        useDashboardStore.getState().actions.setStatus(mockStatus);

        expect(useDashboardStore.getState().status).toEqual(mockStatus);
    });

    it('updates connection state', () => {
        useDashboardStore.getState().actions.setConnected(true);
        expect(useDashboardStore.getState().isConnected).toBe(true);
    });
});
