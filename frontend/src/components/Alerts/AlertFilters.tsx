import React from 'react';
import { useAlertsStore } from '../../stores/alertsStore';
import { AlertSeverity } from '../../types';
import styles from './AlertFilters.module.css';

const AlertFilters: React.FC = () => {
    const {
        severityFilter,
        setSeverityFilter,
        typeFilter,
        setTypeFilter,
        showHistory,
        toggleHistory
    } = useAlertsStore();

    const severities: AlertSeverity[] = ['critical', 'error', 'warning', 'info'];

    const handleSeverityToggle = (severity: AlertSeverity) => {
        const nextFilter = severityFilter.includes(severity)
            ? severityFilter.filter(s => s !== severity)
            : [...severityFilter, severity];

        setSeverityFilter(nextFilter);

        // Trigger re-fetch if in history mode
        if (showHistory) {
            useAlertsStore.getState().fetchAlertHistory(1);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.filterGroup}>
                <span className={styles.label}>Severity:</span>
                <div className={styles.chipGroup}>
                    {severities.map(s => (
                        <button
                            key={s}
                            className={`${styles.chip} ${styles[s]} ${severityFilter.includes(s) ? styles.active : ''}`}
                            onClick={() => handleSeverityToggle(s)}
                        >
                            {s.toUpperCase()}
                        </button>
                    ))}
                </div>
            </div>

            <div className={styles.filterGroup}>
                <span className={styles.label}>Type:</span>
                <select
                    className={styles.select}
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                >
                    <option value="ALL">ALL</option>
                    <option value="economy_alert">Economy</option>
                    <option value="combat_alert">Combat</option>
                    <option value="system_alert">System</option>
                </select>
            </div>

            <div className={styles.historyToggle}>
                <label className={styles.toggleLabel}>
                    <input
                        type="checkbox"
                        checked={showHistory}
                        onChange={toggleHistory}
                    />
                    <span>Show History</span>
                </label>
            </div>
        </div>
    );
};

export default AlertFilters;
