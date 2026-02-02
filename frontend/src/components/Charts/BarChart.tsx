import React from 'react';
import {
    ResponsiveContainer,
    BarChart as RechartsBarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    Cell
} from 'recharts';
import { CHART_COLORS, chartConfig, getFactionColor } from '../../styles/chartTheme';
import { ChartTooltip } from './ChartTooltip';

interface BarChartProps {
    data: any[];
    dataKeys: string[];
    xAxisKey?: string;
    stacked?: boolean;
    height?: number | string;
    colors?: Record<string, string>;
    valueFormatter?: (value: number) => string;
}

export const BarChart: React.FC<BarChartProps> = ({
    data,
    dataKeys,
    xAxisKey = 'label',
    stacked = false,
    height = 250,
    colors = {},
    valueFormatter
}) => {
    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer width="100%" height="100%">
                <RechartsBarChart data={data} margin={chartConfig.margin}>
                    <CartesianGrid
                        vertical={false}
                        stroke={CHART_COLORS.grid}
                        strokeDasharray={chartConfig.gridDashArray}
                    />
                    <XAxis
                        dataKey={xAxisKey}
                        stroke={CHART_COLORS.text}
                        fontSize={10}
                        axisLine={false}
                        tickLine={false}
                    />
                    <YAxis
                        stroke={CHART_COLORS.text}
                        fontSize={10}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={valueFormatter}
                    />
                    <Tooltip content={<ChartTooltip valueFormatter={valueFormatter} labelFormatter={(label) => label} />} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
                    <Legend
                        verticalAlign="top"
                        align="right"
                        iconType="rect"
                        wrapperStyle={{
                            fontSize: '10px',
                            paddingBottom: '10px',
                            textTransform: 'uppercase'
                        }}
                    />
                    {dataKeys.map((key) => (
                        <Bar
                            key={key}
                            dataKey={key}
                            name={key}
                            fill={colors[key] || getFactionColor(key)}
                            stackId={stacked ? "a" : undefined}
                            radius={[2, 2, 0, 0]}
                            animationDuration={chartConfig.animationDuration}
                        />
                    ))}
                </RechartsBarChart>
            </ResponsiveContainer>
        </div>
    );
};
