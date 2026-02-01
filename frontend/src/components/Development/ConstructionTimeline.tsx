import React from 'react';
import { ConstructionEvent } from '../../types';
import styles from './Timeline.module.css';

interface ConstructionTimelineProps {
    events: ConstructionEvent[];
}

export const ConstructionTimeline: React.FC<ConstructionTimelineProps> = ({ events }) => {
    return (
        <div className={styles.timelineContainer}>
            <h3 className={styles.timelineTitle}>Construction Timeline</h3>
            <div className={styles.eventList}>
                {events.length === 0 ? (
                    <div className={styles.emptyState}>No recent construction events.</div>
                ) : (
                    events.map((event, i) => (
                        <div key={`${event.turn}-${i}`} className={styles.eventItem}>
                            <span className={styles.eventTurn}>T-{event.turn}</span>
                            <span className={styles.eventFaction} data-faction={event.faction}>{event.faction}</span>
                            <span className={styles.eventAction}>
                                built <strong>{event.building}</strong> on <em>{event.planet}</em>
                            </span>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
