import { create } from 'zustand';
import { Alert, AlertSeverity, AlertSummary } from '../types';
import { alertsApi } from '../api/client';

interface AlertsState {
    alerts: Alert[];
    summary: AlertSummary | null;
    loading: boolean;
    error: string | null;
    showHistory: boolean;
    severityFilter: AlertSeverity[];
    typeFilter: string;
    page: number;
    pageSize: number;
    total: number;

    // Actions
    fetchActiveAlerts: () => Promise<void>;
    fetchAlertHistory: (page?: number, pageSize?: number) => Promise<void>;
    fetchSummary: () => Promise<void>;
    acknowledgeAlert: (id: string) => Promise<void>;
    resolveAlert: (id: string) => Promise<void>;
    addAlert: (alert: Omit<Alert, 'id' | 'timestamp' | 'acknowledged' | 'resolved'>) => void;
    addAlertFromWebSocket: (alert: Alert) => void;
    toggleHistory: () => void;
    setSeverityFilter: (severities: AlertSeverity[]) => void;
    setTypeFilter: (type: string) => void;
    clearAll: () => void;
}

export const useAlertsStore = create<AlertsState>((set, get) => ({
    alerts: [],
    summary: null,
    loading: false,
    error: null,
    showHistory: false,
    severityFilter: ['info', 'warning', 'error', 'critical'],
    typeFilter: 'ALL',
    page: 1,
    pageSize: 20,
    total: 0,

    fetchActiveAlerts: async () => {
        set({ loading: true, error: null });
        try {
            const response = await alertsApi.getActive();
            // Optional: apply client-side type filtering if needed
            set({ alerts: response.data, loading: false });
        } catch (err: any) {
            set({ error: err.message, loading: false });
        }
    },

    fetchAlertHistory: async (page = 1, pageSize = 20) => {
        set({ loading: true, error: null, page, pageSize });
        try {
            const { severityFilter, typeFilter } = get();

            // Construct params
            const params: any = {
                page,
                page_size: pageSize,
                severity: severityFilter
            };

            if (typeFilter && typeFilter !== 'ALL') {
                params.alert_type = typeFilter;
            }

            const response = await alertsApi.getHistory(params);
            set({
                alerts: response.data.items,
                total: response.data.total,
                loading: false
            });
        } catch (err: any) {
            set({ error: err.message, loading: false });
        }
    },

    fetchSummary: async () => {
        try {
            const response = await alertsApi.getSummary();
            set({ summary: response.data });
        } catch (err: any) {
            console.error('Failed to fetch alert summary:', err);
        }
    },

    acknowledgeAlert: async (id) => {
        try {
            await alertsApi.acknowledge(id);
            set((state) => ({
                alerts: state.alerts.map((a) => a.id === id ? { ...a, acknowledged: true } : a)
            }));
            // Update summary
            get().fetchSummary();
        } catch (err: any) {
            console.error(`Failed to acknowledge alert ${id}:`, err);
        }
    },

    resolveAlert: async (id) => {
        try {
            await alertsApi.resolve(id);
            set((state) => ({
                alerts: state.alerts.map((a) => a.id === id ? { ...a, resolved: true } : a)
            }));
            // Update summary
            get().fetchSummary();
        } catch (err: any) {
            console.error(`Failed to resolve alert ${id}:`, err);
        }
    },

    addAlert: (alertData) => {
        const newAlert: Alert = {
            ...alertData,
            id: `local-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date().toISOString(),
            acknowledged: false,
            resolved: false,
            context: alertData.context || {}
        };
        set((state) => ({
            alerts: [newAlert, ...state.alerts].slice(0, 100)
        }));
    },

    addAlertFromWebSocket: (alert) => set((state) => {
        // Prevent duplicates
        if (state.alerts.some(a => a.id === alert.id)) return state;

        const newAlerts = [alert, ...state.alerts].slice(0, 100);

        // If summary exists, increment counts
        const newSummary = state.summary ? {
            ...state.summary,
            total: state.summary.total + 1,
            active: state.summary.active + 1,
            by_severity: {
                ...state.summary.by_severity,
                [alert.severity]: (state.summary.by_severity[alert.severity] || 0) + 1
            }
        } : state.summary;

        return { alerts: newAlerts, summary: newSummary };
    }),

    toggleHistory: () => set((state) => {
        const nextShowHistory = !state.showHistory;
        if (nextShowHistory) {
            get().fetchAlertHistory();
        } else {
            get().fetchActiveAlerts();
        }
        return { showHistory: nextShowHistory };
    }),

    setSeverityFilter: (severityFilter) => {
        set({ severityFilter });
        if (get().showHistory) {
            get().fetchAlertHistory(1, get().pageSize);
        }
    },

    setTypeFilter: (typeFilter) => {
        set({ typeFilter });
        if (get().showHistory) {
            get().fetchAlertHistory(1, get().pageSize);
        }
    },

    clearAll: () => set({ alerts: [], summary: null }),
}));
