import React from 'react';
import { ExportFormat } from '../types';

export const generateExportFilename = (runId: string, format: ExportFormat): string => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const ext = format === 'excel' ? 'xlsx' : format;
    return `export_${runId}_${timestamp}.${ext}`;
};

export const downloadBlob = (blob: Blob, filename: string): void => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
};

export const formatExportProgress = (status: string): string => {
    const messages: Record<string, string> = {
        idle: 'Ready to export',
        preparing: 'Preparing export...',
        generating: 'Generating export...',
        downloading: 'Downloading...',
        complete: 'Export complete!',
        error: 'Export failed'
    };
    return messages[status] || status;
};
