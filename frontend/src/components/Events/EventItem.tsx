import React, { useState } from 'react';
import { TelemetryEvent } from '../../types';
import { formatEventMessage, formatEventTime } from '../../utils/eventFormatters';
import { getFactionColor } from '../../utils/factionColors';
import EventIcon from './EventIcon';
import styles from './EventItem.module.css';

interface EventItemProps {
    event: TelemetryEvent;
}

const EventItem: React.FC<EventItemProps> = ({ event }) => {
    const [expanded, setExpanded] = useState(false);

    const message = formatEventMessage(event);
    const time = formatEventTime(event.timestamp, event.turn);
    const factionColor = getFactionColor(event.faction);

    return (
        <div className={styles.container}>
            <div
                className={styles.mainRow}
                onClick={() => setExpanded(!expanded)}
            >
                <EventIcon
                    eventType={event.event_type}
                    category={event.category}
                    size="small"
                    timestamp={event.timestamp}
                />

                <div className={styles.content}>
                    <div className={styles.header}>
                        {event.faction && (
                            <span
                                className={styles.factionBadge}
                                style={{ backgroundColor: `${factionColor}33`, color: factionColor, borderColor: `${factionColor}66` }}
                            >
                                {event.faction.toUpperCase()}
                            </span>
                        )}
                        <span className={styles.time}>{time}</span>
                    </div>
                    <div className={styles.message}>{message}</div>
                </div>

                <div className={`${styles.chevron} ${expanded ? styles.expanded : ''}`}>
                    ▼
                </div>
            </div>

            {expanded && (
                <div className={styles.details}>
                    <pre className={styles.json}>
                        {JSON.stringify(event.data, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
};

export default EventItem;
