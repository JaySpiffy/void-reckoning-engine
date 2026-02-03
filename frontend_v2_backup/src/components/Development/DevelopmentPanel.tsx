import React, { useMemo } from 'react';
import { ChartContainer, LineChart, BarChart } from '../Charts';
import { useIndustrialDensity, useQueueEfficiency, useConstructionTimeline, useTechProgress, useResearchTimeline } from '../../hooks/useIndustrialData';
import { formatPercentage } from '../../utils/chartHelpers';
import { ConstructionTimeline } from './ConstructionTimeline';
import { ResearchTimeline } from './ResearchTimeline';
import styles from './DevelopmentPanel.module.css';

export const DevelopmentPanel: React.FC = () => {
    const { data: densityData, loading: densityLoading } = useIndustrialDensity();
    const { data: efficiencyData, loading: efficiencyLoading } = useQueueEfficiency();
    const { data: timelineData, loading: timelineLoading } = useConstructionTimeline();
    const { data: techData, loading: techLoading } = useTechProgress();
    const { data: researchTimelineData, loading: researchTimelineLoading } = useResearchTimeline();

    // Transform Industrial Density data
    const densityChartData = useMemo(() => {
        if (!densityData) return [];
        // Picking the first faction or logic TBD
        const firstFaction = Object.values(densityData.factions)[0];
        if (!firstFaction) return [];
        return Object.entries(firstFaction.building_counts).map(([type, count]) => ({
            type,
            count
        }));
    }, [densityData]);

    // Transform Queue Efficiency data
    const efficiencyChartData = useMemo(() => {
        if (!efficiencyData) return [];
        return efficiencyData.turns.map((turn, i) => ({
            x: turn,
            efficiency: efficiencyData.efficiency[i],
            idle: efficiencyData.idle_slots[i]
        }));
    }, [efficiencyData]);

    // Transform Tech Progress data
    const techChartData = useMemo(() => {
        if (!techData) return [];
        // Aggregate techs across selected factions or show comparison
        // For BarChart, let's show tiers
        const tiers: Record<string, number> = {};
        Object.values(techData.factions).forEach(f => {
            const techs = f.techs_by_tier || {};
            Object.entries(techs).forEach(([tier, count]) => {
                tiers[tier] = (tiers[tier] || 0) + (count as number);
            });
        });
        return Object.entries(tiers).map(([tier, count]) => ({
            tier: `Tier ${tier}`,
            count
        }));
    }, [techData]);

    return (
        <div className={styles.panelContainer}>
            <div className={styles.panelHeader}>
                <h2 className={styles.panelTitle}>Development Pulse Analysis</h2>
            </div>

            <div className={styles.performanceGrid}>
                <ChartContainer
                    title="Industrial Asset Density"
                    loading={densityLoading}
                    isEmpty={densityChartData.length === 0}
                >
                    <BarChart
                        data={densityChartData}
                        dataKeys={['count']}
                        xAxisKey="type"
                    />
                </ChartContainer>

                <ChartContainer
                    title="Queue Efficiency & Load"
                    loading={efficiencyLoading}
                    isEmpty={efficiencyChartData.length === 0}
                >
                    <LineChart
                        data={efficiencyChartData}
                        dataKeys={['efficiency', 'idle']}
                        valueFormatter={formatPercentage}
                        yAxisLabel="%"
                    />
                </ChartContainer>

                <ChartContainer
                    title="Technological Advancement"
                    loading={techLoading}
                    isEmpty={techChartData.length === 0}
                >
                    <BarChart
                        data={techChartData}
                        dataKeys={['count']}
                        xAxisKey="tier"
                    />
                </ChartContainer>
            </div>

            <div className={styles.timelineSection}>
                <div className={styles.timelineGrid}>
                    <ConstructionTimeline events={timelineData?.events || []} />
                    <ResearchTimeline events={researchTimelineData?.events || []} />
                </div>
            </div>
        </div>
    );
};
