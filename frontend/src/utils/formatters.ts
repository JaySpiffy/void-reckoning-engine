/**
 * Utility functions for formatting data.
 */

/**
 * Format a number with commas and specified decimal places.
 */
export const formatNumber = (value: number, decimals: number = 0): string => {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(value);
};

/**
 * Format a per-second rate.
 */
export const formatRate = (value: number): string => {
    return `${formatNumber(value, 2)}/s`;
};

/**
 * Format a turn number.
 */
export const formatTurn = (turn: number): string => {
    return `Turn ${turn}`;
};

/**
 * Format a Unix timestamp to a readable date/time string.
 */
export const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp).toLocaleString();
};

/**
 * Format a duration in seconds to a readable string (e.g., "2h 15m").
 */
export const formatDuration = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    const parts = [];
    if (h > 0) parts.push(`${h}h`);
    if (m > 0 || h > 0) parts.push(`${m}m`);
    parts.push(`${s}s`);

    return parts.join(' ');
};

/**
 * Truncate a string with an ellipsis.
 */
export const truncate = (str: string, length: number): string => {
    if (str.length <= length) return str;
    return str.slice(0, length) + '...';
};
