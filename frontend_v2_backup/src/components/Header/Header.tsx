import React, { useEffect, useState } from 'react';
import styles from './Header.module.css';
import { useDashboardStore } from '../../stores/dashboardStore';
import { ConnectionStatus } from './ConnectionStatus';
import { TimelineControls } from './TimelineControls';
import { TurnDisplay } from './TurnDisplay';
import { RefreshButton } from './RefreshButton';
import { ExportModal } from '../Export';
import { BookmarkManager } from '../Bookmarks';
import HealthStatus from '../Diagnostics/HealthStatus';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { controlApi } from '../../api/client';

export const Header: React.FC = () => {
    const { universe, runId } = useDashboardStore();
    const [exportOpen, setExportOpen] = React.useState(false);
    const [bookmarksOpen, setBookmarksOpen] = React.useState(false);

    useKeyboardShortcuts({
        onExport: () => setExportOpen(true),
        onBookmarks: () => setBookmarksOpen(true),
    });

    return (
        <header className={styles.header}>
            <div className={styles.titleSection}>
                <h1>CAMPAIGN<span>COMMAND</span></h1>
                <div className={styles.subtitle}>
                    {universe} // {runId}
                </div>

                <div className={styles.subtitle}>
                    {universe} // {runId}
                </div>
            </div>

            <div className={styles.statusSection}>
                <TimelineControls />
                <TurnDisplay />
                <div className={styles.divider} />
                <button
                    className={styles.toolbarBtn}
                    onClick={() => setExportOpen(true)}
                    title="Export Data"
                >
                    EXPORT
                </button>
                <button
                    className={styles.toolbarBtn}
                    onClick={() => setBookmarksOpen(true)}
                    title="Bookmark Manager"
                >
                    BOOKMARKS
                </button>
                <div className={styles.divider} />
                <HealthStatus />
                <ConnectionStatus />
                <RefreshButton />

                <ExportModal isOpen={exportOpen} onClose={() => setExportOpen(false)} />
                <BookmarkManager isOpen={bookmarksOpen} onClose={() => setBookmarksOpen(false)} />
            </div>
        </header>
    );
};
