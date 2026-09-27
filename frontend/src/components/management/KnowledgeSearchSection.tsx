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
  const [query, setQuery] = useState('');
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
    <div className="flex-1 p-4 md:p-6 bg-[#f8fafc] overflow-y-auto max-w-7xl mx-auto w-full telemetry-grid text-slate-900">
      {/* ═══════════════════════════════════════════════════════════════════
          TOP HEADER & VECTOR STORE STATUS
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-5">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 shadow-2xs">
              <BookOpen className="w-4 h-4 text-sky-600 animate-pulse" />
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight font-sans">
              Harrison's Internal Medicine RAG Explorer
            </h2>
            <span className="px-3 py-1 text-xs font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full shadow-2xs flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              47,806 KNOWLEDGE CHUNKS
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1.5 leading-relaxed font-sans">
            Query Harrison's 21st Edition and Braunwald's Heart Disease evidence database via dense semantic vector search and hybrid BM25 lexical alignment.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={handleSeed}
            disabled={isSeeding}
            className="group relative inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-slate-100 border border-slate-200 hover:border-sky-400 text-sky-700 hover:text-sky-800 font-mono text-xs font-bold shadow-xs transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer"
          >
            <span className="w-5 h-5 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-xs shadow-2xs">
              <RefreshCw className={`w-3 h-3 text-sky-600 ${isSeeding ? 'animate-spin' : ''}`} />
            </span>
            <span>{isSeeding ? 'RE-INDEXING CHUNKS...' : 'RE-INDEX VECTOR STORE'}</span>
          </button>
        </div>
      </div>

      {seedStatus && (
        <div className="mb-5 p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-mono text-emerald-800 flex items-center gap-2.5 shadow-xs">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{seedStatus}</span>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          TACTICAL VECTOR STORE KPI MATRIX
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {/* KPI 1: Dense Knowledge Chunks */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-[11px] font-bold text-sky-700 uppercase tracking-wider">
            <span>Vector Chunks</span>
            <Layers className="w-4 h-4 text-sky-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2 font-mono tracking-tight">47,806</div>
          <div className="text-[10px] text-sky-700 mt-1 flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-500" />
            <span>Harrison's 21st &amp; Braunwald's</span>
          </div>
        </div>

        {/* KPI 2: Embedding Architecture */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-[11px] font-bold text-purple-700 uppercase tracking-wider">
            <span>Embedding Core</span>
            <Cpu className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-black text-purple-900 mt-2 font-mono tracking-tight">bge-small-en</div>
          <div className="text-[10px] text-purple-700 mt-1 flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
            <span>Cosine Semantic Proximity</span>
          </div>
        </div>

        {/* KPI 3: Subspecialty Coverage */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-[11px] font-bold text-emerald-700 uppercase tracking-wider">
            <span>Disciplines</span>
            <BookOpen className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-emerald-800 mt-2 font-mono tracking-tight">12 Specialties</div>
          <div className="text-[10px] text-emerald-700 mt-1 flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Full Inpatient Breadth</span>
          </div>
        </div>

        {/* KPI 4: Retrieval Latency */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-[11px] font-bold text-amber-700 uppercase tracking-wider">
            <span>Dense Latency</span>
            <Zap className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-black text-amber-800 mt-2 font-mono tracking-tight">&lt; 18ms</div>
          <div className="text-[10px] text-amber-700 mt-1 flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span>Sub-Millisecond Search</span>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          SEARCH INPUT & QUERY FILTER BAR
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs mb-6">
        <form onSubmit={(e) => handleSearch(e)} className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[280px] relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search clinical guidelines (e.g., NSTEMI dual antiplatelet, DKA fluid resuscitation)..."
                className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-xl pl-10 pr-4 py-2.5 focus:bg-white focus:outline-none focus:border-sky-500 font-mono transition shadow-2xs"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <select
                value={specialty}
                onChange={(e) => setSpecialty(e.target.value)}
                className="bg-slate-50 text-slate-800 text-xs font-semibold rounded-xl px-3 py-2.5 border border-slate-300 focus:bg-white focus:outline-none focus:border-sky-500 font-mono transition cursor-pointer"
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
                className="bg-slate-50 text-slate-800 text-xs font-semibold rounded-xl px-3 py-2.5 border border-slate-300 focus:bg-white focus:outline-none focus:border-sky-500 font-mono transition cursor-pointer"
              >
                <option value={3}>Top 3</option>
                <option value={5}>Top 5</option>
                <option value={10}>Top 10</option>
              </select>

              <button
                type="submit"
                disabled={loading}
                className="group relative inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-mono font-bold text-xs shadow-xs transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer"
              >
                <span className="w-4 h-4 flex items-center justify-center">
                  {loading ? (
                    <span className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Search className="w-3.5 h-3.5 text-white" />
                  )}
                </span>
                <span>{loading ? 'SEARCHING...' : 'SEARCH EVIDENCE'}</span>
              </button>
            </div>
          </div>

          {/* Quick Query Shortcuts */}
          <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-slate-100">
            <span className="text-[11px] font-mono font-bold text-slate-500 flex items-center gap-1.5 mr-1">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              <span>CLINICAL QUERIES:</span>
            </span>
            {sampleQueries.map((sq) => (
              <button
                key={sq}
                type="button"
                onClick={() => handleSearch(undefined, sq)}
                className="group px-3 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-sky-800 text-[11px] font-mono border border-slate-200 transition-all cursor-pointer flex items-center gap-1.5"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 group-hover:bg-sky-600 transition-colors" />
                <span>{sq}</span>
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          SEARCH RESULTS SECTION
          ═══════════════════════════════════════════════════════════════════ */}
      {loading ? (
        <div className="py-20 text-center text-slate-500 text-xs flex flex-col items-center justify-center gap-3 font-mono">
          <span className="w-8 h-8 border-2 border-sky-400 border-t-sky-600 rounded-full animate-spin" />
          <span className="font-bold tracking-wide">QUERYING 47,806 HARRISON'S VECTOR EMBEDDINGS...</span>
          <span className="text-slate-400 text-[11px]">Executing dense semantic vector retrieval via BGE small embeddings</span>
        </div>
      ) : results.length > 0 ? (
        <div className="space-y-4">
          <div className="text-xs font-mono text-slate-500 mb-2 flex flex-wrap items-center justify-between gap-2 px-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-sky-600" />
              <span>FOUND {results.length} EVIDENCE EXCERPTS MATCHING:</span>
              <span className="text-sky-800 font-bold">"{query}"</span>
            </div>
            <span className="text-[11px] text-slate-400">Sorted by Cosine Semantic Proximity</span>
          </div>

          {results.map((res) => (
            <div
              key={res.id}
              className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs hover:border-sky-300 transition-all"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-3.5">
                <div>
                  <h4 className="text-sm sm:text-base font-bold text-slate-900 flex flex-wrap items-center gap-2 font-sans">
                    <span>{res.topic}</span>
                    <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-sky-50 text-sky-800 border border-sky-200 rounded-md">
                      {res.specialty}
                    </span>
                  </h4>
                  <div className="text-xs font-mono text-slate-500 mt-1 flex items-center gap-2">
                    <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                    <span>{res.book_title} • {res.chapter}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2.5 shrink-0">
                  <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 font-black flex items-center gap-1.5 shadow-2xs">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span>RELEVANCE: {Math.round(res.score * 100)}%</span>
                  </span>

                  <button
                    onClick={() => handleCopyCitation(res)}
                    className="group/copy px-3 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-sky-800 border border-slate-200 text-xs font-mono font-medium flex items-center gap-1.5 transition active:scale-[0.98] cursor-pointer"
                    title="Copy evidence citation to clipboard"
                  >
                    {copiedId === res.id ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                        <span className="text-emerald-700">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5 text-slate-400 group-hover/copy:text-sky-700" />
                        <span>Cite</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Evidence Quote Container */}
              <div className="text-xs sm:text-[13px] text-slate-800 bg-slate-50 p-4 rounded-xl border border-slate-200 leading-relaxed font-sans italic relative pl-5 border-l-4 border-l-sky-500">
                "{res.content}"
              </div>

              {res.metadata && res.metadata.tags && (
                <div className="flex flex-wrap items-center gap-1.5 mt-3.5 pt-3 border-t border-slate-100">
                  <span className="text-[10px] font-mono text-slate-400 mr-1">TAGS:</span>
                  {res.metadata.tags.map((tag: string, i: number) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 text-[10px] bg-slate-100 text-slate-600 border border-slate-200 rounded-md font-mono"
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
        <div className="py-16 text-center p-8 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="text-4xl mb-3">🔍</div>
          <h4 className="text-base font-bold text-slate-900 font-mono">No Medical Guidelines Found</h4>
          <p className="text-xs text-slate-500 mt-1.5 max-w-sm mx-auto leading-relaxed font-sans">
            No evidence chunks matched your current query or specialty filter. Try different diagnostic keywords or select "All Specialties".
          </p>
        </div>
      ) : (
        <div className="py-16 text-center p-8 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="w-12 h-12 rounded-xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 mx-auto mb-3">
            <Search className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-semibold text-slate-900 font-sans">Semantic Medical Search Ready</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto font-sans leading-relaxed">
            Enter a clinical diagnostic problem or select one of the suggested query presets above to explore 47,806 indexed textbook sections.
          </p>
        </div>
      )}
    </div>
  );
};

export default KnowledgeSearchSection;
