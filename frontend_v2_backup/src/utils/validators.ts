/**
 * Validation helpers for the dashboard application.
 */

import { EVENT_CATEGORIES, METRIC_TYPES } from './constants';

/**
 * Check if a faction name is valid (non-empty).
 */
export const isValidFaction = (faction: string): boolean => {
    return typeof faction === 'string' && faction.trim().length > 0;
};

/**
 * Check if a turn range is valid.
 */
export const isValidTurnRange = (min: number, max: number): boolean => {
    return typeof min === 'number' && typeof max === 'number' && min <= max && min >= 0;
};

/**
 * Check if an event category is recognized by the system.
 */
export const isValidEventCategory = (category: string): boolean => {
    return EVENT_CATEGORIES.includes(category);
};

/**
 * Check if a metric type is valid.
 */
export const isValidMetricType = (type: string): boolean => {
    return METRIC_TYPES.includes(type);
};

/**
 * Check if a WebSocket message type is valid (basic check).
 */
export const isValidWSType = (type: string): boolean => {
    const validTypes = [
        'status_update', 'snapshot', 'metrics_update', 'event_stream',
        'battle_event', 'resource_event', 'tech_event', 'construction_event',
        'system_event', 'error_notification', 'ping', 'pong', 'response'
    ];
    return validTypes.includes(type);
};
