import React from 'react';
import { GridColumn } from './GridColumn';
import { ForceCompositionChart, ProductionChart, QueueEfficiencyChart } from '../Charts';
import { EventLogPanel, TechTimelinePanel } from '../Events';
import { PanelErrorBoundary } from '../Common/PanelErrorBoundary';

export const RightColumn: React.FC = () => (
    <GridColumn position="right">
        <PanelErrorBoundary title="Live Telemetry">
            <EventLogPanel />
        </PanelErrorBoundary>

        <PanelErrorBoundary title="Technology Feed">
            <TechTimelinePanel />
        </PanelErrorBoundary>

        <ForceCompositionChart />
        <ProductionChart />
        <QueueEfficiencyChart />
    </GridColumn>
);

export default RightColumn;
