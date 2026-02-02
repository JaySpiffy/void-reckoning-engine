import { TelemetryEvent } from '../types';
import { formatEventMessage, formatEventTime } from './eventFormatters';

/**
 * Exports an array of events as a JSON file.
 */
export const exportEventsAsJSON = (events: TelemetryEvent[]): void => {
    const dataStr = JSON.stringify(events, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `telemetry_events_${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
};

/**
 * Exports an array of events as a CSV file.
 */
export const exportEventsAsCSV = (events: TelemetryEvent[]): void => {
    const headers = ['Timestamp', 'Turn', 'Category', 'Type', 'Faction', 'Message'];
    const rows = events.map(event => [
        new Date(event.timestamp * 1000).toISOString(),
        event.turn || 'N/A',
        event.category,
        event.event_type,
        event.faction || 'Neutral',
        formatEventMessage(event).replace(/,/g, ';') // Avoid CSV break on message commas
    ]);

    const csvContent = [
        headers.join(','),
        ...rows.map(r => r.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `telemetry_log_${Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
};
