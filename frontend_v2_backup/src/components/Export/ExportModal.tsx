import React, { useState, useEffect } from 'react';
import { useDashboardStore } from '../../stores/dashboardStore';
import { useFiltersStore } from '../../stores/filtersStore';
import { exportApi } from '../../api/client';
import { ExportFormat, ExportProgress } from '../../types';
import { generateExportFilename, downloadBlob, formatExportProgress } from '../../utils/exportHelpers';
import styles from './ExportModal.module.css';

interface ExportModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose }) => {
    const { status: simStatus } = useDashboardStore();
    const { visibleMetrics, selectedFactions, turnRange } = useFiltersStore();

    const [format, setFormat] = useState<ExportFormat>('csv');
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>(
        Object.entries(visibleMetrics).filter(([_, v]) => v).map(([k]) => k)
    );
    const [progress, setProgress] = useState<ExportProgress>({
        status: 'idle',
        progress: 0,
        message: 'Select format and metrics to begin'
    });

    // Resync selected metrics with current filter visibility when opened
    useEffect(() => {
        if (isOpen) {
            setSelectedMetrics(
                Object.entries(visibleMetrics)
                    .filter(([_, v]) => v)
                    .map(([k]) => k)
            );
        }
    }, [isOpen, visibleMetrics]);

    if (!isOpen) return null;

    const handleMetricToggle = (metric: string) => {
        setSelectedMetrics(prev =>
            prev.includes(metric)
                ? prev.filter(m => m !== metric)
                : [...prev, metric]
        );
    };

    const handleExport = async () => {
        if (selectedMetrics.length === 0) {
            setProgress({ status: 'error', progress: 0, message: 'Please select at least one metric' });
            return;
        }

        try {
            setProgress({ status: 'preparing', progress: 10, message: 'Preparing export payload...' });

            const payload = {
                universe: simStatus.universe,
                run_id: simStatus.run_id,
                batch_id: simStatus.batch_id,
                factions: selectedFactions,
                turn_range: turnRange,
                metrics: selectedMetrics,
                format
            };

            setProgress({ status: 'generating', progress: 40, message: 'Generating report on server...' });

            const response = await exportApi.exportMetrics(payload);

            setProgress({ status: 'downloading', progress: 70, message: 'Receiving data stream...' });

            const filename = generateExportFilename(simStatus.run_id, format);
            downloadBlob(response.data, filename);

            setProgress({ status: 'complete', progress: 100, message: 'EXPORT COMPLETE!' });

            setTimeout(() => {
                onClose();
                setProgress({ status: 'idle', progress: 0, message: '' });
            }, 1500);

        } catch (error: any) {
            console.error('Export failed:', error);
            setProgress({
                status: 'error',
                progress: 100,
                message: `EXPORT FAILED: ${error.message || 'Unknown error'}`
            });
        }
    };

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={e => e.stopPropagation()}>
                <div className={styles.header}>
                    <h2>Data Export System</h2>
                    <button className={styles.closeBtn} onClick={onClose}>&times;</button>
                </div>

                <div className={styles.content}>
                    <section className={styles.section}>
                        <h3>Select Format</h3>
                        <div className={styles.formatGrid}>
                            {(['csv', 'excel', 'pdf'] as ExportFormat[]).map(f => (
                                <div
                                    key={f}
                                    className={`${styles.formatOption} ${format === f ? styles.active : ''}`}
                                    onClick={() => setFormat(f)}
                                >
                                    <span className={styles.formatLabel}>{f.toUpperCase()}</span>
                                    <div className={styles.radio} />
                                </div>
                            ))}
                        </div>
                    </section>

                    <section className={styles.section}>
                        <h3>Select Metrics</h3>
                        <div className={styles.metricGrid}>
                            {Object.keys(visibleMetrics).map(m => (
                                <label key={m} className={styles.metricLabel}>
                                    <input
                                        type="checkbox"
                                        checked={selectedMetrics.includes(m)}
                                        onChange={() => handleMetricToggle(m)}
                                    />
                                    <span className={styles.checkboxLabel}>{m.charAt(0).toUpperCase() + m.slice(1)}</span>
                                </label>
                            ))}
                        </div>
                    </section>

                    <div className={styles.progressSection}>
                        <div className={styles.progressBarBg}>
                            <div
                                className={`${styles.progressBar} ${progress.status === 'error' ? styles.error : ''}`}
                                style={{ width: `${progress.progress}%` }}
                            />
                        </div>
                        <span className={`${styles.statusText} ${progress.status === 'error' ? styles.errorText : ''}`}>
                            {progress.message || formatExportProgress(progress.status)}
                        </span>
                    </div>
                </div>

                <div className={styles.footer}>
                    <button className={styles.cancelBtn} onClick={onClose} disabled={progress.status !== 'idle' && progress.status !== 'error'}>
                        Cancel
                    </button>
                    <button
                        className={styles.exportBtn}
                        onClick={handleExport}
                        disabled={progress.status !== 'idle' && progress.status !== 'error'}
                    >
                        {progress.status === 'idle' ? 'Start Export' : 'Retry Export'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ExportModal;
