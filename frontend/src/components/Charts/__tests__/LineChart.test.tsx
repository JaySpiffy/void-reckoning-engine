import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LineChart } from '../LineChart';

// Mock Recharts since it uses DOM APIs not fully supported in simple jsdom setup without polyfills
vi.mock('recharts', () => {
    const OriginalModule = vi.importActual('recharts');
    return {
        ...OriginalModule,
        ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
        LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
        Line: () => <div data-testid="line" />,
        XAxis: () => <div data-testid="x-axis" />,
        YAxis: () => <div data-testid="y-axis" />,
        Tooltip: () => <div data-testid="tooltip" />,
        Legend: () => <div data-testid="legend" />,
        CartesianGrid: () => <div data-testid="cartesian-grid" />,
    };
});

describe('LineChart', () => {
    const mockData = [
        { name: 'Turn 1', value: 100 },
        { name: 'Turn 2', value: 200 }
    ];

    it('renders chart components', () => {
        render(<LineChart data={mockData} dataKey="value" xAxisKey="name" />);

        expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    it('displays title if provided', () => {
        render(<LineChart data={mockData} dataKey="value" xAxisKey="name" title="Revenue Trend" />);
        expect(screen.getByText('Revenue Trend')).toBeInTheDocument();
    });
});
