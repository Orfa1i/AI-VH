import React from 'react';
import type { BenchmarkCase } from '../../types';
import { Play, Loader2, Hospital, ClipboardCheck } from 'lucide-react';

interface CaseSelectorProps {
  cases: BenchmarkCase[];
  selectedCaseId: string;
  onSelectCase: (caseId: string) => void;
  onRunSimulation: () => void;
  isRunning: boolean;
  activeView: 'HOSPITAL_3D' | 'PHYSICIAN_REVIEW';
  onChangeView: (view: 'HOSPITAL_3D' | 'PHYSICIAN_REVIEW') => void;
  reportsCount: number;
  onOpenConsult?: () => void;
}

export const CaseSelector: React.FC<CaseSelectorProps> = ({
  cases,
  selectedCaseId,
  onSelectCase,
  onRunSimulation,
  isRunning,
  activeView,
  onChangeView,
  reportsCount,
  onOpenConsult,
}) => {
  return (
    <header className="h-16 px-6 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 flex items-center justify-between z-30 shrink-0">
      {/* Brand & System Title */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white font-bold">
          🏥
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-black tracking-wider text-slate-100 uppercase">
              AI Virtual Hospital
            </span>
            <span className="px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/30 text-[10px] font-mono font-semibold">
              MEDGEMMA 4-BIT • RTX 4060
            </span>
          </div>
          <p className="text-[11px] text-slate-400">
            Autonomous Multi-Agent Clinical Simulation Platform
          </p>
        </div>
      </div>

      {/* Case Selector & Encounter Launcher */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-xl border border-slate-700 text-xs">
          <span className="text-slate-400 font-semibold">Case:</span>
          <select
            value={selectedCaseId}
            onChange={(e) => onSelectCase(e.target.value)}
            disabled={isRunning}
            className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer"
          >
            {cases.map((c) => (
              <option key={c.id} value={c.id} className="bg-slate-900 text-slate-200">
                {c.id}: {c.name} ({c.chief_complaint.slice(0, 35)}...)
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={onRunSimulation}
          disabled={isRunning}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-sky-500/25 flex items-center gap-2 cursor-pointer transition-all disabled:opacity-50"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-white" />
              <span>Simulating Clinical Encounter...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>Run Clinical Encounter</span>
            </>
          )}
        </button>

        {onOpenConsult && (
          <button
            onClick={onOpenConsult}
            className="px-3.5 py-2 rounded-xl bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-700/70 text-emerald-300 text-xs font-bold shadow-lg shadow-emerald-900/30 flex items-center gap-1.5 cursor-pointer transition-all"
          >
            <span>🩺</span>
            <span>Consult IM Specialist (RAG)</span>
          </button>
        )}
      </div>

      {/* View Switcher Tabs */}
      <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs font-semibold">
        <button
          onClick={() => onChangeView('HOSPITAL_3D')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
            activeView === 'HOSPITAL_3D'
              ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Hospital className="w-3.5 h-3.5" />
          <span>3D Virtual Hospital</span>
        </button>

        <button
          onClick={() => onChangeView('PHYSICIAN_REVIEW')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
            activeView === 'PHYSICIAN_REVIEW'
              ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ClipboardCheck className="w-3.5 h-3.5" />
          <span>Physician Review</span>
          {reportsCount > 0 && (
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                activeView === 'PHYSICIAN_REVIEW'
                  ? 'bg-white/20 text-white'
                  : 'bg-sky-500/20 text-sky-400 border border-sky-500/40'
              }`}
            >
              {reportsCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
};
