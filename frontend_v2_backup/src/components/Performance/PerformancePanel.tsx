import React, { useEffect, useState } from 'react';
import { usePerformanceStore } from '../../stores/performanceStore';
import styles from './PerformancePanel.module.css';
import MetricCard from './MetricCard';
import ProfilingToggle from './ProfilingToggle';
import SlowQueriesModal from './SlowQueriesModal';

const PerformancePanel: React.FC = () => {
    const {
        stats,
        isLoading,
        isExpanded,
        enableProfiling,
        disableProfiling,
        toggleExpanded,
        startPolling,
        stopPolling
    } = usePerformanceStore();

    const [isSlowQueriesModalOpen, setIsSlowQueriesModalOpen] = useState(false);

    // Initial polling handled by isExpanded change in store, 
    // but we can also ensure it starts if default expanded
    useEffect(() => {
        if (isExpanded) {
            startPolling();
        } else {
            stopPolling();
        }
        return () => stopPolling();
    }, [isExpanded, startPolling, stopPolling]);

    // Derived values
    const memoryUsage = stats ? stats.memory.rss_mb.toFixed(0) : '-';
    const hitRate = stats ? stats.cache.hit_rate.toFixed(1) : '-';
    const slowQueryCount = stats ? stats.profiling.slow_queries : 0;
    const isProfilingEnabled = stats ? stats.profiling_enabled : false;

    return (
        <div className={styles.container}>
            <div
                className={styles.header}
                onClick={toggleExpanded}
            >
                <h3 className={styles.headerTitle}>
                    <span role="img" aria-label="performance">📊</span>
                    Performance & Resources
                </h3>
                <span className={`${styles.toggleIcon} ${isExpanded ? styles.rotated : ''}`}>
                    ▼
                </span>
            </div>

            <div className={`${styles.content} ${isExpanded ? styles.expanded : styles.collapsed}`} style={{ display: isExpanded ? 'grid' : 'none' }}>
                <MetricCard
                    label="Memory Usage"
                    value={memoryUsage}
                    unit="MB"
                    loading={isLoading && !stats}
                />

                <MetricCard
                    label="Cache Hit Rate"
                    value={hitRate}
                    unit="%"
                    loading={isLoading && !stats}
                />

                <div className={styles.metricCard}>
                    <div className={styles.label}>Query Profiling</div>
                    <div className={styles.value}>
                        <ProfilingToggle
                            enabled={isProfilingEnabled}
                            loading={isLoading} // Simplified loading state
                            onToggle={() => isProfilingEnabled ? disableProfiling() : enableProfiling()}
                        />
                    </div>
                </div>

                <MetricCard
                    label="Slow Queries"
                    value={slowQueryCount}
                    onClick={() => setIsSlowQueriesModalOpen(true)}
                    loading={isLoading && !stats}
                />
            </div>

            <SlowQueriesModal
                isOpen={isSlowQueriesModalOpen}
                onClose={() => setIsSlowQueriesModalOpen(false)}
            />
        </div>
    );
};

export default PerformancePanel;
