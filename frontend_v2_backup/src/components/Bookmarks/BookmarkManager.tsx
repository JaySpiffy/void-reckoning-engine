import React, { useState } from 'react';
import { useBookmarksStore } from '../../stores/bookmarksStore';
import { useFiltersStore } from '../../stores/filtersStore';
import BookmarkItem from './BookmarkItem';
import styles from './BookmarkManager.module.css';

interface BookmarkManagerProps {
    isOpen: boolean;
    onClose: () => void;
}

const BookmarkManager: React.FC<BookmarkManagerProps> = ({ isOpen, onClose }) => {
    const {
        bookmarks,
        addBookmark,
        deleteBookmark,
        applyBookmark,
        clearAll,
        exportToFile,
        importFromFile
    } = useBookmarksStore();

    const [name, setName] = useState('');
    const [importLoading, setImportLoading] = useState(false);

    if (!isOpen) return null;

    const handleSave = () => {
        if (!name.trim()) return;
        const currentFilters = useFiltersStore.getState();
        addBookmark(name, {
            selectedFactions: currentFilters.selectedFactions,
            turnRange: currentFilters.turnRange,
            visibleMetrics: currentFilters.visibleMetrics,
            comparisonMode: currentFilters.comparisonMode,
            liveMode: currentFilters.liveMode
        });
        setName('');
    };

    const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setImportLoading(true);
        await importFromFile(file);
        setImportLoading(false);
        // Clear input
        e.target.value = '';
    };

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={e => e.stopPropagation()}>
                <div className={styles.header}>
                    <h2>Bookmark Manager</h2>
                    <button className={styles.closeBtn} onClick={onClose}>&times;</button>
                </div>

                <div className={styles.content}>
                    <div className={styles.saveSection}>
                        <input
                            type="text"
                            className={styles.nameInput}
                            placeholder="Snapshot Name (e.g. Early Game Economic Crisis)"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleSave()}
                        />
                        <button
                            className={styles.saveBtn}
                            onClick={handleSave}
                            disabled={!name.trim()}
                        >
                            Save Active Filters
                        </button>
                    </div>

                    <div className={styles.listSection}>
                        <h3>Saved Bookmarks ({bookmarks.length})</h3>
                        <div className={styles.bookmarkList}>
                            {bookmarks.length === 0 ? (
                                <div className={styles.emptyState}>No saved snapshots found.</div>
                            ) : (
                                bookmarks.map(bookmark => (
                                    <BookmarkItem
                                        key={bookmark.id}
                                        bookmark={bookmark}
                                        onLoad={() => {
                                            applyBookmark(bookmark.id);
                                            onClose();
                                        }}
                                        onDelete={() => deleteBookmark(bookmark.id)}
                                    />
                                ))
                            )}
                        </div>
                    </div>
                </div>

                <div className={styles.footer}>
                    <div className={styles.backupGroup}>
                        <button className={styles.secondaryBtn} onClick={exportToFile}>
                            Export All
                        </button>
                        <label className={styles.secondaryBtn}>
                            {importLoading ? 'Importing...' : 'Import JSON'}
                            <input type="file" accept=".json" onChange={handleImport} hidden />
                        </label>
                    </div>
                    <button className={styles.clearBtn} onClick={clearAll} disabled={bookmarks.length === 0}>
                        Clear Library
                    </button>
                </div>
            </div>
        </div>
    );
};

export default BookmarkManager;
