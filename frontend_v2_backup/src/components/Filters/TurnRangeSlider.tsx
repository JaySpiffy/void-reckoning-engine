import React, { useState, useEffect, useCallback } from 'react';
import styles from './TurnRangeSlider.module.css';
import { useFiltersStore } from '../../stores/filtersStore';
import { useDashboardStore } from '../../stores/dashboardStore';
import { getMaxTurn } from '../../api/client';

export const TurnRangeSlider: React.FC = () => {
    const { currentTurn, maxTurn, setMaxTurn } = useDashboardStore();
    const { turnRange, setTurnRange, liveMode } = useFiltersStore();

    const [localMin, setLocalMin] = useState(turnRange.min);
    const [localMax, setLocalMax] = useState(turnRange.max);
    const [fetching, setFetching] = useState(maxTurn === 0);

    // Discovery: Fetch max turn on mount if not available
    useEffect(() => {
        const discoverMaxTurn = async () => {
            if (maxTurn === 0) {
                try {
                    const { data } = await getMaxTurn();
                    if (data.max_turn > 0) {
                        setMaxTurn(data.max_turn);
                        if (turnRange.max === 0) {
                            setTurnRange(1, data.max_turn);
                        }
                    }
                } catch (err) {
                    console.error('Failed to discover max turn:', err);
                } finally {
                    setFetching(false);
                }
            }
        };
        discoverMaxTurn();
    }, [maxTurn, setMaxTurn, setTurnRange, turnRange.max]);

    // Sync with store when store changes (e.g. status update)
    useEffect(() => {
        if (liveMode) {
            setLocalMin(1);
            setLocalMax(maxTurn || 1);
        } else {
            setLocalMin(turnRange.min || 1);
            setLocalMax(turnRange.max || maxTurn || 1);
        }
    }, [turnRange.min, turnRange.max, maxTurn, liveMode]);

    const handleMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = parseInt(e.target.value, 10) || 1;
        setLocalMin(val);
    };

    const handleMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = parseInt(e.target.value, 10) || 1;
        setLocalMax(val);
    };

    const syncStore = useCallback(() => {
        let finalMin = Math.max(1, localMin);
        let finalMax = Math.min(maxTurn, localMax);

        if (finalMin > finalMax) finalMin = finalMax;

        setTurnRange(finalMin, finalMax);
    }, [localMin, localMax, maxTurn, setTurnRange]);

    // Debounced update to store
    useEffect(() => {
        const timer = setTimeout(syncStore, 500);
        return () => clearTimeout(timer);
    }, [syncStore]);

    const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = parseInt(e.target.value, 10);
        setLocalMax(val);
    };

    if (fetching) {
        return <div className={styles.rangeSliderContainer} style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>SCANNING TEMPORAL ARCHIVES...</div>;
    }

    if (maxTurn === 0) {
        return <div className={styles.rangeSliderContainer} style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>NO ARCHIVES FOUND (TURN 0)</div>;
    }

    return (
        <div className={styles.rangeSliderContainer}>
            <div className={styles.rangeInputs}>
                <input
                    type="number"
                    value={localMin}
                    onChange={handleMinChange}
                    min={1}
                    max={maxTurn}
                    disabled={liveMode}
                />
                <span>TO</span>
                <input
                    type="number"
                    value={localMax}
                    onChange={handleMaxChange}
                    min={1}
                    max={maxTurn}
                    disabled={liveMode}
                />
            </div>

            <div className={styles.sliderWrapper}>
                <input
                    type="range"
                    className={styles.slider}
                    min={1}
                    max={maxTurn || 1}
                    value={localMax}
                    onChange={handleSliderChange}
                    disabled={liveMode}
                />
            </div>
        </div>
    );
};

export default TurnRangeSlider;
