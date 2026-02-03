import React from 'react';
import {
    ScatterChart as RechartsScatterChart,
    Scatter,
    XAxis,
    YAxis,
    ZAxis,
    Tooltip,
    ResponsiveContainer,
    CartesianGrid,
    Cell
} from 'recharts';
import { CHART_COLORS } from '../../styles/chartTheme';
import { ChartTooltip } from './ChartTooltip';

interface ScatterChartProps {
    data: any[];
    xKey?: string;
    yKey?: string;
    zKey?: string; // For size
    nameKey?: string;
    colorKey?: string;
}

export const ScatterChart: React.FC<ScatterChartProps> = ({
    data,
    xKey = 'x',
    yKey = 'y',
    zKey = 'z',
    nameKey = 'name',
    colorKey = 'faction'
}) => {
    return (
        <ResponsiveContainer width="100%" height="100%">
            <RechartsScatterChart
                margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
            >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                    type="category"
                    dataKey={xKey}
                    name="System"
                    stroke="var(--text-muted)"
                    fontSize={10}
                    tick={{ fill: 'var(--text-secondary)' }}
                />
                <YAxis
                    type="number"
                    dataKey={yKey}
                    name="Performance/CER"
                    stroke="var(--text-muted)"
                    fontSize={10}
                    tick={{ fill: 'var(--text-secondary)' }}
                />
                <ZAxis type="number" dataKey={zKey} range={[50, 400]} name="Battles" />
                <Tooltip content={<ChartTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                <Scatter name="Combat Heatmap" data={data}>
                    {data.map((entry, index) => (
                        <Cell
                            key={`cell-${index}`}
                            fill={CHART_COLORS[entry[colorKey]] || 'var(--accent)'}
                        />
                    ))}
                </Scatter>
            </RechartsScatterChart>
        </ResponsiveContainer>
    );
};
