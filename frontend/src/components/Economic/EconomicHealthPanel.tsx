import React, { useMemo, useState } from 'react';
import { ChartContainer, LineChart, PieChart, BarChart } from '../Charts';
import { useNetProfit, useRevenueBreakdown, useStockpileVelocity, useResourceROI } from '../../hooks/useEconomicData';
import { formatNumericValue } from '../../utils/chartHelpers';
import styles from './EconomicHealthPanel.module.css';

export const EconomicHealthPanel: React.FC = () => {
    const { data: profitData, loading: profitLoading } = useNetProfit();
    const { data: breakdownData, loading: breakdownLoading } = useRevenueBreakdown();
    const { data: velocityData, loading: velocityLoading } = useStockpileVelocity();
    const { data: roiData, loading: roiLoading } = useResourceROI();

    const [viewMode, setViewMode] = useState<'income' | 'expenses'>('income');

    // Debug logging
    // console.log("EconomicPanel Data:", { profitData, breakdownData, velocityData, roiData });

    // Transform profit data for LineChart
    const profitChartData = useMemo(() => {
        if (!profitData || !profitData.turns || !profitData.factions) return [];
        try {
            return profitData.turns.map((turn, i) => {
                const point: any = { x: turn };
                Object.entries(profitData.factions || {}).forEach(([faction, metrics]) => {
                    if (metrics) {
                        point[`${faction}_profit`] = metrics.net_profit?.[i] || 0;
                        point[`${faction}_income`] = metrics.gross_income?.[i] || 0;
                    }
                });
                return point;
            });
        } catch (e) {
            console.error("Error transforming profit data", e);
            return [];
        }
    }, [profitData]);

    const profitKeys = useMemo(() => {
        if (!profitData || !profitData.factions) return [];
        try {
            return Object.keys(profitData.factions).map(f => `${f}_profit`);
        } catch (e) {
            console.error("Error generating profit keys", e);
            return [];
        }
    }, [profitData]);

    // Transform breakdown data for PieChart
    const breakdownChartData = useMemo(() => {
        if (!breakdownData) return [];
        // Use empty object default to prevent "undefined" access
        const income = breakdownData.income || {};
        const expenses = breakdownData.expenses || {};

        const source = viewMode === 'income' ? income : expenses;
        if (!source) return [];

        const turns = breakdownData.turns || [];
        const latestIdx = turns.length - 1;
        if (latestIdx < 0) return [];

        try {
            return Object.entries(source).map(([cat, values]) => ({
                name: cat,
                value: values?.[latestIdx] || 0
            })).filter(d => d.value > 0);
        } catch (e) {
            console.error("Error transforming breakdown data", e);
            return [];
        }
    }, [breakdownData, viewMode]);

    // Toggle Button Component
    const toggleAction = (
        <div className={styles.toggleGroup}>
            <button
                className={`${styles.toggleBtn} ${viewMode === 'income' ? styles.active : ''}`}
                onClick={() => setViewMode('income')}
            >
                Income
            </button>
            <button
                className={`${styles.toggleBtn} ${viewMode === 'expenses' ? styles.active : ''}`}
                onClick={() => setViewMode('expenses')}
            >
                Expenses
            </button>
        </div>
    );

    // Custom coloring for expenses (Red/Orange theme) vs Income (Green/Blue/Default)
    const pieColors = viewMode === 'expenses'
        ? ['#ef4444', '#f97316', '#dc2626', '#c2410c', '#b91c1c']
        : undefined; // Default theme for income

    // ... (rest of velocity/roi logic) ...

    // Transform velocity data
    const velocityChartData = useMemo(() => {
        if (!velocityData || !velocityData.turns || !velocityData.factions) return [];
        try {
            return velocityData.turns.map((turn, i) => {
                const point: any = { x: turn };
                Object.entries(velocityData.factions || {}).forEach(([faction, metrics]) => {
                    if (metrics) {
                        point[`${faction}_stockpile`] = metrics.stockpile?.[i] || 0;
                        point[`${faction}_velocity`] = metrics.velocity?.[i] || 0;
                    }
                });
                return point;
            });
        } catch (e) { return []; }
    }, [velocityData]);

    const velocityKeys = useMemo(() => {
        if (!velocityData || !velocityData.factions) return [];
        try {
            const keys: string[] = [];
            Object.keys(velocityData.factions).forEach(f => {
                keys.push(`${f}_stockpile`);
                keys.push(`${f}_velocity`);
            });
            return keys;
        } catch (e) {
            console.error("Error generating velocity keys", e);
            return [];
        }
    }, [velocityData]);

    // Transform ROI data
    const roiChartData = useMemo(() => {
        if (!roiData || !roiData.roi_data) return [];
        try {
            return roiData.roi_data.map(item => ({
                name: item.faction || item.category,
                roi: item.roi || item.amount
            }));
        } catch (e) { return []; }
    }, [roiData]);

    return (
        <div className={styles.panelContainer}>
            <div className={styles.panelHeader}>
                <h2 className={styles.panelTitle}>Economic Health Analysis</h2>
            </div>

            <div className={styles.performanceGrid}>
                <ChartContainer title="Net Profit Trajectory" loading={profitLoading} isEmpty={profitChartData.length === 0}>
                    <LineChart
                        data={profitChartData}
                        dataKeys={profitKeys}
                        valueFormatter={formatNumericValue}
                        yAxisLabel="Credits"
                    />
                </ChartContainer>

                <ChartContainer
                    title={viewMode === 'income' ? "Revenue Sources" : "Expense Breakdown"}
                    action={toggleAction}
                    loading={breakdownLoading}
                    isEmpty={breakdownChartData.length === 0}
                >
                    <PieChart data={breakdownChartData} colors={pieColors} />
                </ChartContainer>

                <ChartContainer title="Stockpile Velocity" loading={velocityLoading} isEmpty={velocityChartData.length === 0}>
                    <LineChart
                        data={velocityChartData}
                        dataKeys={velocityKeys}
                        valueFormatter={formatNumericValue}
                        yAxisLabel="Resources"
                    />
                </ChartContainer>

                <ChartContainer title="Resource ROI" loading={roiLoading} isEmpty={roiChartData.length === 0}>
                    <BarChart
                        data={roiChartData}
                        dataKeys={['roi']}
                        xAxisKey="name"
                    />
                </ChartContainer>
            </div>
        </div>
    );
};
