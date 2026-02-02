import React from 'react';
import { GridColumn } from './GridColumn';
import { MetricsGrid } from '../Metrics/MetricsGrid';
import { StatusFeed } from '../Status/StatusFeed';
import { CombatEffectivenessChart } from '../Charts';

export const LeftColumn: React.FC = () => (
    <GridColumn position="left" className="left-column-gap">
        <MetricsGrid />
        <StatusFeed />
        <CombatEffectivenessChart />
    </GridColumn>
);

export default LeftColumn;
