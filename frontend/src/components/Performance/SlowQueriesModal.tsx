import React, { useEffect, useState } from 'react';
import styles from './SlowQueriesModal.module.css';
import { performanceApi } from '../../api/client';
import { SlowQuery } from '../../types';

interface SlowQueriesModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const SlowQueriesModal: React.FC<SlowQueriesModalProps> = ({ isOpen, onClose }) => {
    const [queries, setQueries] = useState<SlowQuery[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchQueries();
        }
    }, [isOpen]);

    const fetchQueries = async () => {
        setIsLoading(true);
        try {
            const response = await performanceApi.getSlowQueries({ threshold_ms: 50 }); // Default hardcoded or match plan
            // Sort by duration desc
            const sorted = response.data.sort((a, b) => b.duration_ms - a.duration_ms);
            setQueries(sorted);
        } catch (error) {
            console.error("Failed to fetch slow queries", error);
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    const threshold = 500; // ms for highlighting

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={e => e.stopPropagation()}>
                <div className={styles.header}>
                    <h2>Slow Operations Log</h2>
                    <button className={styles.closeButton} onClick={onClose}>×</button>
                </div>

                <div className={styles.content}>
                    {isLoading ? (
                        <div className={styles.emptyState}>Loading...</div>
                    ) : queries.length === 0 ? (
                        <div className={styles.emptyState}>No slow queries detected.</div>
                    ) : (
                        <table className={styles.tableContainer}>
                            <thead>
                                <tr>
                                    <th>Duration</th>
                                    <th>Operation</th>
                                    <th>Timestamp</th>
                                </tr>
                            </thead>
                            <tbody>
                                {queries.map((q, i) => (
                                    <tr key={i} className={styles.row}>
                                        <td className={q.duration_ms > threshold ? styles.verySlowQuery : styles.slowQuery}>
                                            {q.duration_ms.toFixed(1)} ms
                                        </td>
                                        <td>{q.metric}</td>
                                        <td>{new Date(q.timestamp).toLocaleTimeString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SlowQueriesModal;
