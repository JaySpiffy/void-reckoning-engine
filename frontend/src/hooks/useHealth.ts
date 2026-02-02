import { useState, useEffect, useCallback, useRef } from 'react';
import { getHealth } from '../api/client';
import { HealthResponse } from '../types';

interface UseHealthOptions {
    detailed?: boolean;
    polling?: boolean;
    interval?: number;
}

/**
 * Hook for monitoring backend system health.
 */
export const useHealth = (options: UseHealthOptions = {}) => {
    const { detailed = false, polling = false, interval = 30000 } = options;
    const [health, setHealth] = useState<HealthResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const fetchHealth = useCallback(async () => {
        try {
            const response = await getHealth(detailed);
            setHealth(response.data);
            setError(null);
        } catch (err: any) {
            // 503 is a valid health response for degraded status
            if (err.response?.status === 503 && err.response?.data) {
                setHealth(err.response.data);
                setError(null);
            } else {
                setError(err instanceof Error ? err : new Error('Health check failed'));
            }
        } finally {
            setLoading(false);
        }
    }, [detailed]);

    useEffect(() => {
        fetchHealth();

        if (polling) {
            timerRef.current = setInterval(fetchHealth, interval);
        }

        return () => {
            if (timerRef.current) clearInterval(timerRef.current as any);
        };
    }, [fetchHealth, polling, interval]);

    return { health, loading, error, refetch: fetchHealth };
};
