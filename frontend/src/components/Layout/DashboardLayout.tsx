import React from 'react';
import styles from './DashboardLayout.module.css';
import { DashboardLayoutProps } from '../../types/components';
import { FilterPanel } from '../Filters';
import { PerformancePanel } from '../Performance';

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children, factions }) => {
    return (
        <div className={styles.dashboardContainer}>
            <div style={{ padding: '0 1rem' }}>
                {factions && <FilterPanel factions={factions} />}
                <PerformancePanel />
            </div>
            {children}
        </div>
    );
};
