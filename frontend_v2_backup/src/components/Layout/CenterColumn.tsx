import React from 'react';
import { GridColumn } from './GridColumn';
import AlertsPanel from '../Alerts/AlertsPanel';
import { GalaxyPanel } from '../Galaxy/GalaxyPanel';
import { EconomicHealthPanel } from '../Economic/EconomicHealthPanel';
import { MilitaryAnalysisPanel } from '../Military/MilitaryAnalysisPanel';
import { DevelopmentPanel } from '../Development/DevelopmentPanel';
import { PanelErrorBoundary } from '../Common/PanelErrorBoundary';

export const CenterColumn: React.FC = () => (
    <GridColumn position="center">
        <PanelErrorBoundary title="Anomalies & Alerts">
            <AlertsPanel />
        </PanelErrorBoundary>

        <PanelErrorBoundary title="Galaxy Map">
            <GalaxyPanel style={{ minHeight: '400px', marginBottom: '1.5rem' }} />
        </PanelErrorBoundary>

        <PanelErrorBoundary title="Economic Health">
            <EconomicHealthPanel />
        </PanelErrorBoundary>

        <PanelErrorBoundary title="Military Analysis">
            <MilitaryAnalysisPanel />
        </PanelErrorBoundary>

        <PanelErrorBoundary title="Development Pulse">
            <DevelopmentPanel />
        </PanelErrorBoundary>
    </GridColumn>
);

export default CenterColumn;
