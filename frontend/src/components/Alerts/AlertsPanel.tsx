import React, { useEffect } from 'react';
import { useAlertsStore } from '../../stores/alertsStore';
import AlertList from './AlertList';
import AnomalyChart from './AnomalyChart';
import AlertFilters from './AlertFilters';
import styles from './AlertsPanel.module.css';

const AlertsPanel: React.FC = () => {
    const {
        alerts,
        summary,
        loading,
        error,
        fetchActiveAlerts,
        fetchSummary
    } = useAlertsStore();

    useEffect(() => {
        fetchActiveAlerts();
        fetchSummary();

        // Refresh summary periodically
        const interval = setInterval(() => {
            fetchSummary();
        }, 30000);

        return () => clearInterval(interval);
    }, [fetchActiveAlerts, fetchSummary]);

    const activeCount = summary?.active || 0;
    const criticalCount = summary?.by_severity?.critical || 0;
    const warningCount = summary?.by_severity?.warning || 0;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.titleGroup}>
                    <h2 className={styles.title}>
                        Anomalies & Alerts
                        {activeCount > 0 && <span className={styles.pulseIndicator} />}
                    </h2>
                    <div className={styles.summaryBadges}>
                        {criticalCount > 0 && (
                            <span className={`${styles.badge} ${styles.badgeCritical}`}>
                                {criticalCount} CRITICAL
                            </span>
                        )}
                        {warningCount > 0 && (
                            <span className={`${styles.badge} ${styles.badgeWarning}`}>
                                {warningCount} WARNING
                            </span>
                        )}
                    </div>
                </div>
                <AlertFilters />
            </div>

            <div className={styles.content}>
                <div className={styles.mainContent}>
                    {error && <div className={styles.error}>Error: {error}</div>}
                    <AlertList alerts={alerts} loading={loading} />
                </div>
                <div className={styles.sidebar}>
                    <div className={styles.chartTitle}>Severity Distribution</div>
                    <AnomalyChart summary={summary} />
                </div>
            </div>
        </div>
    );
};

export default AlertsPanel;
