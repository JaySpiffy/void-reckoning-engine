import React from 'react';
import styles from './LoadingOverlay.module.css';
import { LoadingOverlayProps } from '../../types/components';

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
    visible,
    message = "INITIALIZING COMMAND COGITATOR..."
}) => {
    if (!visible) return null;

    return (
        <div className={styles.overlay}>
            <div className={styles.spinner}></div>
            <div className={styles.message}>{message}</div>
        </div>
    );
};
