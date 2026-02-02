import { useMemo } from 'react';
import { useMetricsStore } from '../stores/metricsStore';
import { useFiltersStore } from '../stores/filtersStore';
import { formatTimeSeriesData, downsampleData } from '../utils/chartHelpers';

interface UseChartDataOptions {
    maxPoints?: number;
    factions?: string[];
}

/**
 * Hook to consume metrics history and provide filtered, formatted data for Recharts.
 */
export const useChartData = (
    historySelector: (state: any) => Record<string, any[]>,
    dataExtractor: (data: any) => number,
    options: UseChartDataOptions = {}
) => {
    const historyMap = useMetricsStore(historySelector);
    const selectedFactions = useFiltersStore(state => state.selectedFactions);
    const comparisonMode = useFiltersStore(state => state.comparisonMode);

    // Determine which factions to show
    const activeFactions = useMemo(() => {
        if (options.factions) return options.factions;
        if (comparisonMode) return selectedFactions;
        return selectedFactions.slice(0, 1); // Show primary only if not in comparison mode
    }, [comparisonMode, selectedFactions, options.factions]);

    // Transform and filter
    const chartData = useMemo(() => {
        if (!activeFactions.length) return [];

        let data = formatTimeSeriesData(
            historyMap,
            activeFactions,
            dataExtractor,
            'timestamp' // Stores currently use timestamp for history keys
        );

        if (options.maxPoints) {
            data = downsampleData(data, options.maxPoints);
        }

        return data;
    }, [historyMap, activeFactions, dataExtractor, options.maxPoints]);

    return {
        data: chartData,
        factions: activeFactions,
        isEmpty: chartData.length === 0
    };
};
