import React from 'react';
import styles from './MetricCard.module.css';

export const MetricCardSkeleton: React.FC = () => {
    return (
        <div className={styles.card}>
            <div className={`${styles.skeletonLabel} skeleton`} />
            <div className={`${styles.skeletonValue} skeleton`} />
        </div>
    );
};
