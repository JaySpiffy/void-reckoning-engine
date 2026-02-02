import React, { useMemo } from 'react';
import { ChartContainer, LineChart, PieChart, RadarChart, ScatterChart } from '../Charts';
import { useCombatEffectiveness, useForceComposition, useAttritionRate, useBattleHeatmap, useFleetPower } from '../../hooks/useMilitaryData';
import { formatPercentage } from '../../utils/chartHelpers';
import styles from './MilitaryAnalysisPanel.module.css';

export const MilitaryAnalysisPanel: React.FC = () => {
    const { data: effectivenessData, loading: effectivenessLoading } = useCombatEffectiveness();
    const { data: compositionData, loading: compositionLoading } = useForceComposition();
    const { data: attritionData, loading: attritionLoading } = useAttritionRate();
    const { data: heatmapData, loading: heatmapLoading } = useBattleHeatmap();
    const { data: fleetPowerData, loading: fleetPowerLoading } = useFleetPower();

    // Combat Effectiveness Data Transformation
    const effectivenessChartData = useMemo(() => {
        if (!effectivenessData) return [];

        // Check if it's time-series (single faction) or multi-faction (radar-ready)
        if ('turns' in effectivenessData && effectivenessData.turns) {
            return effectivenessData.turns.map((turn, i) => ({
                x: turn,
                value: effectivenessData.values[i]
            }));
        } else if ('factions' in effectivenessData && effectivenessData.factions) {
            // Radar transformation: we might need multiple metrics for a true radar, 
            // but for now mapping factions to metrics
            return Object.entries(effectivenessData.factions).map(([faction, stats]) => ({
                metric: faction,
                value: stats.cer * 100 // Scale for radar
            }));
        }
        return [];
    }, [effectivenessData]);

    // Force Composition Data
    const compositionChartData = useMemo(() => {
        if (!compositionData || !compositionData.composition) return [];
        return Object.entries(compositionData.composition).map(([type, count]) => ({
            name: type,
            value: count
        }));
    }, [compositionData]);

    // Attrition Rate Transformation
    const attritionChartData = useMemo(() => {
        if (!attritionData || !attritionData.factions) return [];
        const turns = attritionData.factions[Object.keys(attritionData.factions)[0]]?.turns || [];
        return turns.map((turn, i) => {
            const point: any = { x: turn };
            Object.entries(attritionData.factions).forEach(([faction, metrics]) => {
                point[faction] = metrics.attrition[i];
            });
            return point;
        });
    }, [attritionData]);

    const attritionKeys = useMemo(() => {
        if (!attritionData || !attritionData.factions) return [];
        return Object.keys(attritionData.factions);
    }, [attritionData]);

    // Fleet Power Transformation
    const fleetPowerChartData = useMemo(() => {
        if (!fleetPowerData || !fleetPowerData.factions) return [];
        const turns = fleetPowerData.factions[Object.keys(fleetPowerData.factions)[0]]?.turns || [];
        return turns.map((turn, i) => {
            const point: any = { x: turn };
            Object.entries(fleetPowerData.factions).forEach(([faction, metrics]) => {
                point[faction] = metrics.power[i];
            });
            return point;
        });
    }, [fleetPowerData]);

    const fleetPowerKeys = useMemo(() => {
        if (!fleetPowerData || !fleetPowerData.factions) return [];
        return Object.keys(fleetPowerData.factions);
    }, [fleetPowerData]);

    // Heatmap Transformation
    const heatmapChartData = useMemo(() => {
        if (!heatmapData || !heatmapData.heatmap) return [];
        return heatmapData.heatmap.map(entry => ({
            x: entry.system,
            y: entry.cer,
            z: entry.battle_count,
            faction: entry.faction,
            name: `${entry.faction} @ ${entry.system}`
        }));
    }, [heatmapData]);

    return (
        <div className={styles.panelContainer}>
            <div className={styles.panelHeader}>
                <h2 className={styles.panelTitle}>Military Performance Analysis</h2>
            </div>

            <div className={styles.performanceGrid}>
                <ChartContainer
                    title="Combat Effectiveness (CER)"
                    loading={effectivenessLoading}
                    isEmpty={!effectivenessData}
                >
                    {effectivenessData && 'turns' in effectivenessData ? (
                        <LineChart data={effectivenessChartData} dataKeys={['value']} yAxisLabel="CER" />
                    ) : (
                        <RadarChart data={effectivenessChartData} dataKeys={['value']} angleKey="metric" />
                    )}
                </ChartContainer>

                <ChartContainer
                    title="Force Composition"
                    loading={compositionLoading}
                    isEmpty={compositionChartData.length === 0}
                >
                    <PieChart data={compositionChartData} />
                </ChartContainer>

                <ChartContainer
                    title="Attrition Rate History"
                    loading={attritionLoading}
                    isEmpty={attritionChartData.length === 0}
                >
                    <LineChart
                        data={attritionChartData}
                        dataKeys={attritionKeys}
                        valueFormatter={formatPercentage}
                        yAxisLabel="Loss %"
                    />
                </ChartContainer>

                <ChartContainer
                    title="Fleet Power Projection"
                    loading={fleetPowerLoading}
                    isEmpty={fleetPowerChartData.length === 0}
                >
                    <LineChart
                        data={fleetPowerChartData}
                        dataKeys={fleetPowerKeys}
                        yAxisLabel="Power Index"
                    />
                </ChartContainer>

                <ChartContainer
                    title="Tactical Heatmap"
                    loading={heatmapLoading}
                    isEmpty={heatmapChartData.length === 0}
                >
                    <ScatterChart
                        data={heatmapChartData}
                        xKey="x"
                        yKey="y"
                        zKey="z"
                        colorKey="faction"
                    />
                </ChartContainer>
            </div>
        </div>
    );
};
