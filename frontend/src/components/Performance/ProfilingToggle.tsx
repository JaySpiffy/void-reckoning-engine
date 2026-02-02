import React from 'react';
import styles from './PerformancePanel.module.css';

interface ProfilingToggleProps {
    enabled: boolean;
    loading?: boolean;
    onToggle: () => void;
}

const ProfilingToggle: React.FC<ProfilingToggleProps> = ({
    enabled,
    loading = false,
    onToggle
}) => {
    return (
        <button
            className={`${styles.profilingButton} ${enabled ? styles.enabled : ''}`}
            onClick={(e) => {
                e.stopPropagation();
                if (!loading) onToggle();
            }}
            disabled={loading}
        >
            {loading ? (
                <span className={styles.spinner}></span>
            ) : (
                enabled ? 'ENABLED' : 'DISABLED'
            )}
        </button>
    );
};

export default ProfilingToggle;
