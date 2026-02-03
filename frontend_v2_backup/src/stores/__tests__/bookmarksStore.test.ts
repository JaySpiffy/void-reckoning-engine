import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useBookmarksStore } from '../bookmarksStore';
import { Bookmark } from '../../types';

// Mock localStorage
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: vi.fn((key: string) => store[key] || null),
        setItem: vi.fn((key: string, value: string) => {
            store[key] = value.toString();
        }),
        clear: vi.fn(() => {
            store = {};
        }),
    };
})();

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
});

// Mock URL.createObjectURL and revokeObjectURL
window.URL.createObjectURL = vi.fn();
window.URL.revokeObjectURL = vi.fn();

describe('bookmarksStore', () => {
    beforeEach(() => {
        localStorageMock.clear();
        vi.clearAllMocks();
        // Reset store state
        useBookmarksStore.setState({ bookmarks: [] });
    });

    it('should add a bookmark', () => {
        const store = useBookmarksStore.getState();
        const filters = {
            selectedFactions: ['Imperium'],
            turnRange: { min: 0, max: 100 },
            visibleMetrics: { economy: true },
            comparisonMode: false,
            liveMode: true,
        };

        store.addBookmark('Test Bookmark', filters);

        const updatedStore = useBookmarksStore.getState();
        expect(updatedStore.bookmarks).toHaveLength(1);
        expect(updatedStore.bookmarks[0].name).toBe('Test Bookmark');
        expect(updatedStore.bookmarks[0].filters).toEqual(filters);
        expect(localStorageMock.setItem).toHaveBeenCalled();
    });

    it('should delete a bookmark', () => {
        const store = useBookmarksStore.getState();
        const filters = {
            selectedFactions: [],
            turnRange: { min: 0, max: 0 },
            visibleMetrics: {},
            comparisonMode: false,
            liveMode: false,
        };

        store.addBookmark('To Delete', filters);
        const bookmarkId = useBookmarksStore.getState().bookmarks[0].id;

        useBookmarksStore.getState().deleteBookmark(bookmarkId);

        expect(useBookmarksStore.getState().bookmarks).toHaveLength(0);
        expect(localStorageMock.setItem).toHaveBeenCalledTimes(2);
    });

    it('should clear all bookmarks', () => {
        const store = useBookmarksStore.getState();
        store.addBookmark('B1', {} as any);
        store.addBookmark('B2', {} as any);

        store.clearAll();

        expect(useBookmarksStore.getState().bookmarks).toHaveLength(0);
        expect(localStorageMock.setItem).toHaveBeenCalled();
    });

    it('should export bookmarks to a file', () => {
        const store = useBookmarksStore.getState();
        store.addBookmark('Export Me', {} as any);

        const documentSpy = vi.spyOn(document, 'createElement');
        const appendSpy = vi.spyOn(document.body, 'appendChild');
        const removeSpy = vi.spyOn(document.body, 'removeChild');

        store.exportToFile();

        expect(window.URL.createObjectURL).toHaveBeenCalled();
        expect(documentSpy).toHaveBeenCalledWith('a');
        expect(appendSpy).toHaveBeenCalled();
        expect(removeSpy).toHaveBeenCalled();
    });

    it('should import bookmarks from a file', async () => {
        const store = useBookmarksStore.getState();
        const mockBookmarks: Bookmark[] = [
            {
                id: '1',
                name: 'Imported',
                timestamp: new Date().toISOString(),
                filters: {
                    selectedFactions: ['Chaos'],
                    turnRange: { min: 10, max: 20 },
                    visibleMetrics: {},
                    comparisonMode: true,
                    liveMode: false
                }
            }
        ];
        const blob = new Blob([JSON.stringify(mockBookmarks)], { type: 'application/json' });
        const file = new File([blob], 'bookmarks.json');

        await store.importFromFile(file);

        expect(useBookmarksStore.getState().bookmarks).toHaveLength(1);
        expect(useBookmarksStore.getState().bookmarks[0].name).toBe('Imported');
    });
});
