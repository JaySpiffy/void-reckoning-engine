import React from 'react';
import { ChartContainer } from './ChartContainer';
import { LineChart } from './LineChart';
import { useChartData } from '../../hooks/useChartData';
import { formatNumericValue } from '../../utils/chartHelpers';

export const NetProfitChart: React.FC = () => {
    const { data, factions, isEmpty } = useChartData(
        (state) => state.economicHistory,
        (data) => data.net_profit
    );

    return (
        <ChartContainer title="Economic Trajectory (Net Profit)" isEmpty={isEmpty}>
            <LineChart
                data={data}
                dataKeys={factions}
                valueFormatter={formatNumericValue}
                yAxisLabel="Credits"
            />
        </ChartContainer>
    );
};

export const ResourceTrendsChart: React.FC = () => {
    const { data, factions, isEmpty } = useChartData(
        (state) => state.economicHistory,
        (data) => data.gross_income
    );

    return (
        <ChartContainer title="Resource Production Trends" isEmpty={isEmpty}>
            <LineChart
                data={data}
                dataKeys={factions}
                valueFormatter={formatNumericValue}
                yAxisLabel="Income"
            />
        </ChartContainer>
    );
};
