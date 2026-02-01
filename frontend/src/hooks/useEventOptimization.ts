import { useMemo } from 'react';
import { useEventsStore } from '../stores/eventsStore';

/**
 * Performance optimizations for event processing.
 */
export const useEventOptimization = () => {
    const events = useEventsStore(state => state.events);
    const clearEvents = useEventsStore(state => state.clearEvents);

    // Limit events to a rolling window (auto-cleanup handled by store maxEvents)
    // but we can add secondary filters here for high-frequency rendering

    const memoizedEvents = useMemo(() => events, [events]);

    return {
        events: memoizedEvents,
        clearEvents
    };
};
