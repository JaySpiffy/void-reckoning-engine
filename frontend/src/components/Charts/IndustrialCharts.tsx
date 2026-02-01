import React from 'react';
import { ChartContainer } from './ChartContainer';
import { BarChart } from './BarChart';
import { LineChart } from './LineChart';
import { useChartData } from '../../hooks/useChartData';
import { formatPercentage } from '../../utils/chartHelpers';

export const ProductionChart: React.FC = () => {
    const { data, factions, isEmpty } = useChartData(
        (state) => state.spawnHistory,
        (data) => {
            // Summing all spawn rates in the entry
            if (!data.spawn_rate) return 0;
            return Object.values(data.spawn_rate as Record<string, any>).reduce(
                (acc, val) => acc + (val.navy || 0) + (val.army || 0), 0
            );
        }
    );

    return (
        <ChartContainer title="Unit Production Throughput" isEmpty={isEmpty}>
            <BarChart
                data={data}
                dataKeys={factions}
                xAxisKey="x"
            />
        </ChartContainer>
    );
};

export const QueueEfficiencyChart: React.FC = () => {
    const { data, isEmpty } = useChartData(
        (state) => ({ global: state.constructionHistory }),
        (data) => data.avg_queue_efficiency || 0,
        { factions: ['global'] }
    );

    return (
        <ChartContainer title="Construction Queue Efficiency" isEmpty={isEmpty}>
            <LineChart
                data={data}
                dataKeys={['global']}
                valueFormatter={formatPercentage}
                colors={{ 'global': '#22c55e' }}
            />
        </ChartContainer>
    );
};
