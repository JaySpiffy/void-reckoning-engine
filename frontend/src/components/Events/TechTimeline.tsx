import React from 'react';
import { useTechEvents } from '../../stores/eventsStore';
import TechTimelineItem from './TechTimelineItem';
import styles from './TechTimeline.module.css';

const TechTimeline: React.FC = () => {
    const techEvents = useTechEvents();

    if (techEvents.length === 0) {
        return (
            <div className={styles.empty}>
                No technologies researched yet.
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.timeline}>
                {techEvents.slice(0, 20).map((event, idx) => (
                    <TechTimelineItem
                        key={`${event.timestamp}-${idx}`}
                        event={event as any}
                        isLast={idx === techEvents.length - 1 || idx === 19}
                    />
                ))}
            </div>
        </div>
    );
};

export default TechTimeline;
