import React from 'react';
import { ChartContainer } from './ChartContainer';
import { RadarChart } from './RadarChart';
import { PieChart } from './PieChart';
import { useDashboardStore } from '../../stores/dashboardStore';
import { useFiltersStore } from '../../stores/filtersStore';

export const CombatEffectivenessChart: React.FC = () => {
    const metrics = useDashboardStore(state => state.liveMetrics);
    const { selectedFactions, comparisonMode } = useFiltersStore();

    const activeFactions = comparisonMode ? selectedFactions : selectedFactions.slice(0, 1);
    const battlePerformance = metrics?.battle_performance || {};

    // Transform live metrics for Radar
    // We normalize the values to a 0-100 scale
    const metrics_keys = ['Offense', 'Defense', 'Mobility', 'Logistics', 'Intelligence'];

    const data = metrics_keys.map(m => {
        const point: any = { metric: m };
        activeFactions.forEach(faction => {
            const factionPerf = battlePerformance[faction] || {};
            const baseValue = factionPerf.avg_cer || 0;

            // Artificial normalization/variation for visualization based on CER
            // In a real scenario, these would come from specific telemetry sub-metrics
            let val = 0;
            if (m === 'Offense') val = baseValue * 85;
            else if (m === 'Defense') val = baseValue * 70;
            else if (m === 'Mobility') val = baseValue * 60;
            else if (m === 'Logistics') val = baseValue * 75;
            else if (m === 'Intelligence') val = baseValue * 65;

            point[faction] = Math.min(100, Math.max(0, val));
        });
        return point;
    });

    const isEmpty = activeFactions.length === 0 || !activeFactions.some(f => battlePerformance[f]);

    return (
        <ChartContainer title="Tactical Combat Readiness" isEmpty={isEmpty}>
            <RadarChart data={data} dataKeys={activeFactions} angleKey="metric" />
        </ChartContainer>
    );
};

export const ForceCompositionChart: React.FC = () => {
    const metrics = useDashboardStore(state => state.liveMetrics);
    const { selectedFactions } = useFiltersStore();

    // Always use primary selection for Pie charts
    const primaryFaction = selectedFactions[0];
    const battlePerformance = metrics?.battle_performance || {};
    const composition = (primaryFaction ? battlePerformance[primaryFaction]?.latest_composition : {}) || {};

    const data = Object.entries(composition).map(([name, value]) => ({
        name,
        value: value as number
    }));

    return (
        <ChartContainer
            title={primaryFaction ? `Force Composition: ${primaryFaction}` : "Force Composition"}
            isEmpty={data.length === 0}
        >
            <PieChart data={data} />
        </ChartContainer>
    );
};
