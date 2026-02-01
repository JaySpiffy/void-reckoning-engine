/**
 * Constants for the frontend application.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
export const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws`;

export const DEFAULT_TIME_WINDOW = 60; // seconds
export const RECONNECT_INTERVAL = 3000;
export const MAX_RECONNECT_ATTEMPTS = 10;

export const EVENT_CATEGORIES = [
    'combat',
    'economy',
    'technology',
    'construction',
    'system',
    'diplomacy',
    'movement',
    'campaign',
    'strategy',
    'doctrine'
];

export const METRIC_TYPES = [
    'battles',
    'units',
    'economy',
    'construction',
    'research'
];

export const SEVERITIES = ['info', 'warning', 'critical'] as const;
