import React from 'react';
import styles from './StatusMessage.module.css';
import { StatusMessageProps } from '../../types/components';
import { formatTimestamp } from '../../utils/formatters';

export const StatusMessage: React.FC<StatusMessageProps> = ({ message, type, timestamp }) => {
    const getIcon = () => {
        switch (type) {
            case 'warning': return '⚠️';
            case 'error': return '❌';
            default: return 'ℹ️';
        }
    };

    return (
        <div className={`${styles.message} ${styles[type]}`}>
            <div className={styles.icon}>{getIcon()}</div>
            <div className={styles.content}>
                <span className={styles.text}>{message}</span>
                <span className={styles.timestamp}>{formatTimestamp(new Date(timestamp))}</span>
            </div>
        </div>
    );
};
