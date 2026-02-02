import React, { useRef } from 'react';
import { Card } from '../Layout/Card';
import { GalaxyMap } from './GalaxyMap';
import { GalaxyControls } from './GalaxyControls';
import { useGalaxyData } from '../../hooks/useGalaxyData';
import { GalaxyPanelProps } from '../../types/components';
import { useGalaxyStore } from '../../stores/galaxyStore';
import styles from './GalaxyPanel.module.css';

export const GalaxyPanel: React.FC<GalaxyPanelProps> = ({ className, style }) => {
    const { loading, error, refetch } = useGalaxyData();
    const { bounds, systems, updateTransform } = useGalaxyStore();

    // Auto-fit helper for controls
    const handleReset = () => {
        if (!bounds || systems.length === 0) return;

        // This logic is slightly duplicated from GalaxyMap, 
        // but we need it here to trigger the transform update in store.
        // GalaxyMap handles the actual auto-fit on load, but manual reset needs this.
        const container = document.querySelector(`.${styles.mapWrapper}`);
        if (!container) return;

        const { width, height } = container.getBoundingClientRect();
        const padding = 0.1;

        const scaleX = (width * (1 - padding * 2)) / bounds.width;
        const scaleY = (height * (1 - padding * 2)) / bounds.height;
        const scale = Math.min(scaleX, scaleY, 3.0);

        const offsetX = -bounds.min_x * scale + (width - bounds.width * scale) / 2;
        const offsetY = -bounds.min_y * scale + (height - bounds.height * scale) / 2;

        updateTransform({ scale, x: offsetX, y: offsetY });
    };

    return (
        <Card
            title="Strategic Galaxy View"
            className={`${styles.panelCard} ${className || ''}`}
            style={style}
            loading={loading}
            headerActions={
                <button
                    onClick={() => refetch()}
                    className={styles.refreshBtn}
                    title="Refresh Map Data"
                >
                    ↻
                </button>
            }
        >
            {error ? (
                <div className={styles.errorState}>
                    <p>{error}</p>
                    <button onClick={() => refetch()}>Retry Loading Map</button>
                </div>
            ) : (
                <div className={styles.mapWrapper}>
                    <GalaxyMap onSystemClick={(name) => console.log('System clicked:', name)} />
                    <GalaxyControls onReset={handleReset} />
                </div>
            )}
        </Card>
    );
};
