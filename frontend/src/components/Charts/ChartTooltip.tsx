import React from 'react';
import styles from './ChartContainer.module.css'; // Reusing some base styles or creating specific ones
import { CHART_COLORS } from '../../styles/chartTheme';

interface ChartTooltipProps {
    active?: boolean;
    payload?: any[];
    label?: string | number;
    valueFormatter?: (value: number) => string;
    labelFormatter?: (label: string | number) => React.ReactNode;
}

export const ChartTooltip: React.FC<ChartTooltipProps> = ({
    active,
    payload,
    label,
    valueFormatter = (v) => v.toLocaleString(),
    labelFormatter
}) => {
    if (!active || !payload || !payload.length) return null;

    const formattedLabel = labelFormatter ? labelFormatter(label!) : `Turn ${label}`;

    return (
        <div style={{
            background: CHART_COLORS.tooltipBg,
            border: `1px solid ${CHART_COLORS.tooltipBorder}`,
            padding: '0.75rem',
            borderRadius: '0.5rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
            backdropFilter: 'blur(4px)',
            fontSize: '0.75rem'
        }}>
            <div style={{ color: '#fff', fontWeight: 600, marginBottom: '0.5rem', borderBottom: `1px solid ${CHART_COLORS.grid}`, paddingBottom: '0.25rem' }}>
                {formattedLabel}
            </div>
            {payload.map((entry, index) => (
                <div key={index} style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', color: entry.color, padding: '2px 0' }}>
                    <span>{entry.name}:</span>
                    <span style={{ fontWeight: 700 }}>{valueFormatter(entry.value)}</span>
                </div>
            ))}
        </div>
    );
};
