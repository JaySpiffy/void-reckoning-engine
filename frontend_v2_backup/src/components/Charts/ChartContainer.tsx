import React from 'react';
import styles from './ChartContainer.module.css';

interface ChartContainerProps {
    title?: string;
    action?: React.ReactNode;
    loading?: boolean;
    error?: Error;
    isEmpty?: boolean;
    children: React.ReactNode;
    chartId?: string;
    className?: string;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
    title,
    action,
    loading,
    error,
    isEmpty,
    children,
    className = ''
}) => {
    return (
        <div className={`${styles.container} ${className}`}>
            {(title || action) && (
                <div className={styles.title}>
                    <span>{title}</span>
                    {action && <div className={styles.actions}>{action}</div>}
                </div>
            )}

            <div className={styles.chartBody}>
                {loading ? (
                    <div className={styles.loading}>
                        <div className={styles.shimmer} />
                        <span style={{ zIndex: 1 }}>Initializing Analytics...</span>
                    </div>
                ) : error ? (
                    <div className={styles.error}>
                        <span className={styles.errorIcon}>⚠️</span>
                        <span className={styles.errorText}>Data Pipeline Error</span>
                        <small style={{ opacity: 0.7 }}>{error.message}</small>
                    </div>
                ) : isEmpty ? (
                    <div className={styles.empty}>
                        <span>No trajectory data available for current selection</span>
                    </div>
                ) : (
                    children
                )}
            </div>
        </div>
    );
};
