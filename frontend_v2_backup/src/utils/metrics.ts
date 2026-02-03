import { UnitsMetrics } from '../types';

/**
 * Calculates the total units per second by summing spawn rates across all factions.
 */
export const calculateTotalUnitsPerSec = (unitsMetrics: UnitsMetrics | undefined): number => {
    if (!unitsMetrics || !unitsMetrics.spawn_rate) return 0;

    let total = 0;
    const rates = unitsMetrics.spawn_rate;

    for (const faction in rates) {
        if (Object.prototype.hasOwnProperty.call(rates, faction)) {
            const factionRates = rates[faction];
            total += (factionRates.navy || 0) + (factionRates.army || 0);
        }
    }

    return total;
};

/**
 * Formats a metric value with appropriate decimal places.
 */
export const formatMetricValue = (value: number, decimals: number = 2): string => {
    return value.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
};

/**
 * Determines the status of a metric based on thresholds.
 */
export const getMetricStatus = (value: number, threshold: number): 'normal' | 'warning' | 'critical' => {
    if (value >= threshold * 1.5) return 'critical';
    if (value >= threshold) return 'warning';
    return 'normal';
};
