import React, { useEffect, useRef } from 'react';
import { useEventsStore, usePaginatedEvents } from '../../stores/eventsStore';
import EventItem from './EventItem';
import styles from './EventLog.module.css';

const EventLog: React.FC = () => {
    const { events, page, totalPages, totalEvents } = usePaginatedEvents();
    const { autoScroll, setPage } = useEventsStore();
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (autoScroll && scrollRef.current) {
            scrollRef.current.scrollTop = 0;
        }
    }, [events, autoScroll]);

    if (totalEvents === 0) {
        return (
            <div className={styles.empty}>
                <div className={styles.pulseNode} />
                <span>Awaiting Telemetry Stream...</span>
            </div>
        );
    }

    return (
        <div className={styles.wrapper}>
            <div className={styles.container} ref={scrollRef}>
                {events.map((event, idx) => (
                    <EventItem
                        key={`${event.timestamp}-${event.event_type}-${idx}`}
                        event={event}
                    />
                ))}
            </div>

            {totalPages > 1 && (
                <div className={styles.pagination}>
                    <button
                        disabled={page === 1}
                        onClick={() => setPage(page - 1)}
                        className={styles.pageBtn}
                    >
                        PREV
                    </button>
                    <span className={styles.pageInfo}>
                        PAGE {page} OF {totalPages}
                    </span>
                    <button
                        disabled={page === totalPages}
                        onClick={() => setPage(page + 1)}
                        className={styles.pageBtn}
                    >
                        NEXT
                    </button>
                </div>
            )}
        </div>
    );
};

export default EventLog;
