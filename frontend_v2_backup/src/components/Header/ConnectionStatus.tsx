import React from 'react';
import styles from './ConnectionStatus.module.css';
import { useDashboardStore } from '../../stores/dashboardStore';

export const ConnectionStatus: React.FC = () => {
    const wsConnected = useDashboardStore((s) => s.wsConnected);
    const connectionStatus = useDashboardStore((s) => s.connectionStatus);
    const lastPingTime = useDashboardStore((s) => s.lastPingTime);

    const isOnline = wsConnected;
    const isConnecting = connectionStatus === 'connecting' || connectionStatus === 'reconnecting';
    const isError = connectionStatus === 'error';

    const isStale = isOnline && lastPingTime && (Date.now() - lastPingTime > 10000);

    const getStatusText = () => {
        if (isError) return 'SYSTEM ERROR';
        if (isOnline) return isStale ? 'LAG DETECTED' : 'ONLINE';
        if (isConnecting) return 'CONNECTING';
        return 'OFFLINE';
    };

    const getBadgeClass = () => {
        if (isError) return styles.error;
        if (isOnline) return isStale ? styles.stale : styles.online;
        if (isConnecting) return styles.connecting;
        return styles.offline;
    };

    return (
        <div className={`${styles.statusBadge} ${getBadgeClass()}`} title={lastPingTime ? `Last ping: ${new Date(lastPingTime).toLocaleTimeString()}` : 'No ping data'}>
            <span className={`${styles.dot} ${isOnline && !isStale ? styles.pulse : ''} ${isError ? styles.pulseError : ''}`}></span>
            {getStatusText()}
        </div>
    );
};
