import React from 'react';
import styles from './MetricsGrid.module.css';
import { useDashboardStore } from '../../stores/dashboardStore';
import { MetricCard } from './MetricCard';
import { MetricCardSkeleton } from './MetricCardSkeleton';
import { calculateTotalUnitsPerSec } from '../../utils/metrics';

export const MetricsGrid: React.FC = () => {
    const liveMetrics = useDashboardStore((s) => s.liveMetrics);
    const wsConnected = useDashboardStore((s) => s.wsConnected);

    // Connecting: Haven't received first metrics yet but WS is allegedly up
    const isConnecting = !liveMetrics && wsConnected;
    // Disconnected: WS is down
    const isError = !wsConnected;

    const battlesPerSec = liveMetrics?.battles?.rate ?? 0;
    const unitsPerSec = calculateTotalUnitsPerSec(liveMetrics?.units);

    return (
        <div className={styles.grid}>
            <MetricCard
                label="Battles / Sec"
                value={battlesPerSec}
                unit="OPS"
                accentColor={true}
                loading={isConnecting}
                error={isError ? new Error('Disconnected') : null}
            />
            <MetricCard
                label="Units / Sec"
                value={unitsPerSec}
                unit="REQ"
                accentColor={false}
                loading={isConnecting}
                error={isError ? new Error('Disconnected') : null}
            />
        </div>
    );
};
