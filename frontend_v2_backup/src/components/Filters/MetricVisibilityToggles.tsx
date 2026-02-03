import React from 'react';
import styles from './MetricVisibilityToggles.module.css';
import { useFiltersStore } from '../../stores/filtersStore';

export const MetricVisibilityToggles: React.FC = () => {
    const { visibleMetrics, toggleMetricVisibility } = useFiltersStore();

    const metrics = [
        { id: 'battles', label: 'Battles' },
        { id: 'units', label: 'Units' },
        { id: 'economy', label: 'Economy' },
        { id: 'construction', label: 'Construction' },
        { id: 'research', label: 'Research' },
    ] as const;

    return (
        <div className={styles.visibilityPanel}>
            {metrics.map((metric) => (
                <label
                    key={metric.id}
                    className={`${styles.toggleItem} ${visibleMetrics[metric.id] ? styles.active : ''}`}
                >
                    <input
                        type="checkbox"
                        checked={visibleMetrics[metric.id]}
                        onChange={() => toggleMetricVisibility(metric.id)}
                    />
                    <span className={styles.label}>{metric.label}</span>
                </label>
            ))}
        </div>
    );
};

export default MetricVisibilityToggles;
