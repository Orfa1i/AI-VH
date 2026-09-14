import React from 'react';
import type { BenchmarkCase } from '../../types';
import {
  Play,
  Loader2,
  Hospital,
  ClipboardCheck,
  Sparkles,
  Award,
  Activity,
  Volume2,
  VolumeX,
} from 'lucide-react';

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
  onOpenRLDataset?: () => void;
  onOpenPharmacy?: () => void;
  onOpenBenchmark?: () => void;
  onOpenInpatient?: () => void;
  isAudioMuted?: boolean;
  onToggleAudio?: () => void;
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
  onOpenRLDataset,
  onOpenPharmacy,
  onOpenBenchmark,
  onOpenInpatient,
  isAudioMuted = false,
  onToggleAudio,
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
      <div className="flex items-center gap-2.5">
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
                {c.id}: {c.name} ({c.chief_complaint.slice(0, 30)}...)
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={onRunSimulation}
          disabled={isRunning}
          className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-sky-500/25 flex items-center gap-1.5 cursor-pointer transition-all disabled:opacity-50"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-white" />
              <span>Simulating...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>Run Encounter</span>
            </>
          )}
        </button>

        {onOpenConsult && (
          <button
            onClick={onOpenConsult}
            className="px-3 py-2 rounded-xl bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-700/70 text-emerald-300 text-xs font-bold shadow-lg shadow-emerald-900/30 flex items-center gap-1 cursor-pointer transition-all"
          >
            <span>🩺</span>
            <span>IM Consult</span>
          </button>
        )}

        {onOpenPharmacy && (
          <button
            onClick={onOpenPharmacy}
            className="px-3 py-2 rounded-xl bg-teal-950/80 hover:bg-teal-900 border border-teal-700/70 text-teal-300 text-xs font-bold shadow-lg shadow-teal-900/30 flex items-center gap-1 cursor-pointer transition-all"
          >
            <span>💊</span>
            <span>Pharmacy</span>
          </button>
        )}

        {onOpenInpatient && (
          <button
            onClick={onOpenInpatient}
            className="px-3 py-2 rounded-xl bg-sky-950/80 hover:bg-sky-900 border border-sky-700/70 text-sky-300 text-xs font-bold shadow-lg shadow-sky-900/30 flex items-center gap-1 cursor-pointer transition-all"
          >
            <Activity className="w-3.5 h-3.5 text-sky-400" />
            <span>Telemetry</span>
          </button>
        )}

        {onOpenBenchmark && (
          <button
            onClick={onOpenBenchmark}
            className="px-3 py-2 rounded-xl bg-purple-950/80 hover:bg-purple-900 border border-purple-700/70 text-purple-300 text-xs font-bold shadow-lg shadow-purple-900/30 flex items-center gap-1 cursor-pointer transition-all"
          >
            <Award className="w-3.5 h-3.5 text-purple-400" />
            <span>Policy Benchmark</span>
          </button>
        )}

        {onOpenRLDataset && (
          <button
            onClick={onOpenRLDataset}
            className="px-3 py-2 rounded-xl bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-700/70 text-indigo-300 text-xs font-bold shadow-lg shadow-indigo-900/30 flex items-center gap-1 cursor-pointer transition-all"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>RL Corpus</span>
          </button>
        )}

        {onToggleAudio && (
          <button
            onClick={onToggleAudio}
            title={isAudioMuted ? 'Unmute Agent Voices' : 'Mute Agent Voices'}
            className={`p-2 rounded-xl border text-xs font-semibold cursor-pointer transition-all ${
              isAudioMuted
                ? 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
                : 'bg-emerald-950/80 text-emerald-300 border-emerald-700/70 shadow-lg shadow-emerald-900/30'
            }`}
          >
            {isAudioMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
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
