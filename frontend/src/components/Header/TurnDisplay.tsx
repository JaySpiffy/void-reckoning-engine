import React, { useEffect, useState } from 'react';
import styles from './TurnDisplay.module.css';
import { useDashboardStore } from '../../stores/dashboardStore';

export const TurnDisplay: React.FC = () => {
    const currentTurn = useDashboardStore((s) => s.currentTurn);
    const maxTurn = useDashboardStore((s) => s.maxTurn);
    const [isPulsing, setIsPulsing] = useState(false);

    useEffect(() => {
        if (currentTurn > 0) {
            setIsPulsing(true);
            const timer = setTimeout(() => setIsPulsing(false), 400);
            return () => clearTimeout(timer);
        }
    }, [currentTurn]);

    return (
        <div className={`${styles.turnDisplay} ${isPulsing ? styles.pulse : ''}`}>
            <span className={styles.label}>TURN ARCHIVE</span>
            <div className={styles.value}>
                {currentTurn === 0 ? '--' : currentTurn}
                {maxTurn > 0 && <span className={styles.maxTurn}> / {maxTurn}</span>}
            </div>
        </div>
    );
};
