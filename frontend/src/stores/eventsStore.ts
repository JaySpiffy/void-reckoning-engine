import { create } from 'zustand';
import { produce } from 'immer';
import { TelemetryEvent } from '../types';

interface EventsState {
    events: TelemetryEvent[];
    maxEvents: number;
    autoScroll: boolean;
    eventTypeFilter: string[];
    factionFilter: string[];
    searchQuery: string;
    page: number;
    pageSize: number;
    loading: boolean;
    error: string | null;

    // Actions
    addEvent: (event: TelemetryEvent) => void;
    addBatchEvents: (events: TelemetryEvent[]) => void;
    clearEvents: () => void;
    setEventTypeFilter: (types: string[]) => void;
    setFactionFilter: (factions: string[]) => void;
    setSearchQuery: (query: string) => void;
    setPage: (page: number) => void;
    toggleAutoScroll: () => void;
}

export const useEventsStore = create<EventsState>((set, get) => ({
    events: [],
    maxEvents: 100,
    autoScroll: true,
    eventTypeFilter: [],
    factionFilter: [],
    searchQuery: '',
    page: 1,
    pageSize: 20,
    loading: false,
    error: null,

    addEvent: (event) => set(produce((state) => {
        // Deduplication: combination of timestamp, event_type, and faction
        const isDuplicate = state.events.some((e: any) =>
            e.timestamp === event.timestamp &&
            e.event_type === event.event_type &&
            e.faction === event.faction &&
            JSON.stringify(e.data) === JSON.stringify(event.data)
        );

        if (!isDuplicate) {
            state.events.unshift(event);
            if (state.events.length > state.maxEvents) {
                state.events.pop();
            }
        }
    })),

    addBatchEvents: (events) => set(produce((state) => {
        const newEvents = events.filter(event =>
            !state.events.some((e: any) =>
                e.timestamp === event.timestamp &&
                e.event_type === event.event_type &&
                e.faction === event.faction
            )
        );
        state.events = [...newEvents, ...state.events].slice(0, state.maxEvents);
    })),

    clearEvents: () => set(produce((state) => {
        state.events = [];
    })),

    setEventTypeFilter: (types) => set(produce((state) => {
        state.eventTypeFilter = types;
    })),

    setFactionFilter: (factions) => set(produce((state) => {
        state.factionFilter = factions;
    })),

    setSearchQuery: (query) => set(produce((state) => {
        state.searchQuery = query;
        state.page = 1; // Reset to first page on search
    })),

    setPage: (page) => set(produce((state) => {
        state.page = page;
    })),

    toggleAutoScroll: () => set(produce((state) => {
        state.autoScroll = !state.autoScroll;
    })),
}));

// Selectors
export const useFilteredEvents = () => {
    const events = useEventsStore(state => state.events);
    const typeFilter = useEventsStore(state => state.eventTypeFilter);
    const factionFilter = useEventsStore(state => state.factionFilter);
    const searchQuery = useEventsStore(state => state.searchQuery).toLowerCase();

    return events.filter(event => {
        const matchesType = typeFilter.length === 0 || typeFilter.includes(event.category) || typeFilter.includes(event.event_type);
        const matchesFaction = factionFilter.length === 0 || (event.faction && factionFilter.includes(event.faction));

        // Simple search in event data or faction name
        const matchesSearch = !searchQuery ||
            (event.faction?.toLowerCase().includes(searchQuery)) ||
            (event.event_type.toLowerCase().includes(searchQuery)) ||
            (JSON.stringify(event.data).toLowerCase().includes(searchQuery));

        return matchesType && matchesFaction && matchesSearch;
    });
};

export const usePaginatedEvents = () => {
    const filteredEvents = useFilteredEvents();
    const page = useEventsStore(state => state.page);
    const pageSize = useEventsStore(state => state.pageSize);

    const startIndex = (page - 1) * pageSize;
    const paginatedEvents = filteredEvents.slice(startIndex, startIndex + pageSize);
    const totalPages = Math.ceil(filteredEvents.length / pageSize);

    return {
        events: paginatedEvents,
        page,
        totalPages,
        totalEvents: filteredEvents.length
    };
};

export const useTechEvents = () => {
    const events = useEventsStore(state => state.events);
    return events.filter(e => e.category === 'technology' || e.event_type === 'tech_event' || e.event_type === 'tech_unlocked');
};
