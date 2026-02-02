import React from 'react';
import { getEventIcon } from '../../utils/eventFormatters';
import styles from './EventIcon.module.css';

interface EventIconProps {
    eventType: string;
    category: string;
    size?: 'small' | 'medium' | 'large';
    timestamp?: number;
}

const EventIcon: React.FC<EventIconProps> = ({
    eventType,
    category,
    size = 'medium',
    timestamp
}) => {
    const { icon, color } = getEventIcon(eventType, category);

    // Check if event is very recent (less than 5 seconds old)
    const isRecent = timestamp ? (Date.now() / 1000 - timestamp < 5) : false;

    return (
        <div
            className={`${styles.container} ${styles[size]} ${isRecent ? styles.pulse : ''}`}
            style={{ '--icon-color': color } as React.CSSProperties}
            title={category.toUpperCase()}
        >
            <span className={styles.icon}>{icon}</span>
        </div>
    );
};

export default EventIcon;
