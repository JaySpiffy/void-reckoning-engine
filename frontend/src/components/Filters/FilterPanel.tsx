import React, { useEffect } from 'react';
import styles from './FilterPanel.module.css';
import { FactionFilter } from './FactionFilter';
import { TurnRangeSlider } from './TurnRangeSlider';
import { MetricVisibilityToggles } from './MetricVisibilityToggles';
import { SimulationControls } from '../Controls';
import { FilterPanelProps } from '../../types/components';
import { useFiltersStore } from '../../stores/filtersStore';

import { controlApi } from '../../api/client';
import { useDashboardStore } from '../../stores/dashboardStore';

export const FilterPanel: React.FC<FilterPanelProps> = ({ factions, className }) => {
    const { setFactions, comparisonMode, setComparisonMode } = useFiltersStore();
    const { universe, runId } = useDashboardStore();
    const [runs, setRuns] = React.useState<any[]>([]);

    // Run Selector Logic
    useEffect(() => {
        const fetchRuns = async () => {
            try {
                const res = await controlApi.getRuns(universe !== 'unknown' ? universe : undefined);
                setRuns(res.data);
            } catch (err) {
                console.error("Failed to fetch runs:", err);
            }
        };
        fetchRuns();
    }, [universe]);

    const handleRunSwitch = async (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newRunId = e.target.value;
        if (!newRunId || newRunId === runId) return;
        if (confirm(`Switch to run ${newRunId}? Current view will be reset.`)) {
            try {
                await controlApi.switchRun(newRunId);
                window.location.reload();
            } catch (err) {
                alert("Failed to switch run: " + err);
            }
        }
    };

    // Initialize store with all factions if none selected
    useEffect(() => {
        if (factions.length > 0) {
            setFactions(factions);
        }
    }, [factions, setFactions]);

    return (
        <div className={`${styles.filterPanel} ${className || ''}`}>
            <div className={styles.filterRow}>
                <div className={styles.filterGroup}>
                    <label>Run Selector</label>
                    <select
                        value={runId || ""}
                        onChange={handleRunSwitch}
                        style={{
                            background: 'rgba(0,0,0,0.5)',
                            color: '#e2e8f0',
                            border: '1px solid #334155',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontFamily: 'monospace',
                            fontSize: '0.8rem',
                            outline: 'none',
                            minWidth: '200px'
                        }}
                    >
                        <option value="" disabled>Select Run...</option>
                        {runs.map(run => (
                            <option key={run.run_id} value={run.run_id}>
                                {run.run_id} (T:{run.turns_taken})
                            </option>
                        ))}
                    </select>
                </div>

                <div className={styles.filterGroup}>
                    <label>Faction Selection</label>
                    <FactionFilter factions={factions} />
                </div>

                <div className={styles.filterGroup}>
                    <label>Historical Turn Window</label>
                    <TurnRangeSlider />
                </div>

                <div className={styles.filterGroup}>
                    <label>Simulation Control</label>
                    <SimulationControls />
                </div>

                <div className={`${styles.filterGroup} ${styles.actionRow}`} style={{ marginLeft: 'auto' }}>
                    <div className={styles.toggleContainer}>
                        <span className={styles.toggleLabel}>Comparison Mode</span>
                        <label className={styles.switch}>
                            <input
                                type="checkbox"
                                checked={comparisonMode}
                                onChange={(e) => setComparisonMode(e.target.checked)}
                            />
                            <span className={styles.slider}></span>
                        </label>
                    </div>
                    <button className="btn-outline" style={{ fontSize: '0.7rem' }}>EXPORT DATA</button>
                    <button className="btn-accent" style={{ fontSize: '0.7rem' }}>APPLY FILTERS</button>
                </div>
            </div>

            <div className={styles.filterRow}>
                <div className={styles.filterGroup} style={{ width: '100%' }}>
                    <label>Visibility Toggles</label>
                    <MetricVisibilityToggles />
                </div>
            </div>
        </div>
    );
};

export default FilterPanel;
