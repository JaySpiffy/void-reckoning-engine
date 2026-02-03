import React from 'react';
import {
    ResponsiveContainer,
    PieChart as RechartsPieChart,
    Pie,
    Cell,
    Tooltip,
    Legend
} from 'recharts';
import { CHART_COLORS, chartConfig } from '../../styles/chartTheme';

interface PieChartProps {
    data: Array<{ name: string; value: number }>;
    height?: number | string;
    innerRadius?: number | string;
    colors?: string[];
    valueFormatter?: (value: number) => string;
}

const DEFAULT_COLORS = [
    CHART_COLORS.primary,
    CHART_COLORS.secondary,
    CHART_COLORS.success,
    CHART_COLORS.warning,
    CHART_COLORS.danger,
    CHART_COLORS.info
];

export const PieChart: React.FC<PieChartProps> = ({
    data,
    height = 250,
    innerRadius = '60%',
    colors = DEFAULT_COLORS,
    valueFormatter = (v) => v.toLocaleString()
}) => {
    // Check if data is empty or all values are zero
    const hasData = data && data.length > 0 && data.some(d => d.value > 0);

    if (!hasData) {
        return <EmptyState height={height} message="No Distribution Data" icon={<span>🥧</span>} />;
    }

    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer width="100%" height="100%">
                <RechartsPieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={innerRadius}
                        outerRadius="90%"
                        paddingAngle={5}
                        dataKey="value"
                        animationDuration={chartConfig.animationDuration}
                        stroke="none"
                    >
                        {data.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                        ))}
                    </Pie>
                    <Tooltip
                        contentStyle={{
                            background: CHART_COLORS.tooltipBg,
                            border: `1px solid ${CHART_COLORS.tooltipBorder}`,
                            borderRadius: '8px',
                            fontSize: '12px'
                        }}
                        itemStyle={{ color: '#fff' }}
                        formatter={valueFormatter}
                    />
                    <Legend
                        verticalAlign="bottom"
                        align="center"
                        iconType="circle"
                        wrapperStyle={{
                            fontSize: '10px',
                            paddingTop: '10px',
                            textTransform: 'uppercase'
                        }}
                    />
                </RechartsPieChart>
            </ResponsiveContainer>
        </div>
    );
};
