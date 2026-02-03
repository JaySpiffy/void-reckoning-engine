import { useState, useEffect, useCallback, useRef } from 'react';
import { getLiveMetrics } from '../api/client';
import { useDashboardStore } from '../stores/dashboardStore';
import { useMetricsStore } from '../stores/metricsStore';

interface UseMetricsOptions {
    polling?: boolean;
    interval?: number;
}

/**
 * Hook for fetching live metrics with optional polling.
 */
export const useMetrics = (options: UseMetricsOptions = {}) => {
    const { polling = false, interval = 5000 } = options;
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const updateMetrics = useDashboardStore((s) => s.updateMetrics);
    const addBattleMetric = useMetricsStore((s) => s.addBattleMetric);
    const pruneHistory = useMetricsStore((s) => s.pruneHistory);

    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const fetchMetrics = useCallback(async () => {
        try {
            const response = await getLiveMetrics();
            updateMetrics(response.data);

            // Accumulate in history store
            if (response.data.battles) {
                addBattleMetric(response.data.battles);
            }

            pruneHistory();
            setError(null);
        } catch (err: any) {
            setError(err instanceof Error ? err : new Error('Failed to fetch metrics'));
        } finally {
            setLoading(false);
        }
    }, [updateMetrics, addBattleMetric, pruneHistory]);

    useEffect(() => {
        fetchMetrics();

        if (polling) {
            timerRef.current = setInterval(fetchMetrics, interval);
        }

        return () => {
            if (timerRef.current) clearInterval(timerRef.current as any);
        };
    }, [fetchMetrics, polling, interval]);

    return { loading, error, refetch: fetchMetrics };
};
