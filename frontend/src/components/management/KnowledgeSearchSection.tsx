import React, { useState } from 'react';

interface KnowledgeSearchResult {
  id: string;
  specialty: string;
  book_title: string;
  chapter: string;
  topic: string;
  content: string;
  score: number;
  metadata?: Record<string, any>;
}

export const KnowledgeSearchSection: React.FC = () => {
  const [query, setQuery] = useState('Acute Coronary Syndrome STEMI');
  const [specialty, setSpecialty] = useState('ALL');
  const [topK, setTopK] = useState<number>(5);
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [hasSearched, setHasSearched] = useState<boolean>(false);
  const [isSeeding, setIsSeeding] = useState<boolean>(false);
  const [seedStatus, setSeedStatus] = useState<string | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setHasSearched(true);
    try {
      const params = new URLSearchParams({
        q: query.trim(),
        top_k: String(topK),
      });
      if (specialty !== 'ALL') {
        params.append('specialty', specialty);
      }

      const res = await fetch(`/api/knowledge/search?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data.results || []);
      }
    } catch (err) {
      console.error('Error searching knowledge chunks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    setIsSeeding(true);
    setSeedStatus(null);
    try {
      const res = await fetch('/api/knowledge/seed', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSeedStatus(`Knowledge Vector Store populated: ${data.total_seeded || 20} chunks indexed.`);
      }
    } catch (err) {
      setSeedStatus('Failed to seed knowledge base.');
    } finally {
      setIsSeeding(false);
    }
  };

  return (
    <div className="flex-1 p-6 bg-slate-900/60 overflow-y-auto max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-slate-100">Harrison's Internal Medicine RAG Search</span>
            <span className="px-2.5 py-0.5 text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full">
              128-Dim Vector Store
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Query Harrison's 21st Edition clinical guidelines, disease criteria, diagnostic workups, and medication contraindications.
          </p>
        </div>

        <button
          onClick={handleSeed}
          disabled={isSeeding}
          className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs rounded-lg border border-slate-700 flex items-center gap-1.5 transition self-start disabled:opacity-50"
        >
          {isSeeding ? 'Seeding Embeddings...' : '⚡ Re-Index Harrison\'s Chunks'}
        </button>
      </div>

      {seedStatus && (
        <div className="mb-4 p-3 bg-cyan-950/60 border border-cyan-800 rounded-lg text-xs text-cyan-300">
          {seedStatus}
        </div>
      )}

      {/* Search Input Bar */}
      <form onSubmit={handleSearch} className="bg-slate-800/40 border border-slate-800 p-4 rounded-xl mb-6 flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[280px]">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search medical guidelines (e.g., Diabetic Ketoacidosis Anion Gap, Submassive PE)..."
            className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3.5 py-2.5 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            className="bg-slate-900 text-slate-200 text-xs rounded-lg px-3 py-2.5 border border-slate-700 focus:outline-none"
          >
            <option value="ALL">All Specialties</option>
            <option value="CARDIOLOGY">Cardiology</option>
            <option value="ENDOCRINOLOGY">Endocrinology</option>
            <option value="NEPHROLOGY">Nephrology</option>
            <option value="PULMONOLOGY">Pulmonology</option>
          </select>

          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="bg-slate-900 text-slate-200 text-xs rounded-lg px-3 py-2.5 border border-slate-700 focus:outline-none font-mono"
          >
            <option value={3}>Top 3</option>
            <option value={5}>Top 5</option>
            <option value={10}>Top 10</option>
          </select>

          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs rounded-lg transition shadow disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search Evidence'}
          </button>
        </div>
      </form>

      {/* Results */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-2">
          <span className="w-5 h-5 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
          <span>Computing dense vector similarity & lexical overlap...</span>
        </div>
      ) : results.length > 0 ? (
        <div className="space-y-4">
          <div className="text-xs text-slate-400 mb-2">
            Found {results.length} relevant guideline excerpts matching "{query}":
          </div>

          {results.map((res) => (
            <div
              key={res.id}
              className="bg-slate-800/40 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition shadow-sm"
            >
              <div className="flex items-start justify-between gap-4 mb-2">
                <div>
                  <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                    <span>{res.topic}</span>
                    <span className="px-2 py-0.5 text-[10px] font-semibold bg-slate-900 text-cyan-400 border border-slate-700 rounded">
                      {res.specialty}
                    </span>
                  </h4>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {res.book_title} • {res.chapter}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-cyan-300 font-bold">
                    Relevance: {(res.score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="text-xs text-slate-300 bg-slate-950/70 p-4 rounded-lg border border-slate-900 leading-relaxed font-sans">
                {res.content}
              </div>

              {res.metadata && res.metadata.tags && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {res.metadata.tags.map((tag: string, i: number) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 text-[10px] bg-slate-900 text-slate-400 border border-slate-800 rounded font-mono"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : hasSearched ? (
        <div className="py-12 text-center text-slate-500 text-xs">
          No medical guidelines found matching query. Try different diagnostic keywords.
        </div>
      ) : null}
    </div>
  );
};

export default KnowledgeSearchSection;
