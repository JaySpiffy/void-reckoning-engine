import React from 'react';
import styles from './TimelineControls.module.css';
import { useDashboardStore } from '../../stores/dashboardStore';
import { useFiltersStore } from '../../stores/filtersStore';

export const TimelineControls: React.FC = () => {
    const { currentTurn, maxTurn } = useDashboardStore();
    const { liveMode, setLiveMode, turnRange, setTurnRange } = useFiltersStore();

    const handleToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
        setLiveMode(!e.target.checked);
    };

    const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = parseInt(e.target.value, 10);
        setTurnRange(val, maxTurn);
    };

    return (
        <div className={styles.timelineControls}>
            <div className={`${styles.modeLabel} ${liveMode ? styles.modeLive : styles.modeHist}`}>
                {liveMode ? '● LIVE' : '● HISTORICAL'}
            </div>

            <label className={styles.switch}>
                <input
                    type="checkbox"
                    checked={!liveMode}
                    onChange={handleToggle}
                />
                <span className={styles.toggleSlider}></span>
            </label>

            <input
                type="range"
                id="turn-slider"
                className={styles.turnSlider}
                min={0}
                max={maxTurn}
                value={liveMode ? maxTurn : turnRange.min}
                disabled={liveMode}
                onChange={handleSliderChange}
            />
        </div>
    );
};
