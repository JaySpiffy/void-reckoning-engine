import React, { useState, useEffect, useRef } from 'react';
import styles from './StatusFeed.module.css';
import { useDashboardStore } from '../../stores/dashboardStore';
import { Card } from '../Layout/Card';
import { StatusMessage } from './StatusMessage';

interface LogEntry {
    id: string;
    message: string;
    type: 'info' | 'warning' | 'error';
    timestamp: number;
}

export const StatusFeed: React.FC = () => {
    const [messages, setMessages] = useState<LogEntry[]>([]);
    const feedRef = useRef<HTMLDivElement>(null);
    const [isInitializing, setIsInitializing] = useState(true);

    const {
        wsConnected,
        telemetryConnected,
        indexerConnected,
        paused
    } = useDashboardStore();

    // Initial load timer
    useEffect(() => {
        const timer = setTimeout(() => setIsInitializing(false), 2000);
        return () => clearTimeout(timer);
    }, []);

    // Monitor state changes to generate log messages
    useEffect(() => {
        const addMessage = (text: string, type: 'info' | 'warning' | 'error' = 'info') => {
            const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            setMessages(prev => {
                if (prev.length > 0 && prev[0].message === text) return prev;
                return [{ id, message: text, type, timestamp: Date.now() }, ...prev].slice(0, 20);
            });
        };

        if (wsConnected) {
            addMessage('Telemetry stream connection established', 'info');
        } else if (!isInitializing) {
            addMessage('Critical: Telemetry stream disconnected', 'error');
        }
    }, [wsConnected, isInitializing]);

    useEffect(() => {
        const addMessage = (text: string, type: 'info' | 'warning' | 'error' = 'info') => {
            const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            setMessages(prev => {
                if (prev.length > 0 && prev[0].message === text) return prev;
                return [{ id, message: text, type, timestamp: Date.now() }, ...prev].slice(0, 20);
            });
        };

        if (paused) {
            addMessage('Simulation PAUSED by operator', 'warning');
        } else if (messages.length > 0) {
            addMessage('Simulation cycle RESUMED', 'info');
        }
    }, [paused]);

    const handleReconnect = () => {
        window.location.reload(); // Simple reconnect for now
    };

    return (
        <Card title="System Status Feed">
            {!wsConnected && !isInitializing && (
                <div className={styles.errorBanner}>
                    <span className={styles.errorTitle}>Telemetry Grid Offline</span>
                    <button className={styles.reconnectBtn} onClick={handleReconnect}>
                        Initialize Handshake
                    </button>
                </div>
            )}

            <div className={styles.feedContainer} ref={feedRef}>
                {isInitializing && messages.length === 0 ? (
                    <>
                        <div className={`${styles.skeletonItem} skeleton`} />
                        <div className={`${styles.skeletonItem} skeleton`} />
                        <div className={`${styles.skeletonItem} skeleton`} />
                    </>
                ) : messages.length === 0 ? (
                    <div className={styles.emptyState}>
                        Systems Nominal. Monitoring telemetry grid...
                    </div>
                ) : (
                    messages.map((msg) => (
                        <StatusMessage
                            key={msg.id}
                            message={msg.message}
                            type={msg.type}
                            timestamp={msg.timestamp}
                        />
                    ))
                )}
            </div>
        </Card>
    );
};
