import React, { useEffect } from 'react';
import { useStatus, useMetrics, useHealth, useWebSocket } from '../hooks';
import { useDashboardStore } from '../stores/dashboardStore';
import { WS_URL } from '../utils/constants';

/**
 * Integration Test Component
 * Verifies that all stores, hooks, and API methods work correctly.
 */
const TestIntegration: React.FC = () => {
    const { loading: statusLoading, error: statusError } = useStatus();
    const { loading: metricsLoading, error: metricsError } = useMetrics({ polling: true, interval: 2000 });
    const { health, loading: healthLoading } = useHealth({ polling: true, interval: 10000 });

    const { connected: wsConnected } = useWebSocket(WS_URL);

    const dashboard = useDashboardStore();

    useEffect(() => {
        console.log('--- Integration Test Component Mounted ---');
    }, []);

    return (
        <div style={{ padding: '20px', backgroundColor: '#1a1a1a', color: '#eee', borderRadius: '8px' }}>
            <h2>Frontend Infrastructure Integration Test</h2>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                {/* Connection Status Section */}
                <section style={{ padding: '15px', border: '1px solid #444', borderRadius: '4px' }}>
                    <h3>Connection & Status</h3>
                    <p>REST API Status: <span style={{ color: statusError ? '#ff4d4d' : '#4dff4d' }}>{statusLoading ? 'Loading...' : (statusError ? 'Error' : 'Operational')}</span></p>
                    <p>WebSocket Status: <span style={{ color: wsConnected ? '#4dff4d' : '#ff4d4d' }}>{wsConnected ? 'Connected' : 'Disconnected'}</span></p>
                    <p>Health Status: <span style={{ color: health?.status === 'healthy' ? '#4dff4d' : '#ff9900' }}>{healthLoading ? 'Checking...' : (health?.status || 'Unknown')}</span></p>
                    <hr style={{ borderColor: '#333' }} />
                    <p>Universe: <strong>{dashboard.universe}</strong></p>
                    <p>Run ID: <strong>{dashboard.runId}</strong></p>
                    <p>Batch ID: <strong>{dashboard.batchId}</strong></p>
                    <p>Paused: <strong>{dashboard.paused ? 'Yes' : 'No'}</strong></p>
                </section>

                {/* Live Metrics Section */}
                <section style={{ padding: '15px', border: '1px solid #444', borderRadius: '4px' }}>
                    <h3>Live Telemetry (Turn {dashboard.currentTurn})</h3>
                    {metricsLoading ? <p>Initial fetch...</p> : (
                        <>
                            {metricsError ? <p style={{ color: '#ff4d4d' }}>Error loading metrics</p> : (
                                <>
                                    <p>Battle Rate: <strong>{dashboard.liveMetrics?.battles?.rate || 0} / turn</strong></p>
                                    <p>Construction Rate: <strong>{dashboard.liveMetrics?.construction?.total || 0} active</strong></p>
                                    <p>Total Spawned: <strong>{dashboard.liveMetrics?.units?.total_spawned || 0}</strong></p>
                                    <p>Total Lost: <strong>{dashboard.liveMetrics?.units?.total_lost || 0}</strong></p>
                                </>
                            )}
                        </>
                    )}
                </section>
            </div>

            <div style={{ marginTop: '20px', fontSize: '12px', color: '#888' }}>
                Check Browser Console (F12) for detailed WebSocket message logs and API response data.
            </div>
        </div>
    );
};

export default TestIntegration;
