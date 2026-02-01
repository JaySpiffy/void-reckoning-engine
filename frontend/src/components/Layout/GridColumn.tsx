import React from 'react';
import styles from './DashboardLayout.module.css';
import { GridColumnProps } from '../../types/components';

/**
 * Structural component for grid columns that handles independent scrolling.
 */
export const GridColumn: React.FC<GridColumnProps> = ({ children, className = '', position }) => {
    return (
        <div className={`${styles.column} ${styles[position]} ${className}`}>
            {children}
        </div>
    );
};

export const GridContainer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return <div className={styles.gridLayout}>{children}</div>
}
