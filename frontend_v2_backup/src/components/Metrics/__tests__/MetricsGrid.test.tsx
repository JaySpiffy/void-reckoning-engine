import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MetricsGrid } from '../MetricsGrid';

describe('MetricsGrid', () => {
    it('renders metrics correctly', () => {
        const mockMetrics = [
            { label: 'Turn', value: 10, change: 1, trend: 'up' as const },
            { label: 'Income', value: '1000', change: 50, trend: 'up' as const },
            { label: 'fleets', value: 5, change: -1, trend: 'down' as const }
        ];

        render(<MetricsGrid metrics={mockMetrics} />);

        expect(screen.getByText('Turn')).toBeInTheDocument();
        expect(screen.getByText('10')).toBeInTheDocument();
        expect(screen.getByText('Income')).toBeInTheDocument();
        expect(screen.getByText('1000')).toBeInTheDocument();
    });

    it('renders empty state when no metrics provided', () => {
        render(<MetricsGrid metrics={[]} />);
        const grid = screen.getByTestId('metrics-grid'); // Assuming component has data-testid or we query by class logic
        expect(grid).toBeEmptyDOMElement();
    });
});
