import { useState, useEffect, useCallback } from 'react';
import { useFiltersStore } from '../stores/filtersStore';
import { economicApi } from '../api/client';
import {
    NetProfitResponse,
    RevenueBreakdownResponse,
    StockpileVelocityResponse,
    ResourceROIResponse
} from '../types';

/**
 * Hook for fetching net profit time-series data.
 */
export const useNetProfit = () => {
    const { selectedFactions, turnRange } = useFiltersStore();
    const [data, setData] = useState<NetProfitResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const response = await economicApi.getNetProfit({
                factions: selectedFactions.join(','),
                min_turn: turnRange.min,
                max_turn: turnRange.max
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch net profit data');
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
 * Hook for fetching revenue breakdown data.
 */
export const useRevenueBreakdown = () => {
    const { selectedFactions, turnRange } = useFiltersStore();
    const [data, setData] = useState<RevenueBreakdownResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            // Breakdown supports multi-faction (Global View)
            const response = await economicApi.getRevenueBreakdown({
                faction: selectedFactions.join(','),
                min_turn: turnRange.min,
                max_turn: turnRange.max
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch revenue breakdown');
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
 * Hook for fetching stockpile velocity data.
 */
export const useStockpileVelocity = () => {
    const { selectedFactions, turnRange } = useFiltersStore();
    const [data, setData] = useState<StockpileVelocityResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const response = await economicApi.getStockpileVelocity({
                factions: selectedFactions.join(','),
                min_turn: turnRange.min,
                max_turn: turnRange.max
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch stockpile velocity');
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
 * Hook for fetching resource ROI data.
 */
export const useResourceROI = () => {
    const { selectedFactions } = useFiltersStore();
    const [data, setData] = useState<ResourceROIResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const response = await economicApi.getResourceROI({
                factions: selectedFactions.join(',')
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch resource ROI');
        } finally {
            setLoading(false);
        }
    }, [selectedFactions]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
};
