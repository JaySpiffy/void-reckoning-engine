import React from 'react';
import { useEventsStore } from '../../stores/eventsStore';
import styles from './EventFilters.module.css';

const EventFilters: React.FC = () => {
    const {
        eventTypeFilter,
        setEventTypeFilter,
        autoScroll,
        toggleAutoScroll,
        clearEvents
    } = useEventsStore();

    const categories = [
        { id: 'combat', label: 'Combat' },
        { id: 'economy', label: 'Economy' },
        { id: 'technology', label: 'Technology' },
        { id: 'construction', label: 'Construction' },
        { id: 'system', label: 'System' },
        { id: 'diplomacy', label: 'Diplomacy' },
        { id: 'movement', label: 'Movement' },
        { id: 'campaign', label: 'Campaign' },
        { id: 'strategy', label: 'Strategy' },
        { id: 'doctrine', label: 'Doctrine' }
    ];

    const handleToggleType = (type: string) => {
        if (eventTypeFilter.includes(type)) {
            setEventTypeFilter(eventTypeFilter.filter(t => t !== type));
        } else {
            setEventTypeFilter([...eventTypeFilter, type]);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.typeGroup}>
                {categories.map(cat => (
                    <button
                        key={cat.id}
                        className={`${styles.filterBtn} ${eventTypeFilter.includes(cat.id) ? styles.active : ''}`}
                        onClick={() => handleToggleType(cat.id)}
                    >
                        {cat.label}
                    </button>
                ))}
            </div>

            <div className={styles.actions}>
                <button
                    className={`${styles.actionBtn} ${autoScroll ? styles.active : ''}`}
                    onClick={toggleAutoScroll}
                    title="Toggle Auto-Scroll"
                >
                    {autoScroll ? 'AUTO' : 'MANUAL'}
                </button>
                <button
                    className={styles.clearBtn}
                    onClick={clearEvents}
                    title="Clear Log"
                >
                    CLR
                </button>
            </div>
        </div>
    );
};

export default EventFilters;
