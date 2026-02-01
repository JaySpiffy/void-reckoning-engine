import { useState, useEffect, useCallback } from 'react';
import { useFiltersStore } from '../stores/filtersStore';
import { militaryApi } from '../api/client';
import {
    CombatEffectivenessResponse,
    ForceCompositionResponse,
    AttritionRateResponse,
    BattleHeatmapResponse,
    CombatEffectivenessTimeSeriesResponse,
    FleetPowerResponse
} from '../types';

/**
 * Hook for fetching combat effectiveness (CER) data.
 */
export const useCombatEffectiveness = () => {
    const { selectedFactions, turnRange, comparisonMode } = useFiltersStore();
    const [data, setData] = useState<CombatEffectivenessResponse | CombatEffectivenessTimeSeriesResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            // If comparison mode is off and only one faction is selected, use time-series
            if (!comparisonMode && selectedFactions.length === 1) {
                const response = await militaryApi.getCombatEffectiveness({
                    faction: selectedFactions[0],
                    min_turn: turnRange.min,
                    max_turn: turnRange.max
                });
                setData(response.data);
            } else {
                // Multi-faction CER (snaphot/aggregate)
                const response = await militaryApi.getCombatEffectiveness({
                    factions: selectedFactions.join(','),
                    min_turn: turnRange.min,
                    max_turn: turnRange.max
                });
                setData(response.data);
            }
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch combat effectiveness');
        } finally {
            setLoading(false);
        }
    }, [selectedFactions, turnRange, comparisonMode]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
};

/**
 * Hook for fetching force composition data.
 */
export const useForceComposition = () => {
    const { selectedFactions } = useFiltersStore();
    const [data, setData] = useState<ForceCompositionResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const response = await militaryApi.getForceComposition({
                faction: selectedFactions[0] // Composition is usually single-faction
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch force composition');
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
 * Hook for fetching attrition rate data.
 */
export const useAttritionRate = () => {
    const { selectedFactions, turnRange } = useFiltersStore();
    const [data, setData] = useState<AttritionRateResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const response = await militaryApi.getAttritionRate({
                factions: selectedFactions.join(','),
                min_turn: turnRange.min,
                max_turn: turnRange.max
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch attrition rate');
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
 * Hook for fetching battle heatmap data.
 */
export const useBattleHeatmap = () => {
    const { turnRange } = useFiltersStore();
    const [data, setData] = useState<BattleHeatmapResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await militaryApi.getBattleHeatmap({
                min_turn: turnRange.min,
                max_turn: turnRange.max
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch battle heatmap');
        } finally {
            setLoading(false);
        }
    }, [turnRange]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
};

/**
 * Hook for fetching fleet power data.
 */
export const useFleetPower = () => {
    const { selectedFactions, turnRange } = useFiltersStore();
    const [data, setData] = useState<FleetPowerResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (selectedFactions.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const response = await militaryApi.getFleetPower({
                factions: selectedFactions.join(','),
                min_turn: turnRange.min,
                max_turn: turnRange.max
            });
            setData(response.data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to fetch fleet power');
        } finally {
            setLoading(false);
        }
    }, [selectedFactions, turnRange]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
};
