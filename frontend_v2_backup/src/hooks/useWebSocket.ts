import { useEffect, useRef, useState } from 'react';
import type { WebSocketMessage } from '../types/telemetry';

export const useWebSocket = <T>(url: string) => {
  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    let timeoutId: number;
    let isMounted = true;

    const connect = () => {
        try {
            const wsUrl = url.startsWith('ws') ? url : `ws://${window.location.host}${url}`;
            const socket = new WebSocket(wsUrl);
            ws.current = socket;

            socket.onopen = () => {
              console.log('[WS] Connected');
              if (isMounted) setIsConnected(true);
            };

            socket.onmessage = (event) => {
              if (!isMounted) return;
              try {
                const message: WebSocketMessage = JSON.parse(event.data);
                if (message.type === 'metrics_update' || message.type === 'snapshot') {
                    setData(message.data as T);
                }
              } catch (e) {
                console.error('[WS] Parse error', e);
              }
            };

            socket.onclose = () => {
              console.log('[WS] Disconnected');
              if (isMounted) {
                  setIsConnected(false);
                  timeoutId = window.setTimeout(connect, 3000);
              }
            };

            socket.onerror = (e) => {
                 console.error("[WS] Error", e);
                 socket.close();
            }
        } catch (e) {
            console.error("[WS] Connection failed", e);
            if (isMounted) timeoutId = window.setTimeout(connect, 5000);
        }
    };

    connect();

    return () => {
        isMounted = false;
        if (ws.current) ws.current.close();
        if (timeoutId) clearTimeout(timeoutId);
    };
  }, [url]);

  return { data, isConnected };
};
