import React from 'react';
import {
    ResponsiveContainer,
    RadarChart as RechartsRadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    Legend,
    Tooltip
} from 'recharts';
import { CHART_COLORS, chartConfig, getFactionColor } from '../../styles/chartTheme';

interface RadarChartProps {
    data: any[];
    dataKeys: string[];
    angleKey?: string;
    height?: number | string;
    colors?: Record<string, string>;
}

export const RadarChart: React.FC<RadarChartProps> = ({
    data,
    dataKeys,
    angleKey = 'metric',
    height = 250,
    colors = {}
}) => {
    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer width="100%" height="100%">
                <RechartsRadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
                    <PolarGrid stroke={CHART_COLORS.grid} />
                    <PolarAngleAxis
                        dataKey={angleKey}
                        tick={{ fill: CHART_COLORS.text, fontSize: 10 }}
                    />
                    <PolarRadiusAxis
                        angle={30}
                        domain={[0, 100]}
                        tick={false}
                        axisLine={false}
                    />
                    <Tooltip
                        contentStyle={{
                            background: CHART_COLORS.tooltipBg,
                            border: `1px solid ${CHART_COLORS.tooltipBorder}`,
                            borderRadius: '8px',
                            fontSize: '12px'
                        }}
                    />
                    {dataKeys.map((key) => (
                        <Radar
                            key={key}
                            name={key}
                            dataKey={key}
                            stroke={colors[key] || getFactionColor(key)}
                            fill={colors[key] || getFactionColor(key)}
                            fillOpacity={0.3}
                            animationDuration={chartConfig.animationDuration}
                        />
                    ))}
                    <Legend
                        iconType="circle"
                        wrapperStyle={{
                            fontSize: '10px',
                            paddingTop: '10px'
                        }}
                    />
                </RechartsRadarChart>
            </ResponsiveContainer>
        </div>
    );
};
