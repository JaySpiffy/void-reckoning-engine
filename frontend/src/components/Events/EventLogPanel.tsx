import React from 'react';
import { Card } from '../Layout';
import { useEventsStore, useFilteredEvents } from '../../stores/eventsStore';
import { exportEventsAsJSON, exportEventsAsCSV } from '../../utils/eventExport';
import styles from './EventLogPanel.module.css';
import EventLog from './EventLog';
import EventFilters from './EventFilters';

const EventLogPanel: React.FC = () => {
    const { searchQuery, setSearchQuery } = useEventsStore();
    const filteredEvents = useFilteredEvents();

    const handleJSONExport = () => exportEventsAsJSON(filteredEvents);
    const handleCSVExport = () => exportEventsAsCSV(filteredEvents);

    return (
        <Card
            title="Live Telemetry"
            headerActions={<EventFilters />}
        >
            <div className={styles.container}>
                <div className={styles.searchBar}>
                    <input
                        type="text"
                        placeholder="Search events..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className={styles.searchInput}
                    />
                </div>

                <div className={styles.logWrapper}>
                    <EventLog />
                </div>

                <div className={styles.footer}>
                    <span className={styles.count}>{filteredEvents.length} Recent Events</span>
                    <div className={styles.exportGroup}>
                        <button onClick={handleJSONExport} className={styles.exportBtn}>JSON</button>
                        <button onClick={handleCSVExport} className={styles.exportBtn}>CSV</button>
                    </div>
                </div>
            </div>
        </Card>
    );
};

export default EventLogPanel;
