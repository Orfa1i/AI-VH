import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { KnowledgeSearchSection } from '../KnowledgeSearchSection';

describe('KnowledgeSearchSection Component', () => {
  const mockBooksData = {
    total_chunks: 80398,
    total_books: 7,
    embedding_model: 'all-MiniLM-L6-v2',
    embedding_dim: 384,
    books: [
      {
        id: 'harrisons-principles-of-internal-medicine',
        title: "Harrison's Principles of Internal Medicine, 21st Edition (2022)",
        specialty: 'Internal Medicine',
        chunk_count: 31447,
        chapter_count: 503,
        status: 'ACTIVE',
        embedding_model: 'all-MiniLM-L6-v2',
        embedding_dim: 384,
        sample_chunks: [
          {
            id: 'HARRISON_P102',
            chapter: 'Cardiovascular Disorders',
            topic: 'NSTEMI Management',
            excerpt: 'Dual antiplatelet therapy with aspirin and a P2Y12 inhibitor...',
          },
        ],
      },
      {
        id: 'braunwalds-heart-disease',
        title: "Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine",
        specialty: 'Cardiology',
        chunk_count: 16359,
        chapter_count: 1345,
        status: 'ACTIVE',
        embedding_model: 'all-MiniLM-L6-v2',
        embedding_dim: 384,
        sample_chunks: [
          {
            id: 'BRAUNWALD_P412',
            chapter: 'Heart Failure',
            topic: 'HFrEF Pharmacotherapy',
            excerpt: 'Quadruple guideline-directed medical therapy includes ARNI...',
          },
        ],
      },
      {
        id: 'schwartzs-principles-of-surgery',
        title: "Schwartz's Principles of Surgery, 10th Edition",
        specialty: 'Surgery',
        chunk_count: 11983,
        chapter_count: 72,
        status: 'ACTIVE',
        embedding_model: 'all-MiniLM-L6-v2',
        embedding_dim: 384,
        sample_chunks: [],
      },
    ],
  };

  const mockChunksData = {
    total: 80398,
    limit: 20,
    offset: 0,
    chunks: [
      {
        id: 'AAV_P0003_C00',
        specialty: 'Neurology',
        book_title: "Adams and Victor's Principles of Neurology (8th Edition)",
        chapter: 'Adams and Victor',
        topic: 'Neurologic Examination',
        content: 'The clinical neurologic examination begins with mental status evaluation...',
        char_length: 74,
        vector_dim: 384,
        vector_preview: [-0.0063, 0.044, -0.0097, 0.0535, -0.0248],
      },
    ],
  };

  const mockSearchResults = {
    query: 'NSTEMI',
    count: 1,
    book_title: "Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine",
    results: [
      {
        id: 'BRAUN_001',
        specialty: 'Cardiology',
        book_title: "Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine",
        chapter: 'Acute Coronary Syndromes',
        topic: 'NSTEMI Risk Stratification',
        content: 'Immediate coronary angiography is indicated in patients with refractory angina or hemodynamic instability.',
        score: 0.89,
        metadata: { page: 412, char_length: 108 },
      },
    ],
  };

  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockImplementation((input: any, init?: any) => {
      const url = String(input);
      const method = (init?.method || 'GET').toUpperCase();

      if (url.includes('/api/knowledge/books')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockBooksData),
        } as Response);
      }

      if (url.includes('/api/knowledge/chunks')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockChunksData),
        } as Response);
      }

      if (url.includes('/api/knowledge/search')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockSearchResults),
        } as Response);
      }

      if (url.includes('/api/knowledge/embed-all') && method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              status: 'success',
              total_chunks: 80398,
              total_books: 7,
              message: 'All 7 medical knowledge boxes embedded and active in vector store.',
            }),
        } as Response);
      }

      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      } as Response);
    });
  });

  it('renders real telemetry statistics and medical knowledge boxes', async () => {
    render(<KnowledgeSearchSection />);

    // Check KPI stat cards with real formatted numbers
    await waitFor(() => {
      expect(screen.getByText('80,398')).toBeInTheDocument();
    });

    expect(screen.getByText(/384-dim \(all-MiniLM\)/i)).toBeInTheDocument();

    // Check medical knowledge box cards
    expect(screen.getByText("Harrison's Principles of Internal Medicine, 21st Edition (2022)")).toBeInTheDocument();
    expect(screen.getByText("Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine")).toBeInTheDocument();
    expect(screen.getByText("Schwartz's Principles of Surgery, 10th Edition")).toBeInTheDocument();

    // Check chunk counts on boxes
    expect(screen.getByText('31,447')).toBeInTheDocument();
    expect(screen.getByText('16,359')).toBeInTheDocument();
  });

  it('allows clicking "Search in this book" to select specific book', async () => {
    render(<KnowledgeSearchSection />);

    await waitFor(() => {
      expect(screen.getByText("Harrison's Principles of Internal Medicine, 21st Edition (2022)")).toBeInTheDocument();
    });

    const searchInBookButtons = screen.getAllByRole('button', { name: /search in this book/i });
    expect(searchInBookButtons.length).toBeGreaterThan(0);

    fireEvent.click(searchInBookButtons[0]);

    // Select should update to Harrison's
    const select = screen.getByLabelText(/search on book/i) as HTMLSelectElement;
    expect(select.value).toContain("Harrison's Principles of Internal Medicine");
  });

  it('opens Real Vector Chunks Explorer and displays chunk data', async () => {
    render(<KnowledgeSearchSection />);

    const exploreButton = screen.getByRole('button', { name: /explore vector chunks/i });
    fireEvent.click(exploreButton);

    await waitFor(() => {
      expect(screen.getByText('Real Vector Chunks Explorer')).toBeInTheDocument();
    });

    // Chunk ID should be visible
    expect(screen.getByText('AAV_P0003_C00')).toBeInTheDocument();
    expect(screen.getByText(/Embedding Vector/i)).toBeInTheDocument();
  });

  it('executes per-book semantic search and renders matching excerpts', async () => {
    render(<KnowledgeSearchSection />);

    const searchInput = screen.getByPlaceholderText(/search clinical topics/i);
    fireEvent.change(searchInput, { target: { value: 'NSTEMI' } });

    const searchButton = screen.getByRole('button', { name: /search evidence/i });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('NSTEMI Risk Stratification')).toBeInTheDocument();
    });

    expect(screen.getByText(/Immediate coronary angiography is indicated/i)).toBeInTheDocument();
    expect(screen.getByText('89%')).toBeInTheDocument();
  });

  it('triggers "Embed All Boxes" and displays confirmation alert', async () => {
    render(<KnowledgeSearchSection />);

    const embedAllButton = screen.getByRole('button', { name: /embed all boxes/i });
    fireEvent.click(embedAllButton);

    await waitFor(() => {
      expect(screen.getByText(/Successfully embedded all 7 medical knowledge boxes/i)).toBeInTheDocument();
    });
  });
});
