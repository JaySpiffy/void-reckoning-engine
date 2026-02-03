import React from 'react';
import styles from './Timeline.module.css';

interface ResearchTimelineProps {
    events: any[]; // Data shape TBD, using placeholder
}

export const ResearchTimeline: React.FC<ResearchTimelineProps> = ({ events }) => {
    return (
        <div className={styles.timelineContainer}>
            <h3 className={styles.timelineTitle}>Research Timeline</h3>
            <div className={styles.eventList}>
                {events.length === 0 ? (
                    <div className={styles.emptyState}>No recent technological breakthroughs.</div>
                ) : (
                    events.map((event, i) => (
                        <div key={i} className={styles.eventItem}>
                            <span className={styles.eventTurn}>T-{event.turn || '??'}</span>
                            <span className={styles.eventFaction} data-faction={event.faction}>{event.faction}</span>
                            <span className={styles.eventAction}>
                                unlocked <strong>{event.tech || event.technology}</strong>
                            </span>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
