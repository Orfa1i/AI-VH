import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RLDatasetModal } from '../RLDatasetModal';

describe('RLDatasetModal Phase 1 503 latch', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal('confirm', vi.fn(() => true));
    (window as any).confirm = vi.fn(() => true);
  });

  it('shows a clear disabled message on HTTP 503 and keeps the modal usable', async () => {
    const fetchMock = vi.fn((url: string, _init?: RequestInit) => {
      if (typeof url === 'string' && url.includes('/api/rl/train')) {
        return Promise.resolve({
          ok: false,
          status: 503,
          json: async () => ({ detail: 'RL training export is temporarily disabled until Phase 5.' }),
        } as Response);
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({ statistics: null, pairs: [] }),
      } as Response);
    });
    global.fetch = fetchMock as unknown as typeof fetch;

    const user = userEvent.setup();
    render(<RLDatasetModal isOpen={true} onClose={() => {}} />);

    const trainButton = screen.getByRole('button', { name: /Send Data for Training/i });
    await user.click(trainButton);

    await waitFor(() => {
      expect(screen.getByTestId('train-blocked-503')).toBeInTheDocument();
    });
    expect(screen.getByText(/temporarily disabled until Phase 5/i)).toBeInTheDocument();
    // Modal did not break: header + close affordance still present
    expect(screen.getByText(/RL \/ Direct Preference Optimization/i)).toBeInTheDocument();
  });
});
