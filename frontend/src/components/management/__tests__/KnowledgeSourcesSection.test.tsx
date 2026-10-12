import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { KnowledgeSourcesSection } from '../KnowledgeSourcesSection';



describe('KnowledgeSourcesSection Component', () => {
  const mockSources = [
    {
      id: 'SRC-PUBMED',
      name: 'PubMed / MEDLINE Clinical Library',
      url: 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/',
      description: 'NCBI peer-reviewed literature',
      status: 'ACTIVE',
      source_type: 'PUBMED',
      last_synced_at: '2026-10-08T12:00:00Z',
      error_message: null,
    },
    {
      id: 'SRC-OPENFDA',
      name: 'openFDA Drug Labels & Safety Alerts',
      url: 'https://api.fda.gov/drug/label.json',
      description: 'FDA structured drug labeling',
      status: 'INACTIVE',
      source_type: 'OPENFDA',
      last_synced_at: '2026-10-08T12:00:00Z',
      error_message: null,
    },
  ];

  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockImplementation((input: any, init?: any) => {
      const url = String(input);
      const method = (init?.method || 'GET').toUpperCase();

      if (url.includes('/status') && method === 'PATCH') {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ status: 'SUCCESS' }),
        } as Response);
      }

      if (url.includes('/sync') && method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ status: 'SUCCESS', message: 'Verified' }),
        } as Response);
      }

      if (method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({
            status: 'SUCCESS',
            source: {
              id: 'SRC-NEW',
              name: 'CDC Guidelines',
              url: 'https://cdc.gov',
              status: 'ACTIVE',
              source_type: 'CUSTOM',
            },
          }),
        } as Response);
      }

      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ sources: mockSources, total: mockSources.length }),
      } as Response);
    });
  });





  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders registered knowledge sources and status indicators', async () => {
    render(<KnowledgeSourcesSection />);

    expect(await screen.findByText('PubMed / MEDLINE Clinical Library', {}, { timeout: 3000 })).toBeInTheDocument();
    expect(screen.getAllByText('openFDA Drug Labels & Safety Alerts').length).toBeGreaterThan(0);
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });



  it('allows activating / deactivating a knowledge source', async () => {
    render(<KnowledgeSourcesSection />);

    await waitFor(() => {
      expect(screen.getByText('PubMed / MEDLINE Clinical Library')).toBeInTheDocument();
    });

    // PubMed is active -> clicking Deactivate toggles status
    const deactivateBtn = screen.getByRole('button', { name: /Deactivate/i });
    fireEvent.click(deactivateBtn);

    await waitFor(() => {
      expect(screen.getByText(/Source "PubMed \/ MEDLINE Clinical Library" is now INACTIVE/i)).toBeInTheDocument();
    });
  });

  it('submits a new knowledge source through the form', async () => {
    render(<KnowledgeSourcesSection />);

    const nameInput = screen.getByLabelText(/Source Name/i);
    const urlInput = screen.getByLabelText(/Source URL \/ API Endpoint/i);

    fireEvent.change(nameInput, { target: { value: 'CDC Guidelines' } });
    fireEvent.change(urlInput, { target: { value: 'https://cdc.gov' } });

    const submitBtn = screen.getByRole('button', { name: /Save Knowledge Source/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Medical knowledge source registered and synchronized/i)).toBeInTheDocument();
    });
  });
});
