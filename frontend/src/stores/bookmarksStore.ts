import { create } from 'zustand';
import { Bookmark } from '../types';
import { useFiltersStore } from './filtersStore';

interface BookmarksState {
    bookmarks: Bookmark[];
    addBookmark: (name: string, filters: Bookmark['filters']) => void;
    deleteBookmark: (id: string) => void;
    applyBookmark: (id: string) => void;
    clearAll: () => void;
    exportToFile: () => void;
    importFromFile: (file: File) => Promise<void>;
}

const STORAGE_KEY = 'dashboard_bookmarks';

const loadFromStorage = (): Bookmark[] => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch (error) {
        console.error('Failed to load bookmarks from localStorage:', error);
        return [];
    }
};

const saveToStorage = (bookmarks: Bookmark[]) => {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
    } catch (error) {
        console.error('Failed to save bookmarks to localStorage:', error);
    }
};

export const useBookmarksStore = create<BookmarksState>((set, get) => ({
    bookmarks: loadFromStorage(),

    addBookmark: (name, filters) => {
        const newBookmark: Bookmark = {
            id: crypto.randomUUID(),
            name,
            timestamp: new Date().toISOString(),
            filters: JSON.parse(JSON.stringify(filters)) // Deep clone filters
        };

        set((state) => {
            const updated = [newBookmark, ...state.bookmarks];
            saveToStorage(updated);
            return { bookmarks: updated };
        });
    },

    deleteBookmark: (id) => {
        set((state) => {
            const updated = state.bookmarks.filter(b => b.id !== id);
            saveToStorage(updated);
            return { bookmarks: updated };
        });
    },

    applyBookmark: (id) => {
        const bookmark = get().bookmarks.find(b => b.id === id);
        if (bookmark) {
            const filterState = useFiltersStore.getState();
            // Apply each filter property
            filterState.setFactions(bookmark.filters.selectedFactions);
            filterState.setTurnRange(bookmark.filters.turnRange.min, bookmark.filters.turnRange.max);
            filterState.setComparisonMode(bookmark.filters.comparisonMode);
            filterState.setLiveMode(bookmark.filters.liveMode);

            // Handle visibleMetrics individually
            Object.entries(bookmark.filters.visibleMetrics).forEach(([key, value]) => {
                const metricKey = key as keyof typeof filterState.visibleMetrics;
                if (filterState.visibleMetrics[metricKey] !== value) {
                    filterState.toggleMetricVisibility(metricKey);
                }
            });
        }
    },

    clearAll: () => {
        if (window.confirm('Are you sure you want to clear all bookmarks?')) {
            saveToStorage([]);
            set({ bookmarks: [] });
        }
    },

    exportToFile: () => {
        const data = {
            version: '1.0',
            exported_at: new Date().toISOString(),
            bookmarks: get().bookmarks
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dashboard_bookmarks_${new Date().getTime()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    importFromFile: async (file) => {
        try {
            const text = await file.text();
            const data = JSON.parse(text);

            if (!data.bookmarks || !Array.isArray(data.bookmarks)) {
                throw new Error('Invalid bookmark file format');
            }

            set((state) => {
                // Merge bookmarks, avoiding ID duplicates but keeping new entries at top
                const existingIds = new Set(state.bookmarks.map(b => b.id));
                const newBookmarks = data.bookmarks.filter((b: Bookmark) => !existingIds.has(b.id));
                const updated = [...newBookmarks, ...state.bookmarks];
                saveToStorage(updated);
                return { bookmarks: updated };
            });
        } catch (error) {
            console.error('Failed to import bookmarks:', error);
            alert('Failed to import bookmarks. Please ensure the file is a valid JSON export.');
        }
    }
}));
