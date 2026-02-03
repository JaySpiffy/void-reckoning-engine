import React, { useEffect, useState } from 'react';
import { useDiagnosticsStore } from '../../stores/diagnosticsStore';
import styles from './HealthStatus.module.css';

const HealthStatus: React.FC = () => {
    const { healthStatus, isLoading, fetchHealthStatus } = useDiagnosticsStore();
    const [expanded, setExpanded] = useState(false);

    useEffect(() => {
        fetchHealthStatus();
        const interval = setInterval(fetchHealthStatus, 30000); // 30s poll
        return () => clearInterval(interval);
    }, [fetchHealthStatus]);

    if (!healthStatus) return null;

    return (
        <div className={styles.container}>
            <div
                className={`${styles.statusBadge} ${styles[healthStatus.overall_status]}`}
                onClick={() => setExpanded(!expanded)}
                style={{ cursor: 'pointer' }}
            >
                SYSTEM: {healthStatus.overall_status}
            </div>

            {expanded && (
                <>
                    <div className={styles.componentList}>
                        {healthStatus.components.map((comp) => (
                            <div key={comp.component} className={styles.componentItem}>
                                <span className={styles.componentName}>
                                    {comp.component.replace('_', ' ')}
                                </span>
                                <div className={`${styles.statusIndicator} ${styles[comp.status]}`} title={comp.message} />
                            </div>
                        ))}
                    </div>

                    <button
                        className={styles.refreshButton}
                        onClick={() => fetchHealthStatus()}
                        disabled={isLoading}
                    >
                        {isLoading ? '...' : 'Refresh'}
                    </button>

                    <div className={styles.timestamp}>
                        Last Check: {new Date(healthStatus.timestamp * 1000).toLocaleTimeString()}
                    </div>
                </>
            )}
        </div>
    );
};

export default HealthStatus;
