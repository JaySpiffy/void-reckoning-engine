import React, { useState, useEffect, useCallback } from 'react';
import styles from './SimulationControls.module.css';
import { controlApi } from '../../api/client';
import { useDashboardStore } from '../../stores/dashboardStore';

export const SimulationControls: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const paused = useDashboardStore((s) => s.paused);
    const setPaused = useDashboardStore((s) => s.setPaused);

    const fetchStatus = useCallback(async () => {
        try {
            const { data } = await controlApi.getStatus();
            setPaused(data.paused);
        } catch (err) {
            console.error('Failed to fetch simulation status:', err);
        }
    }, [setPaused]);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 2000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    const handleTogglePause = async () => {
        setLoading(true);
        try {
            if (paused) {
                await controlApi.resume();
                setPaused(false);
            } else {
                await controlApi.pause();
                setPaused(true);
            }
        } catch (err) {
            console.error('Failed to toggle simulation pause:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleStep = async () => {
        setLoading(true);
        try {
            await controlApi.step();
        } catch (err) {
            console.error('Failed to trigger simulation step:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.btnGroup}>
            <button
                className={`${styles.btnAccent} ${paused ? styles.paused : ''}`}
                onClick={handleTogglePause}
                disabled={loading}
            >
                {loading ? (
                    <div className="spinner-small"></div>
                ) : (
                    paused ? '▶ RESUME' : '❚❚ PAUSE'
                )}
            </button>

            <button
                className={styles.btnOutline}
                onClick={handleStep}
                disabled={!paused || loading}
                title={!paused ? "Pause simulation to step through turns" : "Step 1 turn forward"}
            >
                STEP ➜
            </button>
        </div>
    );
};

export default SimulationControls;
