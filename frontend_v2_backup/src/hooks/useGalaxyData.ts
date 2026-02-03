import { useEffect, useCallback } from 'react';
import { useGalaxyStore } from '../stores/galaxyStore';
import { useDashboardStore } from '../stores/dashboardStore';
import { getGalaxyTopology } from '../api/client';

/**
 * Custom hook for fetching and managing galaxy topology data.
 */
export const useGalaxyData = () => {
    const {
        setGalaxyData,
        setLoading,
        setError,
        loading,
        error
    } = useGalaxyStore();

    const { universe, runId } = useDashboardStore();

    const fetchGalaxy = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await getGalaxyTopology();
            setGalaxyData(response.data);
        } catch (err: any) {
            console.error('Failed to fetch galaxy topology:', err);
            setError(err.response?.data?.error || 'Failed to load galaxy map');
        } finally {
            setLoading(false);
        }
    }, [setGalaxyData, setLoading, setError]);

    // Fetch on mount or when universe/run changes
    useEffect(() => {
        fetchGalaxy();
    }, [fetchGalaxy, universe, runId]);

    return {
        loading,
        error,
        refetch: fetchGalaxy
    };
};
