import React, { useState, useEffect } from 'react';
import type { DPOPreferencePair, DPOStatistics } from '../../types';
import {
  X,
  Sparkles,
  Download,
  ShieldAlert,
  BookOpen,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Cpu,
  Loader2,
  FileCode2,
} from 'lucide-react';

interface RLDatasetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const RLDatasetModal: React.FC<RLDatasetModalProps> = ({ isOpen, onClose }) => {
  const [pairs, setPairs] = useState<DPOPreferencePair[]>([]);
  const [stats, setStats] = useState<DPOStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'HUMAN' | 'BENCHMARK' | 'SAFETY'>('ALL');
  const [exporting, setExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);

  const fetchDataset = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/rl/dataset');
      if (res.ok) {
        const data = await res.json();
        setStats(data.statistics);
        setPairs(data.pairs || []);
      }
    } catch (err) {
      console.error('Failed to load DPO dataset:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchDataset();
    }
  }, [isOpen]);

  const handleExportJSONL = async () => {
    setExporting(true);
    setExportMessage(null);
    try {
      const res = await fetch('/api/rl/dataset/export', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setExportMessage(`Successfully exported ${data.exported_count} pairs to ${data.filepath}`);
        setTimeout(() => setExportMessage(null), 5000);
      }
    } catch (err) {
      setExportMessage('Failed to export dataset');
    } finally {
      setExporting(false);
    }
  };

  if (!isOpen) return null;

  const filteredPairs = pairs.filter((p) => {
    if (filter === 'HUMAN') return p.source === 'HUMAN_PHYSICIAN';
    if (filter === 'BENCHMARK') return p.source === 'CALIBRATED_BENCHMARK';
    if (filter === 'SAFETY') return p.is_safety_critical;
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-6xl max-h-[92vh] bg-slate-900/95 border border-slate-700/80 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100">
                  Phase 6: RL / Direct Preference Optimization (DPO) Corpus
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-purple-500/20 border border-purple-500/40 text-purple-300 text-[10px] font-mono font-bold">
                  HUGGINGFACE TRL COMPLIANT
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Reward-calibrated preference pairs (Prompt, Chosen, Rejected) synthesized from physician reviews & Harrison's ground truth.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleExportJSONL}
              disabled={exporting}
              className="px-3.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold shadow-lg shadow-purple-500/20 flex items-center gap-2 transition-all cursor-pointer disabled:opacity-50"
            >
              {exporting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Exporting...</span>
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>Export JSONL Dataset</span>
                </>
              )}
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Export Toast Notification */}
        {exportMessage && (
          <div className="px-6 py-2 bg-emerald-950/80 border-b border-emerald-800/80 text-emerald-300 text-xs flex items-center gap-2 font-mono">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{exportMessage}</span>
          </div>
        )}

        {/* Alignment Stats Bar */}
        {stats && (
          <div className="px-6 py-3 bg-slate-950/60 border-b border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3 shrink-0">
            <div className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center gap-3">
              <FileCode2 className="w-5 h-5 text-indigo-400" />
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-bold">Total Preference Pairs</p>
                <p className="text-base font-black text-slate-100 font-mono">{stats.total_pairs}</p>
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center gap-3">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-bold">Avg Reward Margin (ΔR)</p>
                <p className="text-base font-black text-emerald-300 font-mono">+{stats.average_reward_margin.toFixed(2)}</p>
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center gap-3">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-bold">Safety-Critical Violations</p>
                <p className="text-base font-black text-rose-300 font-mono">{stats.safety_critical_count}</p>
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center gap-3">
              <Cpu className="w-5 h-5 text-purple-400" />
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-bold">Target Foundation Model</p>
                <p className="text-xs font-bold text-slate-200">Clinical AI 4-Bit (DPO)</p>
              </div>
            </div>
          </div>
        )}

        {/* Filter Navigation */}
        <div className="px-6 py-2.5 bg-slate-900/50 border-b border-slate-800 flex items-center justify-between text-xs shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-medium mr-1 text-[11px]">Filter Pairs:</span>
            {(['ALL', 'HUMAN', 'BENCHMARK', 'SAFETY'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setFilter(mode)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  filter === mode
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                    : 'bg-slate-800/80 text-slate-400 hover:text-slate-200'
                }`}
              >
                {mode === 'ALL' && 'All Pairs'}
                {mode === 'HUMAN' && `Physician Reviews (${stats?.human_reviews_count || 0})`}
                {mode === 'BENCHMARK' && `Benchmark Calibrations (${stats?.benchmark_calibrations_count || 0})`}
                {mode === 'SAFETY' && `Safety Critical (${stats?.safety_critical_count || 0})`}
              </button>
            ))}
          </div>

          <span className="text-slate-400 text-[11px] font-mono">
            Showing {filteredPairs.length} of {pairs.length} training pairs
          </span>
        </div>

        {/* Scrollable Corpus List */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {loading ? (
            <div className="h-48 flex items-center justify-center gap-2 text-slate-400 text-xs">
              <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
              <span>Compiling DPO preference dataset...</span>
            </div>
          ) : filteredPairs.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs">
              No preference pairs match this filter criteria.
            </div>
          ) : (
            filteredPairs.map((pair) => (
              <div
                key={pair.id}
                className="rounded-xl border border-slate-800 bg-slate-950/70 overflow-hidden shadow-lg"
              >
                {/* Pair Header Banner */}
                <div className="px-4 py-2.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-indigo-950 border border-indigo-700/60 text-indigo-300 text-[10px] font-mono font-bold">
                      {pair.id}
                    </span>
                    <span className="text-xs font-bold text-slate-200">
                      {pair.case_id}
                    </span>
                    <span className="text-slate-400 text-xs">•</span>
                    <span className="text-xs text-slate-400 font-mono">
                      {pair.source === 'CALIBRATED_BENCHMARK' ? 'Calibrated Harrison Benchmark' : 'Human Physician Evaluation'}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {pair.is_safety_critical && (
                      <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px] font-semibold flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3" />
                        <span>Safety Critical</span>
                      </span>
                    )}
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-300 text-[11px] font-mono font-bold">
                      ΔR: +{pair.reward_margin.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Prompt Vignette */}
                <div className="px-4 py-3 bg-slate-900/40 border-b border-slate-800/80">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                    Clinical Scenario & History Prompt:
                  </p>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-line">
                    {pair.prompt}
                  </p>
                </div>

                {/* Side-by-Side Chosen vs Rejected Response */}
                <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-800">
                  {/* CHOSEN RESPONSE */}
                  <div className="p-4 bg-emerald-950/10">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-xs">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>CHOSEN (Aligned / Guideline-Adherent)</span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-emerald-900/60 border border-emerald-600 text-emerald-200 text-[10px] font-mono font-bold">
                        Reward: +{pair.reward_chosen.toFixed(2)}
                      </span>
                    </div>
                    <div className="text-xs text-slate-200 whitespace-pre-line font-sans leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-emerald-900/40">
                      {pair.chosen}
                    </div>
                  </div>

                  {/* REJECTED RESPONSE */}
                  <div className="p-4 bg-rose-950/10">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5 text-rose-400 font-bold text-xs">
                        <XCircle className="w-4 h-4" />
                        <span>REJECTED (Suboptimal / Contraindicated)</span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-rose-900/60 border border-rose-600 text-rose-200 text-[10px] font-mono font-bold">
                        Reward: {pair.reward_rejected.toFixed(2)}
                      </span>
                    </div>
                    <div className="text-xs text-slate-300 whitespace-pre-line font-sans leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-rose-900/40">
                      {pair.rejected}
                    </div>
                  </div>
                </div>

                {/* Evidence Citations Footer */}
                {pair.harrison_citations && pair.harrison_citations.length > 0 && (
                  <div className="px-4 py-2 bg-slate-950 border-t border-slate-800 flex items-center gap-2 flex-wrap text-[11px]">
                    <span className="text-slate-400 flex items-center gap-1 font-semibold">
                      <BookOpen className="w-3.5 h-3.5 text-sky-400" />
                      <span>Harrison's Textbook Grounding:</span>
                    </span>
                    {pair.harrison_citations.map((cite, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-sky-300 text-[10px]"
                      >
                        {cite}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
