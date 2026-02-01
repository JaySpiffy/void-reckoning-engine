import React from 'react';
import { TechUnlockEvent } from '../../types';
import { getFactionColor } from '../../utils/factionColors';
import styles from './TechTimelineItem.module.css';

interface TechTimelineItemProps {
    event: TechUnlockEvent;
    isLast?: boolean;
}

const TechTimelineItem: React.FC<TechTimelineItemProps> = ({ event, isLast }) => {
    const factionColor = getFactionColor(event.faction);
    const techName = event.data?.tech || event.data?.technology || 'Unknown Technology';
    const cost = event.data?.cost;
    const turn = event.turn !== null ? `T${event.turn}` : '';

    return (
        <div className={styles.container}>
            <div
                className={styles.marker}
                style={{ backgroundColor: factionColor, boxShadow: `0 0 8px ${factionColor}66` }}
            />

            <div className={styles.content}>
                <div className={styles.header}>
                    <span className={styles.techName}>{techName}</span>
                    <span className={styles.turnBadge}>{turn}</span>
                </div>
                <div className={styles.meta}>
                    <span style={{ color: factionColor }}>{event.faction}</span>
                    {cost && <span className={styles.cost}> • {cost}RP</span>}
                </div>
            </div>

            {!isLast && <div className={styles.connector} />}
        </div>
    );
};

export default TechTimelineItem;
