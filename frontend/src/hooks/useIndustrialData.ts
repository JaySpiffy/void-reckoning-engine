import { useState, useEffect, useCallback } from 'react';
import { useFiltersStore } from '../stores/filtersStore';
import { industrialApi } from '../api/client';
import {
    IndustrialDensityResponse,
    QueueEfficiencyResponse,
    ConstructionTimelineResponse,
    ResearchTimelineResponse,
    TechProgressResponse
} from '../types';

/**
 * Hook for fetching industrial density data.
 */
export const useIndustrialDensity = () => {
    const { selectedFactions } = useFiltersStore();
    const [data, setData] = useState<IndustrialDensityResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const response = await industrialApi.getIndustrialDensity({
                factions: selectedFactions.join(',')
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch industrial density');
        } finally {
            setLoading(false);
        }
    }, [selectedFactions]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
};

/**
 * Hook for fetching queue efficiency data.
 */
export const useQueueEfficiency = () => {
    const { selectedFactions, turnRange } = useFiltersStore();
    const [data, setData] = useState<QueueEfficiencyResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const response = await industrialApi.getQueueEfficiency({
                faction: selectedFactions[0],
                min_turn: turnRange.min,
                max_turn: turnRange.max
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch queue efficiency');
        } finally {
            setLoading(false);
        }
    }, [selectedFactions, turnRange]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
};

/**
 * Hook for fetching construction timeline events.
 */
export const useConstructionTimeline = (limit: number = 50) => {
    const { selectedFactions } = useFiltersStore();
    const [data, setData] = useState<ConstructionTimelineResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await industrialApi.getConstructionTimeline({
                limit,
                factions: selectedFactions.join(',')
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch construction timeline');
        } finally {
            setLoading(false);
        }
    }, [limit, selectedFactions]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
};

/**
 * Hook for fetching research timeline events.
 */
export const useResearchTimeline = (limit: number = 50) => {
    const { selectedFactions } = useFiltersStore();
    const [data, setData] = useState<ResearchTimelineResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await industrialApi.getResearchTimeline({
                limit,
                factions: selectedFactions.join(',')
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch research timeline');
        } finally {
            setLoading(false);
        }
    }, [limit, selectedFactions]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
};

/**
 * Hook for fetching tech progression data.
 */
export const useTechProgress = () => {
    const { selectedFactions, turnRange } = useFiltersStore();
    const [data, setData] = useState<TechProgressResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const response = await industrialApi.getTechProgress({
                factions: selectedFactions.join(','),
                min_turn: turnRange.min,
                max_turn: turnRange.max
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch tech progress');
        } finally {
            setLoading(false);
        }
    }, [selectedFactions, turnRange]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
};
