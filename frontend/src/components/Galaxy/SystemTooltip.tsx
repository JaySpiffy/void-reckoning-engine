import React from 'react';
import { GalaxySystem } from '../../types';
import { getFactionColor } from '../../utils/factionColors';
import styles from './SystemTooltip.module.css';

interface SystemTooltipProps {
    system: GalaxySystem | null;
    position: { x: number; y: number } | null;
}

export const SystemTooltip: React.FC<SystemTooltipProps> = ({ system, position }) => {
    if (!system || !position) return null;

    const controlEntries = Object.entries(system.control)
        .sort((a, b) => b[1] - a[1]);

    return (
        <div
            className={styles.tooltip}
            style={{
                left: position.x + 15,
                top: position.y + 15
            }}
        >
            <div className={styles.header}>
                <div
                    className={styles.indicator}
                    style={{ backgroundColor: getFactionColor(system.owner) }}
                />
                <span className={styles.name}>{system.name}</span>
            </div>

            <div className={styles.body}>
                <div className={styles.row}>
                    <span className={styles.label}>Owner:</span>
                    <span className={styles.value}>{system.owner || 'Neutral'}</span>
                </div>
                <div className={styles.row}>
                    <span className={styles.label}>Planets:</span>
                    <span className={styles.value}>{system.total_planets}</span>
                </div>
                <div className={styles.row}>
                    <span className={styles.label}>Strategic Value:</span>
                    <span className={styles.value}>{system.node_count}</span>
                </div>

                {controlEntries.length > 0 && (
                    <div className={styles.controlSection}>
                        <div className={styles.controlTitle}>Control Breakdown</div>
                        {controlEntries.map(([faction, count]) => (
                            <div key={faction} className={styles.controlRow}>
                                <div
                                    className={styles.miniIndicator}
                                    style={{ backgroundColor: getFactionColor(faction) }}
                                />
                                <span className={styles.factionName}>{faction}</span>
                                <span className={styles.factionCount}>{count}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
