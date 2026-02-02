import React from 'react';
import { Bookmark } from '../../types';
import styles from './BookmarkItem.module.css';

interface BookmarkItemProps {
    bookmark: Bookmark;
    onLoad: () => void;
    onDelete: () => void;
}

const BookmarkItem: React.FC<BookmarkItemProps> = ({ bookmark, onLoad, onDelete }) => {
    const { filters, timestamp, name } = bookmark;
    const dateStr = new Date(timestamp).toLocaleString();

    // Summary data
    const factionCount = filters.selectedFactions.length;
    const turnRangeStr = `T${filters.turnRange.min}-${filters.turnRange.max}`;
    const metricsCount = Object.values(filters.visibleMetrics).filter(Boolean).length;

    return (
        <div className={styles.item}>
            <div className={styles.info}>
                <div className={styles.topLine}>
                    <span className={styles.name}>{name}</span>
                    <span className={styles.timestamp}>{dateStr}</span>
                </div>
                <div className={styles.summary}>
                    <span className={styles.badge}>{factionCount} Factions</span>
                    <span className={styles.badge}>{turnRangeStr}</span>
                    <span className={styles.badge}>{metricsCount} Metrics</span>
                </div>
            </div>
            <div className={styles.actions}>
                <button className={styles.loadBtn} onClick={onLoad}>Load</button>
                <button className={styles.deleteBtn} onClick={onDelete} title="Delete Bookmark">
                    &times;
                </button>
            </div>
        </div>
    );
};

export default BookmarkItem;
