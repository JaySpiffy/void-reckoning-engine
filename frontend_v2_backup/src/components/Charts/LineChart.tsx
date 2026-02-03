import React from 'react';
import {
    ResponsiveContainer,
    LineChart as RechartsLineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend
} from 'recharts';
import { CHART_COLORS, chartConfig, getFactionColor } from '../../styles/chartTheme';
import { ChartTooltip } from './ChartTooltip';

interface LineChartProps {
    data: any[];
    dataKeys: string[];
    xAxisKey?: string;
    yAxisLabel?: string;
    height?: number | string;
    colors?: Record<string, string>;
    syncId?: string;
    valueFormatter?: (value: number) => string;
    smooth?: boolean;
}

export const LineChart: React.FC<LineChartProps> = ({
    data,
    dataKeys,
    xAxisKey = 'x',
    yAxisLabel,
    height = 250,
    colors = {},
    syncId,
    valueFormatter,
    smooth = true
}) => {
    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer width="100%" height="100%">
                <RechartsLineChart data={data} margin={chartConfig.margin} syncId={syncId}>
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
                        tick={{ fill: CHART_COLORS.text }}
                    />
                    <YAxis
                        stroke={CHART_COLORS.text}
                        fontSize={10}
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: CHART_COLORS.text }}
                        tickFormatter={valueFormatter}
                    />
                    <Tooltip content={<ChartTooltip valueFormatter={valueFormatter} />} />
                    <Legend
                        verticalAlign="top"
                        align="right"
                        iconType="circle"
                        wrapperStyle={{
                            fontSize: '10px',
                            paddingBottom: '10px',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em'
                        }}
                    />
                    {dataKeys.map((key) => (
                        <Line
                            key={key}
                            type={smooth ? "monotone" : "linear"}
                            dataKey={key}
                            name={key}
                            stroke={colors[key] || getFactionColor(key)}
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 4, strokeWidth: 0 }}
                            animationDuration={chartConfig.animationDuration}
                        />
                    ))}
                </RechartsLineChart>
            </ResponsiveContainer>
        </div>
    );
};
