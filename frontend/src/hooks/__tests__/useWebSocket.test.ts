import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useWebSocket } from '../useWebSocket';

describe('useWebSocket', () => {
    let mockWebSocket: any;

    beforeEach(() => {
        // Mock global WebSocket
        mockWebSocket = {
            send: vi.fn(),
            close: vi.fn(),
            readyState: 0,
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
        };
        global.WebSocket = vi.fn(() => mockWebSocket) as any;
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    it('initializes in connecting state', () => {
        const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws'));
        expect(result.current.isConnected).toBe(false);
        // Status 0 is CONNECTING
        expect(result.current.status).toBe(0);
    });

    it('connects to websocket on mount', () => {
        renderHook(() => useWebSocket('ws://localhost:8000/ws'));
        expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws');
    });

    // Note: Testing actual state transitions requires triggering the event listeners mockWebSocket registers
    // This is more involved for a quick test but basic initialization is verified.
});
