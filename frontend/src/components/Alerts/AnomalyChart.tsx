import React from 'react';
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    Tooltip
} from 'recharts';
import { AlertSummary } from '../../types';

interface AnomalyChartProps {
    summary: AlertSummary | null;
}

const SEVERITY_COLORS = {
    critical: '#ff4444',
    error: '#ff8800',
    warning: '#ffbb33',
    info: '#33b5e5'
};

const AnomalyChart: React.FC<AnomalyChartProps> = ({ summary }) => {
    if (!summary || summary.total === 0) {
        return (
            <div style={{ color: '#647181', fontSize: '0.8rem', textAlign: 'center', padding: '1rem' }}>
                No active data
            </div>
        );
    }

    const data = Object.entries(summary.by_severity)
        .filter(([_, value]) => value > 0)
        .map(([name, value]) => ({
            name: name.toUpperCase(),
            value,
            color: SEVERITY_COLORS[name as keyof typeof SEVERITY_COLORS] || '#647181'
        }));

    return (
        <div style={{ width: '100%', height: 140 }}>
            <ResponsiveContainer>
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={30}
                        outerRadius={45}
                        paddingAngle={5}
                        dataKey="value"
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#1a1d26',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '4px',
                            fontSize: '0.75rem'
                        }}
                        itemStyle={{ color: '#e0e6ed' }}
                    />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
};

export default AnomalyChart;
