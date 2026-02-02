import React from 'react';
import styles from './PerformancePanel.module.css';

interface MetricCardProps {
    label: string;
    value: string | number;
    unit?: string;
    onClick?: () => void;
    loading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({
    label,
    value,
    unit,
    onClick,
    loading = false
}) => {
    return (
        <div
            className={`${styles.metricCard} ${onClick ? styles.clickable : ''}`}
            onClick={onClick}
        >
            <div className={styles.label}>{label}</div>
            {loading ? (
                <div className={styles.skeleton}></div>
            ) : (
                <div className={styles.value}>
                    {value}
                    {unit && <span className={styles.unit}>{unit}</span>}
                </div>
            )}
        </div>
    );
};

export default MetricCard;
