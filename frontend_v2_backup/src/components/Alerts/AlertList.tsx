import React from 'react';
import { Alert } from '../../types';
import AlertItem from './AlertItem';
import styles from './AlertsPanel.module.css';

import { useAlertsStore } from '../../stores/alertsStore';

interface AlertListProps {
    alerts: Alert[];
    loading: boolean;
}

const AlertList: React.FC<AlertListProps> = ({ alerts, loading }) => {
    const {
        severityFilter,
        typeFilter,
        showHistory,
        page,
        total,
        pageSize,
        fetchAlertHistory
    } = useAlertsStore();

    // Client-side filtering as a backup or for active alerts
    const filteredAlerts = alerts.filter(alert => {
        // Severity filter
        if (!severityFilter.includes(alert.severity)) return false;

        // Type filter (assuming rule_name contains the category or we have it in context)
        if (typeFilter !== 'ALL') {
            const ruleName = alert.rule_name.toLowerCase();
            const category = typeFilter.toLowerCase();
            if (!ruleName.includes(category)) return false;
        }

        if (showHistory) return true; // Server-side filtering for history

        return true;
    });

    if (loading && alerts.length === 0) {
        return <div className={styles.loading}>Scanning sector for anomalies...</div>;
    }

    if (filteredAlerts.length === 0) {
        return (
            <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>✓</div>
                <div className={styles.emptyText}>No matching anomalies detected in sector.</div>
            </div>
        );
    }

    const totalPages = Math.ceil(total / pageSize);

    return (
        <div className={styles.alertListContainer}>
            <div className={styles.alertList}>
                {filteredAlerts.map((alert) => (
                    <AlertItem key={alert.id} alert={alert} />
                ))}
            </div>

            {showHistory && total > pageSize && (
                <div className={styles.pagination}>
                    <button
                        disabled={page === 1 || loading}
                        onClick={() => fetchAlertHistory(page - 1)}
                        className={styles.pageButton}
                    >
                        PREV
                    </button>
                    <span className={styles.pageInfo}>
                        PAGE {page} OF {totalPages} ({total} TOTAL)
                    </span>
                    <button
                        disabled={page === totalPages || loading}
                        onClick={() => fetchAlertHistory(page + 1)}
                        className={styles.pageButton}
                    >
                        NEXT
                    </button>
                </div>
            )}
        </div>
    );
};

export default AlertList;
