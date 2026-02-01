import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ExportModal from '../ExportModal';
import { exportApi } from '../../../api/client';
import { useDashboardStore } from '../../../stores/dashboardStore';
import { useFiltersStore } from '../../../stores/filtersStore';

// Mock stores and API
vi.mock('../../../api/client', () => ({
    exportApi: {
        exportMetrics: vi.fn(),
    },
}));

vi.mock('../../../stores/dashboardStore', () => ({
    useDashboardStore: vi.fn(),
}));

vi.mock('../../../stores/filtersStore', () => ({
    useFiltersStore: vi.fn(),
}));

describe('ExportModal', () => {
    const mockOnClose = vi.fn();
    const mockVisibleMetrics = {
        economy: true,
        battles: false,
        units: true,
    };

    beforeEach(() => {
        vi.clearAllMocks();
        (useDashboardStore as any).mockReturnValue({
            status: { universe: 'test-uni', run_id: 'test-run', batch_id: 'test-batch' },
        });
        (useFiltersStore as any).mockReturnValue({
            visibleMetrics: mockVisibleMetrics,
            selectedFactions: ['Imperium'],
            turnRange: { min: 0, max: 100 },
        });
    });

    it('should not render when closed', () => {
        const { container } = render(<ExportModal isOpen={false} onClose={mockOnClose} />);
        expect(container.firstChild).toBeNull();
    });

    it('should render and initial metrics should match visibleMetrics', () => {
        render(<ExportModal isOpen={true} onClose={mockOnClose} />);

        expect(screen.getByText(/Data Export System/i)).toBeInTheDocument();
        // Checkboxes for visibleMetrics ('economy' and 'units' should be checked initially due to the new resync logic)
        const economyCheckbox = screen.getByLabelText(/Economy/i) as HTMLInputElement;
        const unitsCheckbox = screen.getByLabelText(/Units/i) as HTMLInputElement;
        const battlesCheckbox = screen.getByLabelText(/Battles/i) as HTMLInputElement;

        expect(economyCheckbox.checked).toBe(true);
        expect(unitsCheckbox.checked).toBe(true);
        expect(battlesCheckbox.checked).toBe(false);
    });

    it('should handle format selection', () => {
        render(<ExportModal isOpen={true} onClose={mockOnClose} />);

        const excelOption = screen.getByText('EXCEL');
        fireEvent.click(excelOption);

        expect(excelOption.closest('div')).toHaveClass(/active/);
    });

    it('should call exportApi when Start Export is clicked', async () => {
        (exportApi.exportMetrics as any).mockResolvedValue({ data: new Blob() });

        render(<ExportModal isOpen={true} onClose={mockOnClose} />);

        const exportBtn = screen.getByText(/Start Export/i);
        fireEvent.click(exportBtn);

        await waitFor(() => {
            expect(exportApi.exportMetrics).toHaveBeenCalled();
        });

        expect(screen.getByText(/EXPORT COMPLETE!/i)).toBeInTheDocument();
    });

    it('should display error message on API failure', async () => {
        (exportApi.exportMetrics as any).mockRejectedValue(new Error('Backend error'));

        render(<ExportModal isOpen={true} onClose={mockOnClose} />);

        const exportBtn = screen.getByText(/Start Export/i);
        fireEvent.click(exportBtn);

        await waitFor(() => {
            expect(screen.getByText(/EXPORT FAILED: Backend error/i)).toBeInTheDocument();
        });
    });

    it('should toggle metrics', () => {
        render(<ExportModal isOpen={true} onClose={mockOnClose} />);

        const economyCheckbox = screen.getByLabelText(/Economy/i) as HTMLInputElement;
        fireEvent.click(economyCheckbox);

        expect(economyCheckbox.checked).toBe(false);
    });
});
