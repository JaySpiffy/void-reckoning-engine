import React, { useState } from 'react';
import styles from './RefreshButton.module.css';
import { getStatus } from '../../api/client';
import { useDashboardStore } from '../../stores/dashboardStore';

export const RefreshButton: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const updateStatus = useDashboardStore((s) => s.updateStatus);

    const handleRefresh = async () => {
        setLoading(true);
        try {
            const response = await getStatus();
            updateStatus(response.data);
        } catch (err) {
            console.error('Manual refresh failed:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <button
            className={styles.btnAccent}
            onClick={handleRefresh}
            disabled={loading}
        >
            {loading ? <div className="spinner-small"></div> : 'REFRESH'}
        </button>
    );
};
