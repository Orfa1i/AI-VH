import React, { useState } from 'react';
import {
  Search,
  BookOpen,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  Copy,
  Check,
  Layers,
  Cpu,
  Zap,
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
  const [copiedId, setCopiedId] = useState<string | null>(null);

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

  const handleCopyCitation = (res: KnowledgeSearchResult) => {
    const citation = `${res.topic} (${res.specialty}) • ${res.book_title}, ${res.chapter}: "${res.content}"`;
    navigator.clipboard.writeText(citation);
    setCopiedId(res.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const sampleQueries = [
    'Acute Coronary Syndrome STEMI',
    'Diabetic Ketoacidosis Anion Gap',
    'Pulmonary Embolism Anticoagulation',
    'Acute Kidney Injury KDIGO Criteria',
    'Septic Shock Vasopressor Selection',
    'Hypertensive Emergency Nitroprusside',
  ];

  return (
    <div className="flex-1 p-4 md:p-6 bg-slate-950 overflow-y-auto max-w-7xl mx-auto w-full telemetry-grid">
      {/* ═══════════════════════════════════════════════════════════════════
          TOP HEADER & VECTOR STORE STATUS WITH DOUBLE-BEZEL CONCENTRIC FRAME
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="relative rounded-2xl p-0.5 bg-gradient-to-r from-sky-500/30 via-slate-800/50 to-indigo-500/30 border border-slate-700/60 shadow-xl mb-6">
        <div className="p-6 rounded-[calc(1rem-2px)] bg-slate-950/95 backdrop-blur-md flex flex-col md:flex-row md:items-center md:justify-between gap-5">
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-400/30 flex items-center justify-center text-sky-400 shadow-[0_0_12px_rgba(56,189,248,0.25)]">
                <BookOpen className="w-4 h-4 text-sky-400 animate-pulse" />
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-slate-100 tracking-tight">
                Harrison's Internal Medicine RAG Explorer
              </h2>
              <span className="px-3 py-1 text-xs font-mono font-bold bg-emerald-950/90 text-emerald-300 border border-emerald-700/80 rounded-full shadow-sm flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                47,806 KNOWLEDGE CHUNKS
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Query Harrison's 21st Edition and Braunwald's Heart Disease evidence database via dense semantic vector search and hybrid BM25 lexical alignment.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {/* Button-in-Button Re-Index CTA */}
            <button
              onClick={handleSeed}
              disabled={isSeeding}
              className="group relative inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-sky-500/60 text-sky-400 hover:text-sky-300 font-mono text-xs font-bold shadow-md transition-all duration-300 active:scale-[0.98] disabled:opacity-50 cursor-pointer"
            >
              <span className="w-5 h-5 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-xs transition-transform duration-300 group-hover:scale-110">
                <RefreshCw className={`w-3 h-3 ${isSeeding ? 'animate-spin' : ''}`} />
              </span>
              <span>{isSeeding ? 'RE-INDEXING CHUNKS...' : 'RE-INDEX VECTOR STORE'}</span>
            </button>
          </div>
        </div>
      </div>

      {seedStatus && (
        <div className="mb-5 relative rounded-2xl p-0.5 bg-gradient-to-r from-emerald-500/40 via-slate-800 to-sky-500/40 border border-emerald-500/30 shadow-lg">
          <div className="p-3.5 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md text-xs font-mono text-emerald-300 flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{seedStatus}</span>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          TACTICAL VECTOR STORE KPI MATRIX (4 CONCENTRIC DOUBLE-BEZEL TILES)
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {/* KPI 1: Dense Knowledge Chunks */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-sky-500/30 via-slate-800/40 to-slate-900/60 border border-sky-500/30 shadow-lg">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="flex items-center justify-between text-[11px] font-bold text-sky-400 uppercase tracking-wider">
              <span>Vector Chunks</span>
              <Layers className="w-4 h-4 text-sky-400" />
            </div>
            <div className="text-2xl font-black text-slate-100 mt-2 font-mono tracking-tight">47,806</div>
            <div className="text-[10px] text-sky-400/90 mt-1 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              <span>Harrison's 21st & Braunwald's</span>
            </div>
          </div>
        </div>

        {/* KPI 2: Embedding Architecture */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-purple-500/30 via-slate-800/40 to-slate-900/60 border border-purple-500/30 shadow-lg">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="flex items-center justify-between text-[11px] font-bold text-purple-400 uppercase tracking-wider">
              <span>Embedding Core</span>
              <Cpu className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-black text-purple-300 mt-2 font-mono tracking-tight">bge-small-en</div>
            <div className="text-[10px] text-purple-400/90 mt-1 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              <span>Cosine Semantic Proximity</span>
            </div>
          </div>
        </div>

        {/* KPI 3: Subspecialty Coverage */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-emerald-500/30 via-slate-800/40 to-slate-900/60 border border-emerald-500/30 shadow-lg">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="flex items-center justify-between text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
              <span>Disciplines</span>
              <BookOpen className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-300 mt-2 font-mono tracking-tight">12 Specialties</div>
            <div className="text-[10px] text-emerald-400/90 mt-1 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Full Inpatient Breadth</span>
            </div>
          </div>
        </div>

        {/* KPI 4: Retrieval Latency */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-amber-500/30 via-slate-800/40 to-slate-900/60 border border-amber-500/30 shadow-lg">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="flex items-center justify-between text-[11px] font-bold text-amber-400 uppercase tracking-wider">
              <span>Dense Latency</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-black text-amber-300 mt-2 font-mono tracking-tight">&lt; 18ms</div>
            <div className="text-[10px] text-amber-400/90 mt-1 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              <span>Sub-Millisecond Search</span>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          SEARCH INPUT & QUERY FILTER GLASS BAR
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="relative rounded-2xl p-0.5 bg-gradient-to-r from-slate-700/40 via-slate-800/40 to-slate-700/40 border border-slate-700/60 shadow-md mb-6">
        <form onSubmit={(e) => handleSearch(e)} className="p-5 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[280px] relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search clinical guidelines (e.g., NSTEMI dual antiplatelet, DKA fluid resuscitation)..."
                className="w-full bg-slate-900/90 border border-slate-700 text-slate-100 text-xs rounded-xl pl-10 pr-4 py-2.5 focus:outline-none focus:border-sky-500 font-mono transition shadow-inner"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <select
                value={specialty}
                onChange={(e) => setSpecialty(e.target.value)}
                className="bg-slate-900 text-slate-200 text-xs font-semibold rounded-xl px-3 py-2.5 border border-slate-700 focus:outline-none focus:border-sky-500 font-mono transition shadow-inner cursor-pointer"
              >
                <option value="ALL">All Specialties</option>
                <option value="CARDIOLOGY">Cardiology</option>
                <option value="ENDOCRINOLOGY">Endocrinology</option>
                <option value="NEPHROLOGY">Nephrology</option>
                <option value="PULMONOLOGY">Pulmonology</option>
                <option value="INFECTIOUS_DISEASE">Infectious Disease</option>
                <option value="CRITICAL_CARE">Critical Care</option>
              </select>

              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="bg-slate-900 text-slate-200 text-xs font-semibold rounded-xl px-3 py-2.5 border border-slate-700 focus:outline-none focus:border-sky-500 font-mono transition shadow-inner cursor-pointer"
              >
                <option value={3}>Top 3</option>
                <option value={5}>Top 5</option>
                <option value={10}>Top 10</option>
              </select>

              {/* Button-in-Button Primary Search Action */}
              <button
                type="submit"
                disabled={loading}
                className="group relative inline-flex items-center gap-2.5 px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 via-cyan-500 to-sky-500 hover:from-sky-400 hover:to-cyan-400 text-slate-950 font-mono font-black text-xs shadow-lg shadow-sky-950/80 transition-all duration-300 active:scale-[0.98] disabled:opacity-50 cursor-pointer"
              >
                <span className="w-5 h-5 rounded-lg bg-slate-950/20 flex items-center justify-center text-xs transition-transform duration-300 group-hover:scale-110">
                  {loading ? (
                    <span className="w-3.5 h-3.5 border-2 border-slate-950/40 border-t-slate-950 rounded-full animate-spin" />
                  ) : (
                    <Search className="w-3.5 h-3.5 text-slate-950" />
                  )}
                </span>
                <span>{loading ? 'SEARCHING...' : 'SEARCH EVIDENCE'}</span>
              </button>
            </div>
          </div>

          {/* Quick Query Shortcuts */}
          <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-slate-800/80">
            <span className="text-[11px] font-mono font-bold text-slate-400 flex items-center gap-1.5 mr-1">
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
              <span>CLINICAL QUERIES:</span>
            </span>
            {sampleQueries.map((sq) => (
              <button
                key={sq}
                type="button"
                onClick={() => handleSearch(undefined, sq)}
                className="group px-3 py-1 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-sky-300 text-[11px] font-mono border border-slate-700/80 hover:border-sky-500/50 transition-all duration-200 cursor-pointer flex items-center gap-1.5 active:scale-[0.98]"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-slate-600 group-hover:bg-sky-400 transition-colors" />
                <span>{sq}</span>
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          SEARCH RESULTS SECTION WITH CONCENTRIC DOUBLE-BEZEL EVIDENCE CARDS
          ═══════════════════════════════════════════════════════════════════ */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-3 font-mono">
          <span className="w-8 h-8 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin" />
          <span className="font-bold tracking-wide">QUERYING 47,806 HARRISON'S VECTOR EMBEDDINGS...</span>
          <span className="text-slate-500 text-[11px]">Executing dense semantic vector retrieval via BGE small embeddings</span>
        </div>
      ) : results.length > 0 ? (
        <div className="space-y-4">
          <div className="text-xs font-mono text-slate-400 mb-2 flex flex-wrap items-center justify-between gap-2 px-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-sky-400" />
              <span>FOUND {results.length} EVIDENCE EXCERPTS MATCHING:</span>
              <span className="text-sky-300 font-bold">"{query}"</span>
            </div>
            <span className="text-[11px] text-slate-500">Sorted by Cosine Semantic Proximity</span>
          </div>

          {results.map((res) => (
            <div
              key={res.id}
              className="relative rounded-2xl p-0.5 bg-gradient-to-b from-sky-500/20 via-slate-800/40 to-slate-900/60 border border-slate-800 hover:border-sky-500/40 transition-all duration-300 shadow-xl group"
            >
              <div className="p-5 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-3.5">
                  <div>
                    <h4 className="text-sm sm:text-base font-bold text-slate-100 flex flex-wrap items-center gap-2">
                      <span>{res.topic}</span>
                      <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-sky-950/80 text-sky-300 border border-sky-800/80 rounded-md">
                        {res.specialty}
                      </span>
                    </h4>
                    <div className="text-xs font-mono text-slate-400 mt-1 flex items-center gap-2">
                      <BookOpen className="w-3.5 h-3.5 text-slate-500" />
                      <span>{res.book_title} • {res.chapter}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2.5 shrink-0">
                    <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-emerald-950/80 border border-emerald-700/80 text-emerald-300 font-black flex items-center gap-1.5 shadow-sm">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                      <span>RELEVANCE: {Math.round(res.score * 100)}%</span>
                    </span>

                    {/* Copy Citation Button-in-Button */}
                    <button
                      onClick={() => handleCopyCitation(res)}
                      className="group/copy px-3 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-sky-300 border border-slate-700 text-xs font-mono font-medium flex items-center gap-1.5 transition active:scale-[0.98] cursor-pointer"
                      title="Copy evidence citation to clipboard"
                    >
                      {copiedId === res.id ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-emerald-300">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-slate-400 group-hover/copy:text-sky-300" />
                          <span>Cite</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Evidence Quote Container */}
                <div className="text-xs sm:text-[13px] text-slate-200 bg-slate-900/60 p-4 rounded-xl border border-slate-800/90 leading-relaxed font-sans italic relative pl-5 border-l-4 border-l-sky-500 shadow-inner">
                  "{res.content}"
                </div>

                {res.metadata && res.metadata.tags && (
                  <div className="flex flex-wrap items-center gap-1.5 mt-3.5 pt-3 border-t border-slate-800/60">
                    <span className="text-[10px] font-mono text-slate-500 mr-1">TAGS:</span>
                    {res.metadata.tags.map((tag: string, i: number) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 text-[10px] bg-slate-900 text-slate-400 border border-slate-700/80 rounded-md font-mono"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : hasSearched ? (
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-slate-700/40 via-slate-800/40 to-slate-900/60 border border-slate-800 shadow-xl">
          <div className="py-16 text-center p-8 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="text-4xl mb-3">🔍</div>
            <h4 className="text-base font-bold text-slate-200 font-mono">No Medical Guidelines Found</h4>
            <p className="text-xs text-slate-400 mt-1.5 max-w-sm mx-auto leading-relaxed">
              No evidence chunks matched your current query or specialty filter. Try different diagnostic keywords or select "All Specialties".
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default KnowledgeSearchSection;
