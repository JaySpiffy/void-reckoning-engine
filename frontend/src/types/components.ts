import React from 'react';

/**
 * Common prop types for dashboard components.
 */

export interface CardProps {
    title: string;
    children: React.ReactNode;
    headerActions?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
    loading?: boolean;
}

export interface DashboardLayoutProps {
    children: React.ReactNode;
    factions?: string[];
}

export interface GridColumnProps {
    children: React.ReactNode;
    className?: string;
    position: 'left' | 'center' | 'right';
}

export interface ConnectionStatusProps {
    className?: string;
}

export interface TimelineControlsProps {
    className?: string;
}

export interface TurnDisplayProps {
    className?: string;
}

export interface LoadingOverlayProps {
    visible: boolean;
    message?: string;
}

export interface RefreshButtonProps {
    className?: string;
}

export interface FilterPanelProps {
    factions: string[];
    className?: string;
}

export interface FactionFilterProps {
    factions: string[];
    className?: string;
}

export interface TurnRangeSliderProps {
    className?: string;
}

export interface SimulationControlsProps {
    className?: string;
}

export interface MetricVisibilityTogglesProps {
    className?: string;
}

export interface GridContainerProps {
    children: React.ReactNode;
}

export interface MetricCardProps {
    label: string;
    value: number;
    unit: string;
    loading?: boolean;
    error?: Error | null;
    accentColor?: boolean;
}

export interface StatusMessageProps {
    message: string;
    type: 'info' | 'warning' | 'error';
    timestamp: number;
}

export interface StatusFeedProps {
    maxMessages?: number;
    className?: string;
}

export interface GalaxyMapProps {
    className?: string;
    style?: React.CSSProperties;
    onSystemClick?: (systemName: string) => void;
}

export interface GalaxyControlsProps {
    className?: string;
    onReset?: () => void;
    onZoomIn?: () => void;
    onZoomOut?: () => void;
}

export interface GalaxyPanelProps {
    className?: string;
    style?: React.CSSProperties;
}
