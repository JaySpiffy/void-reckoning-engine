import { bench, describe } from 'vitest';
import { render } from '@testing-library/react';
import { MetricsGrid } from '../components/Metrics/MetricsGrid';

describe('Performance', () => {
    bench('MetricsGrid render', () => {
        const metrics = Array.from({ length: 50 }, (_, i) => ({
            label: `Metric ${i}`,
            value: i * 100,
            change: 1,
            trend: 'up' as const
        }));

        render(<MetricsGrid metrics={ metrics } />);
    });
});
