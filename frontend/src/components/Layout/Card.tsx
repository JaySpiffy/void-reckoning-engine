import React from 'react';
import styles from './Card.module.css';
import { CardProps } from '../../types/components';

export const Card: React.FC<CardProps> = ({
    title,
    children,
    headerActions,
    className = '',
    style,
    loading = false
}) => {
    return (
        <div className={`${styles.card} ${className}`} style={style}>
            <header className={styles.cardHeader}>
                <h2>{title}</h2>
                {headerActions && <div className={styles.headerActions}>{headerActions}</div>}
            </header>
            <div className={styles.cardContent}>
                {loading && (
                    <div className={styles.loadingOverlay}>
                        <div className="spinner-small"></div>
                    </div>
                )}
                {children}
            </div>
        </div>
    );
};
