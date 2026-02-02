import React from 'react';
import { useGalaxyStore } from '../../stores/galaxyStore';
import { GalaxyControlsProps } from '../../types/components';
import { FACTION_COLORS, getFactionColor } from '../../utils/factionColors';
import styles from './GalaxyControls.module.css';

export const GalaxyControls: React.FC<GalaxyControlsProps> = ({ className, onReset }) => {
    const { transform, updateTransform, systems } = useGalaxyStore();

    // Derive active factions from systems
    const activeFactions = React.useMemo(() => {
        const owners = new Set<string>();
        systems.forEach(sys => {
            if (sys.owner && sys.owner !== 'Unexplored') {
                owners.add(sys.owner);
            }
        });
        return Array.from(owners).sort();
    }, [systems]);

    const handleZoom = (delta: number) => {
        const newScale = Math.max(0.05, Math.min(5, transform.scale * delta));
        updateTransform({ scale: newScale });
    };

    return (
        <div className={`${styles.controlsContainer} ${className || ''}`}>
            {/* Legend */}
            {/* Legend */}
            <div className={styles.legend}>
                <div className={styles.legendTitle}>Faction Legend</div>
                {activeFactions.length > 0 ? (
                    activeFactions.map(faction => (
                        <div key={faction} className={styles.legendEntry}>
                            <div
                                className={styles.swatch}
                                style={{ backgroundColor: getFactionColor(faction) }}
                            />
                            <span>{faction}</span>
                        </div>
                    ))
                ) : (
                    <div className={styles.legendEntry}>
                        <span style={{ opacity: 0.7, fontStyle: 'italic' }}>No active data</span>
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className={styles.actions}>
                <div className={styles.zoomGroup}>
                    <button onClick={() => handleZoom(1.2)} title="Zoom In">+</button>
                    <button onClick={() => handleZoom(0.8)} title="Zoom Out">-</button>
                    <button onClick={onReset} title="Reset View">▣</button>
                </div>

                <div className={styles.stats}>
                    Scale: {Math.round(transform.scale * 100)}%
                </div>
            </div>
        </div>
    );
};
