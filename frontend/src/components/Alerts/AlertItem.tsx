import React from 'react';
import { Alert } from '../../types';
import { useAlertsStore } from '../../stores/alertsStore';
import styles from './AlertItem.module.css';

interface AlertItemProps {
    alert: Alert;
}

const AlertItem: React.FC<AlertItemProps> = ({ alert }) => {
    const { acknowledgeAlert } = useAlertsStore();

    const timestamp = new Date(alert.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    const severityClass = styles[alert.severity] || styles.info;

    return (
        <div className={`${styles.item} ${alert.acknowledged ? styles.acknowledged : ''}`}>
            <div className={`${styles.severityBar} ${severityClass}`} />
            <div className={styles.content}>
                <div className={styles.topRow}>
                    <span className={`${styles.badge} ${severityClass}`}>
                        {alert.severity.toUpperCase()}
                    </span>
                    <span className={styles.ruleName}>{alert.rule_name}</span>
                    <span className={styles.timestamp}>{timestamp}</span>
                </div>
                <div className={styles.message}>{alert.message}</div>
                {alert.context?.turn && (
                    <div className={styles.context}>Turn {alert.context.turn}</div>
                )}
            </div>
            <div className={styles.actions}>
                {!alert.acknowledged && (
                    <button
                        className={styles.ackButton}
                        onClick={() => acknowledgeAlert(alert.id)}
                        title="Acknowledge Alert"
                    >
                        ACK
                    </button>
                )}
            </div>
        </div>
    );
};

export default AlertItem;
