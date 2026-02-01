/**
 * Utility functions for transforming raw metrics history into Recharts-friendly formats.
 */

export const formatTimeSeriesData = (
    historyMap: Record<string, any[]>,
    selectedFactions: string[],
    dataExtractor: (entry: any) => number,
    timeKey: string = 'timestamp'
) => {
    // 1. Identify all unique time points (or turns)
    const timePoints = new Set<number>();
    selectedFactions.forEach(faction => {
        const history = historyMap[faction] || [];
        history.forEach(entry => timePoints.add(entry[timeKey]));
    });

    // 2. Sort time points
    const sortedTime = Array.from(timePoints).sort((a, b) => a - b);

    // 3. Build the data array
    return sortedTime.map(time => {
        const point: any = { x: time };
        selectedFactions.forEach(faction => {
            const history = historyMap[faction] || [];
            const entry = history.find(e => e[timeKey] === time);
            if (entry) {
                point[faction] = dataExtractor(entry.data);
            }
        });
        return point;
    });
};

export const downsampleData = (data: any[], maxPoints: number) => {
    if (data.length <= maxPoints) return data;
    const factor = Math.ceil(data.length / maxPoints);
    return data.filter((_, i) => i % factor === 0);
};

export const formatNumericValue = (val: number): string => {
    if (val >= 1000000) return (val / 1000000).toFixed(1) + 'M';
    if (val >= 1000) return (val / 1000).toFixed(1) + 'K';
    return val.toFixed(0);
};

export const formatPercentage = (val: number): string => `${val.toFixed(1)}%`;
