import React from 'react';
import styles from './MetricCard.module.css';
import { MetricCardProps } from '../../types/components';
import { formatMetricValue } from '../../utils/metrics';

export const MetricCard: React.FC<MetricCardProps> = ({
    label,
    value,
    unit,
    loading = false,
    error,
    accentColor = true
}) => {
    // Priority 1: Error State
    if (error) {
        return (
            <div className={`${styles.card} ${styles.errorCard}`}>
                <span className={styles.label}>{label}</span>
                <div className={styles.error}>
                    <span className={styles.errorIcon}>⚠️</span>
                    <span className={styles.errorText}>CONNECTIVITY FAILURE</span>
                </div>
            </div>
        );
    }

    // Priority 2: Loading State
    if (loading) {
        return (
            <div className={styles.card}>
                <div className={`${styles.skeletonLabel} skeleton`} />
                <div className={`${styles.skeletonValue} skeleton`} />
            </div>
        );
    }

    return (
        <div className={styles.card}>
            <span className={styles.label}>{label}</span>
            <div className={styles.valueContainer}>
                <span className={`${styles.value} ${accentColor ? styles.accent : ''}`}>
                    {formatMetricValue(value)}
                </span>
                <span className={styles.unit}>{unit}</span>
            </div>
        </div>
    );
};
