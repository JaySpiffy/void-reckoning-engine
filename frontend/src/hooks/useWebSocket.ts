import { useEffect, useRef, useState, useCallback } from 'react';
import { useDashboardStore } from '../stores/dashboardStore';
import { useMetricsStore } from '../stores/metricsStore';
import { useAlertsStore } from '../stores/alertsStore';
import { useEventsStore } from '../stores/eventsStore';
import { WSMessage, TelemetryEvent, Alert } from '../types';
import { useGalaxyStore } from '../stores/galaxyStore';
import { UI_COLORS } from '../utils/factionColors';

interface WebSocketOptions {
    autoConnect?: boolean;
    reconnectInterval?: number;
    maxReconnectAttempts?: number;
}

/**
 * Custom hook for native FastAPI WebSocket management.
 * Handles automatic reconnection, ping/pong, and event routing.
 */
export const useWebSocket = (url: string, options: WebSocketOptions = {}) => {
    const {
        autoConnect = true,
        reconnectInterval = 3000,
        maxReconnectAttempts = 10
    } = options;

    const [connected, setConnected] = useState(false);
    const [error, setError] = useState<Event | null>(null);
    const socketRef = useRef<WebSocket | null>(null);
    const reconnectCountRef = useRef(0);
    const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Store actions
    const setWsConnected = useDashboardStore((s) => s.setWebSocketConnected);
    const setConnectionStatus = useDashboardStore((s) => s.setConnectionStatus);
    const updateStatus = useDashboardStore((s) => s.updateStatus);
    const updateMetrics = useDashboardStore((s) => s.updateMetrics);
    const setLastPingTime = useDashboardStore((s) => s.setLastPingTime);

    const addBattleMetric = useMetricsStore((s) => s.addBattleMetric);
    const addEconomicSnapshot = useMetricsStore((s) => s.addEconomicSnapshot);
    const addAlert = useAlertsStore((s) => s.addAlert);

    // Galaxy store actions
    const addAnimation = useGalaxyStore((s) => s.addAnimation);
    const updateSystemControl = useGalaxyStore((s) => s.updateSystemControl);
    const addAlertFromWebSocket = useAlertsStore((s) => s.addAlertFromWebSocket);
    const addEvent = useEventsStore((s) => s.addEvent);

    const connect = useCallback(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) return;

        console.log(`Connecting to WebSocket: ${url}`);
        setConnectionStatus('connecting');
        const socket = new WebSocket(url);
        socketRef.current = socket;

        socket.onopen = () => {
            console.log('WebSocket Connected');
            setConnected(true);
            setWsConnected(true);
            setConnectionStatus('connected');
            setError(null);
            reconnectCountRef.current = 0;
        };

        socket.onclose = (event) => {
            console.log('WebSocket Closed:', event.code, event.reason);
            setConnected(false);
            setWsConnected(false);

            // Always attempt reconnect unless we intentionally disconnected/unmounted
            // 1000 = Normal Closure, 1001 = Going Away (Server Restart)
            // We want to reconnect on 1001, and arguably 1000 if it wasn't us initiating.
            if (reconnectCountRef.current < maxReconnectAttempts) {
                setConnectionStatus('reconnecting');
                const timeout = reconnectInterval * Math.pow(1.5, reconnectCountRef.current);
                console.log(`Connection lost (${event.code}). Reconnecting in ${timeout}ms...`);
                reconnectTimerRef.current = setTimeout(() => {
                    reconnectCountRef.current += 1;
                    connect();
                }, timeout);
            } else {
                setConnectionStatus('disconnected');
            }
        };

        socket.onerror = (err) => {
            console.error('WebSocket Error:', err);
            setError(err);
            setConnectionStatus('error');
        };

        socket.onmessage = (event) => {
            try {
                const msg: WSMessage = JSON.parse(event.data);
                handleMessage(msg);
            } catch (err) {
                console.error('Failed to parse WebSocket message:', err);
            }
        };
    }, [url, reconnectInterval, maxReconnectAttempts, setWsConnected]);

    const disconnect = useCallback(() => {
        if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
        socketRef.current?.close();
        socketRef.current = null;
    }, []);

    const sendMessage = useCallback((msg: any) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify(msg));
        } else {
            console.warn('Cannot send message: WebSocket is not open');
        }
    }, []);

    const handleMessage = (msg: WSMessage) => {
        switch (msg.type) {
            case 'ping':
                setLastPingTime(Date.now());
                sendMessage({ type: 'pong', timestamp: Date.now() });
                break;

            case 'status_update':
                if (msg.data) updateStatus(msg.data);
                break;

            case 'metrics_update':
                if (msg.data) {
                    updateMetrics(msg.data);
                    // Accumulate history selectively
                    if (msg.data.battles) addBattleMetric(msg.data.battles);

                    // Live Galaxy Updates
                    if (msg.data.planet_status) {
                        // Group planets by system and update control
                        const systemsToUpdate: Record<string, { control: Record<string, number>, owner: string }> = {};

                        Object.entries(msg.data.planet_status).forEach(([planetName, status]: [string, any]) => {
                            const systemName = status.system;
                            if (!systemName) return;

                            if (!systemsToUpdate[systemName]) {
                                systemsToUpdate[systemName] = { control: {}, owner: status.owner };
                            }

                            const faction = status.owner;
                            systemsToUpdate[systemName].control[faction] = (systemsToUpdate[systemName].control[faction] || 0) + 1;
                        });

                        Object.entries(systemsToUpdate).forEach(([name, data]) => {
                            updateSystemControl(name, data.control, data.owner);
                        });
                    }
                }
                break;

            case 'battle_event':
                handleTelemetryEvent(msg.data as TelemetryEvent, 'combat');
                break;

            case 'resource_event':
                handleTelemetryEvent(msg.data as TelemetryEvent, 'economy');
                break;

            case 'tech_event':
                handleTelemetryEvent(msg.data as TelemetryEvent, 'technology');
                break;

            case 'construction_event':
                handleTelemetryEvent(msg.data as TelemetryEvent, 'construction');
                break;

            case 'system_event':
                handleTelemetryEvent(msg.data as TelemetryEvent, 'system');
                break;

            case 'movement_event':
                handleTelemetryEvent(msg.data as TelemetryEvent, 'movement');
                break;

            case 'campaign_event':
                handleTelemetryEvent(msg.data as TelemetryEvent, 'campaign');
                break;

            case 'strategy_event':
                handleTelemetryEvent(msg.data as TelemetryEvent, 'strategy');
                break;

            case 'doctrine_event':
                handleTelemetryEvent(msg.data as TelemetryEvent, 'doctrine');
                break;

            case 'alert_triggered':
                if (msg.data) {
                    addAlertFromWebSocket(msg.data as Alert);
                }
                break;

            case 'error_notification':
                if (msg.data) {
                    addAlert({
                        severity: 'critical',
                        category: 'system',
                        message: msg.data.error,
                        data: msg.data.details
                    });
                }
                break;

            default:
            // console.debug('Unhandled WS message type:', msg.type);
        }
    };

    const handleTelemetryEvent = (event: TelemetryEvent, category: string) => {
        if (!event) return;

        // Route to events store
        addEvent({
            ...event,
            category: event.category || category
        });

        // Galaxy animations for battles
        if (category === 'combat' && (event.event_type === 'battle_start' || event.event_type === 'battle_end')) {
            const systemName = event.data?.system;
            const currentSystems = useGalaxyStore.getState().systems;
            const system = currentSystems.find(s => s.name === systemName);
            if (system) {
                addAnimation({
                    x: system.x,
                    y: system.y,
                    color: UI_COLORS.battle,
                    type: 'battle'
                });
            }
        }

        // Live ownership updates from system events
        if (category === 'system' && event.event_type === 'system_captured') {
            const systemName = event.data?.system;
            const newOwner = event.data?.new_owner;
            if (systemName && newOwner) {
                const currentSystems = useGalaxyStore.getState().systems;
                const system = currentSystems.find(s => s.name === systemName);
                if (system) {
                    updateSystemControl(systemName, system.control, newOwner);
                    addAnimation({
                        x: system.x,
                        y: system.y,
                        color: UI_COLORS.capture,
                        type: 'capture'
                    });
                }
            }
        }

        // Example: Trigger alert for major combat losses or massive economic shifts
        if (category === 'combat' && event.event_type === 'battle_start') {
            // Just as an example integration
        }

        if (category === 'economy' && event.event_type === 'income_collected') {
            // Process for metrics history if needed
        }
    };

    useEffect(() => {
        if (autoConnect) {
            connect();
        }
        return () => disconnect();
    }, [autoConnect, connect, disconnect]);

    return { connected, error, sendMessage, connect, disconnect };
};
