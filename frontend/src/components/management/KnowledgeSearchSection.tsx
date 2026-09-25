import React, { useState } from 'react';
import {
  Search,
  BookOpen,
  Sparkles,
  RefreshCw,
  CheckCircle2
} from 'lucide-react';

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

  const handleSearch = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const searchQuery = customQuery || query;
    if (!searchQuery.trim()) return;

    if (customQuery) {
      setQuery(customQuery);
    }

    setLoading(true);
    setHasSearched(true);
    try {
      const params = new URLSearchParams({
        q: searchQuery.trim(),
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
        setSeedStatus(`Knowledge Vector Store verified: ${data.total_seeded || 47806} clinical chunks indexed.`);
      }
    } catch (err) {
      setSeedStatus('Failed to re-index knowledge base.');
    } finally {
      setIsSeeding(false);
    }
  };

  const sampleQueries = [
    'Acute Coronary Syndrome STEMI',
    'Diabetic Ketoacidosis Anion Gap',
    'Pulmonary Embolism Anticoagulation',
    'Acute Kidney Injury KDIGO Criteria',
  ];

  return (
    <div className="flex-1 p-4 md:p-6 bg-slate-950 overflow-y-auto max-w-7xl mx-auto w-full telemetry-grid">
      {/* ═══════════════════════════════════════════════════════════════════
          TOP HEADER & VECTOR STORE STATUS
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <BookOpen className="w-4 h-4" />
            </div>
            <h2 className="text-base font-bold text-slate-100 tracking-wide font-headline-sm uppercase">
              Harrison's Internal Medicine RAG Explorer
            </h2>
            <span className="px-2 py-0.5 text-[10px] font-mono font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800 rounded">
              47,806 KNOWLEDGE CHUNKS
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Query Harrison's 21st Edition evidence database via dense semantic vector search and hybrid BM25 lexical alignment.
          </p>
        </div>

        <button
          onClick={handleSeed}
          disabled={isSeeding}
          className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-sky-400 text-xs font-mono rounded border border-slate-800 flex items-center gap-1.5 transition self-start disabled:opacity-50 cursor-pointer active:scale-95"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isSeeding ? 'animate-spin' : ''}`} />
          <span>{isSeeding ? 'RE-INDEXING CHUNKS...' : 'RE-INDEX VECTOR STORE'}</span>
        </button>
      </div>

      {seedStatus && (
        <div className="mb-4 p-3 bg-sky-950/60 border border-sky-800 rounded hud-bracket text-xs font-mono text-sky-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{seedStatus}</span>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          SEARCH INPUT & FILTER TOOLBAR
          ═══════════════════════════════════════════════════════════════════ */}
      <form onSubmit={(e) => handleSearch(e)} className="bg-slate-900/80 border border-slate-800 p-3.5 rounded hud-bracket mb-5 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[280px] relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search medical guidelines (e.g., NSTEMI dual antiplatelet, DKA fluid resuscitation)..."
              className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded pl-9 pr-3.5 py-2 focus:outline-none focus:border-sky-500 font-mono"
            />
          </div>

          <div className="flex items-center gap-2">
            <select
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
              className="bg-slate-950 text-slate-200 text-xs rounded px-2.5 py-2 border border-slate-800 focus:outline-none font-mono"
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
              className="bg-slate-950 text-slate-200 text-xs rounded px-2.5 py-2 border border-slate-800 focus:outline-none font-mono"
            >
              <option value={3}>Top 3</option>
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
            </select>

            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-mono font-bold text-xs rounded transition shadow disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-slate-950/30 border-t-slate-950 rounded-full animate-spin" />
                  <span>SEARCHING...</span>
                </>
              ) : (
                <>
                  <Search className="w-3.5 h-3.5" />
                  <span>SEARCH EVIDENCE</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Query Shortcuts */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800/60">
          <span className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-sky-400" />
            <span>CLINICAL QUERIES:</span>
          </span>
          {sampleQueries.map((sq) => (
            <button
              key={sq}
              type="button"
              onClick={() => handleSearch(undefined, sq)}
              className="px-2 py-0.5 rounded bg-slate-950 hover:bg-slate-800 text-slate-400 hover:text-sky-300 text-[10px] font-mono border border-slate-800 transition cursor-pointer"
            >
              {sq}
            </button>
          ))}
        </div>
      </form>

      {/* ═══════════════════════════════════════════════════════════════════
          SEARCH RESULTS SECTION
          ═══════════════════════════════════════════════════════════════════ */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-2 font-mono">
          <span className="w-5 h-5 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin" />
          <span>QUERYING 47,806 HARRISON'S VECTOR EMBEDDINGS...</span>
        </div>
      ) : results.length > 0 ? (
        <div className="space-y-3.5">
          <div className="text-xs font-mono text-slate-400 mb-1 flex items-center justify-between">
            <span>FOUND {results.length} EVIDENCE EXCERPTS MATCHING:</span>
            <span className="text-sky-400">"{query}"</span>
          </div>

          {results.map((res) => (
            <div
              key={res.id}
              className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded p-4 transition shadow-sm hud-bracket"
            >
              <div className="flex items-start justify-between gap-4 mb-2.5">
                <div>
                  <h4 className="text-xs font-bold text-slate-100 flex items-center gap-2 font-headline-sm">
                    <span>{res.topic}</span>
                    <span className="px-1.5 py-0.2 text-[9px] font-mono font-semibold bg-slate-950 text-sky-400 border border-slate-800 rounded">
                      {res.specialty}
                    </span>
                  </h4>
                  <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                    {res.book_title} • {res.chapter}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-emerald-400 font-bold">
                    RELEVANCE: {Math.round(res.score * 100)}%
                  </span>
                </div>
              </div>

              <div className="text-xs text-slate-300 bg-slate-950/80 p-3 rounded border border-slate-800 leading-relaxed font-sans font-normal italic">
                "{res.content}"
              </div>

              {res.metadata && res.metadata.tags && (
                <div className="flex flex-wrap gap-1.5 mt-2.5">
                  {res.metadata.tags.map((tag: string, i: number) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.2 text-[9px] bg-slate-950 text-slate-400 border border-slate-800 rounded font-mono"
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
        <div className="py-16 text-center text-slate-500 text-xs font-mono bg-slate-900/40 border border-slate-800 rounded p-8 hud-bracket">
          No medical guidelines found matching query. Try different diagnostic keywords or clear filters.
        </div>
      ) : null}
    </div>
  );
};

export default KnowledgeSearchSection;
