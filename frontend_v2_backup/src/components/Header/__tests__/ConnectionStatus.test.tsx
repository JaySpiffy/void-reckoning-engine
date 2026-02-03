import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ConnectionStatus } from '../ConnectionStatus';
import * as useWebSocketModule from '../../../hooks/useWebSocket';

// Mock the hook
vi.mock('../../../hooks/useWebSocket', () => ({
    useWebSocket: vi.fn(),
    WebSocketStatus: {
        CONNECTING: 0,
        OPEN: 1,
        CLOSING: 2,
        CLOSED: 3
    }
}));

describe('ConnectionStatus', () => {
    it('renders connected state correctly', () => {
        vi.spyOn(useWebSocketModule, 'useWebSocket').mockReturnValue({
            status: 1, // OPEN
            lastMessage: null,
            isConnected: true,
            connect: vi.fn(),
            disconnect: vi.fn(),
            sendMessage: vi.fn()
        });

        render(<ConnectionStatus />);
        expect(screen.getByText(/Connected/i)).toBeInTheDocument();
        // Check for green indicator class or style if possible, 
        // usually implicitly tested by text presence or specific data-testid
    });

    it('renders disconnected state correctly', () => {
        vi.spyOn(useWebSocketModule, 'useWebSocket').mockReturnValue({
            status: 3, // CLOSED
            lastMessage: null,
            isConnected: false,
            connect: vi.fn(),
            disconnect: vi.fn(),
            sendMessage: vi.fn()
        });

        render(<ConnectionStatus />);
        expect(screen.getByText(/Disconnected/i)).toBeInTheDocument();
    });

    it('renders connecting state correctly', () => {
        vi.spyOn(useWebSocketModule, 'useWebSocket').mockReturnValue({
            status: 0, // CONNECTING
            lastMessage: null,
            isConnected: false,
            connect: vi.fn(),
            disconnect: vi.fn(),
            sendMessage: vi.fn()
        });

        render(<ConnectionStatus />);
        expect(screen.getByText(/Connecting/i)).toBeInTheDocument();
    });
});
