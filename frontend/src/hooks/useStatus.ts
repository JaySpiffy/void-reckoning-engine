import { useState, useEffect, useCallback } from 'react';
import { getStatus } from '../api/client';
import { useDashboardStore } from '../stores/dashboardStore';
import { StatusResponse } from '../types';

/**
 * Hook for fetching and managing dashboard status state.
 */
export const useStatus = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);
    const updateStatus = useDashboardStore((s) => s.updateStatus);

    const fetchStatus = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await getStatus();
            updateStatus(response.data);
            setLoading(false);
        } catch (err: any) {
            setError(err instanceof Error ? err : new Error('Failed to fetch status'));
            setLoading(false);
        }
    }, [updateStatus]);

    useEffect(() => {
        fetchStatus();
    }, [fetchStatus]);

    return { loading, error, refetch: fetchStatus };
};
