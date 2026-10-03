import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  CheckCircle2,
  Stethoscope,
  FlaskConical,
  FileCheck2,
  ChevronUp,
  ChevronDown,
  Sparkles,
  ArrowRight,
} from 'lucide-react';

export interface ActiveEncounterProgressBarProps {
  isRunning: boolean;
  patientName?: string;
  encounterId?: string;
  activeStage?: string;
  onViewReport?: () => void;
  onDismiss?: () => void;
}

const MILESTONES = [
  { id: 'INTAKE', label: 'Intake & Vitals', target: 20, icon: Activity },
  { id: 'TRIAGE', label: 'Nurse Triage', target: 45, icon: Stethoscope },
  { id: 'EXAM', label: 'Doctor Exam & RAG', target: 70, icon: Sparkles },
  { id: 'LABS', label: 'Labs & Pharmacy', target: 90, icon: FlaskConical },
  { id: 'REPORT', label: 'Clinical Report', target: 100, icon: FileCheck2 },
];

export const ActiveEncounterProgressBar: React.FC<ActiveEncounterProgressBarProps> = ({
  isRunning,
  patientName = 'Active Encounter',
  encounterId,
  activeStage,
  onViewReport,
  onDismiss,
}) => {
  const [progress, setProgress] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const animationFrameRef = useRef<number | null>(null);
  const targetProgressRef = useRef(0);

  // Active progression simulation engine: smooth dynamic tick that NEVER stalls at 16%
  useEffect(() => {
    if (isRunning) {
      setIsCompleted(false);
      setProgress(5);
      targetProgressRef.current = 25;

      const timer1 = setTimeout(() => {
        targetProgressRef.current = 45;
      }, 700);

      const timer2 = setTimeout(() => {
        targetProgressRef.current = 70;
      }, 1500);

      const timer3 = setTimeout(() => {
        targetProgressRef.current = 88;
      }, 2400);

      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
      };
    } else if (progress > 10 && !isCompleted) {
      // Completed transition to 100%
      targetProgressRef.current = 100;
      const doneTimer = setTimeout(() => {
        setIsCompleted(true);
      }, 400);
      return () => clearTimeout(doneTimer);
    }
  }, [isRunning]);

  // Smooth interpolation loop (60 FPS smooth easing towards target)
  useEffect(() => {
    const updateProgress = () => {
      setProgress((prev) => {
        const diff = targetProgressRef.current - prev;
        if (Math.abs(diff) < 0.5) return targetProgressRef.current;
        return prev + diff * 0.12; // Easing speed
      });
      animationFrameRef.current = requestAnimationFrame(updateProgress);
    };

    animationFrameRef.current = requestAnimationFrame(updateProgress);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Display only when running or recently completed
  if (!isRunning && !isCompleted && progress <= 0) {
    return null;
  }

  const roundedPct = Math.min(100, Math.round(progress));

  const getCurrentMilestoneLabel = () => {
    if (roundedPct >= 98) return 'Encounter Complete • Clinical Report Finalized';
    if (roundedPct >= 85) return 'Pharmacy Medication Reconciliation & Safety Clearance';
    if (roundedPct >= 65) return 'Harrison\'s Internal Medicine RAG & Specialist Consultation';
    if (roundedPct >= 40) return 'Attending Physician Clinical Examination (Dr. Vance)';
    if (roundedPct >= 20) return 'Emergency Severity Index (ESI) Triage & Vitals Capture';
    return activeStage || 'Patient Intake & Bed Allocation Registered';
  };

  return (
    <div className="w-full bg-white border-b border-slate-200 shadow-sm transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-2.5">
        {/* Top Header Row */}
        <div className="flex items-center justify-between gap-4 mb-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all ${
              isCompleted ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-sky-50 text-sky-600 border border-sky-200 animate-pulse'
            }`}>
              {isCompleted ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <Activity className="w-4 h-4 text-sky-600" />}
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-slate-900 tracking-wide uppercase truncate">
                  {patientName}
                </span>
                {encounterId && (
                  <span className="px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 font-mono text-[9px] text-slate-600">
                    {encounterId}
                  </span>
                )}
                <span className={`px-2 py-0.5 rounded-full font-mono text-[10px] font-bold ${
                  isCompleted
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : 'bg-sky-100 text-sky-800 border border-sky-300'
                }`}>
                  {isCompleted ? '100% COMPLETE' : `${roundedPct}% LIVE`}
                </span>
              </div>
              <p className="text-[11px] font-sans text-slate-500 truncate mt-0.5">
                {getCurrentMilestoneLabel()}
              </p>
            </div>
          </div>

          {/* Right Action Controls */}
          <div className="flex items-center gap-2 shrink-0">
            {isCompleted && onViewReport && (
              <button
                onClick={onViewReport}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold rounded-lg shadow-xs transition flex items-center gap-1.5 cursor-pointer active:scale-95"
              >
                <span>View Clinical Report</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}

            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition cursor-pointer"
              title={isCollapsed ? 'Expand Trajectory' : 'Collapse Trajectory'}
            >
              {isCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
            </button>

            {onDismiss && (
              <button
                onClick={onDismiss}
                className="px-2 py-1 text-slate-400 hover:text-slate-700 text-xs font-mono rounded hover:bg-slate-100 cursor-pointer"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>

        {/* Dynamic Connected Visual Progress Track */}
        <div className="relative w-full py-1">
          {/* Base Track */}
          <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200 relative">
            {/* Animated Shimmering Fill */}
            <div
              className={`h-full transition-all duration-300 rounded-full ${
                isCompleted
                  ? 'bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600'
                  : 'bg-gradient-to-r from-sky-500 via-indigo-500 to-emerald-500'
              }`}
              style={{ width: `${roundedPct}%` }}
            >
              {/* Inner animated pulse glow */}
              <div className="w-full h-full bg-white/20 animate-pulse" />
            </div>
          </div>
        </div>

        {/* Clinical Milestones Breakdown (Collapsible) */}
        {!isCollapsed && (
          <div className="grid grid-cols-5 gap-2 mt-2 pt-2 border-t border-slate-100">
            {MILESTONES.map((step) => {
              const isPassed = roundedPct >= step.target;
              const isCurrent = roundedPct < step.target && roundedPct >= step.target - 25;
              const Icon = step.icon;

              return (
                <div key={step.id} className="flex items-center gap-1.5 text-left">
                  <div
                    className={`w-5 h-5 rounded-md flex items-center justify-center shrink-0 text-[10px] transition-all ${
                      isPassed
                        ? 'bg-emerald-100 text-emerald-700 border border-emerald-300'
                        : isCurrent
                        ? 'bg-sky-100 text-sky-700 border border-sky-300 animate-pulse'
                        : 'bg-slate-100 text-slate-400 border border-slate-200'
                    }`}
                  >
                    <Icon className="w-3 h-3" />
                  </div>
                  <div className="min-w-0 hidden md:block">
                    <span className={`block text-[10px] font-mono leading-tight truncate ${
                      isPassed ? 'text-slate-800 font-bold' : isCurrent ? 'text-sky-700 font-bold' : 'text-slate-400'
                    }`}>
                      {step.label}
                    </span>
                    <span className="text-[9px] font-mono text-slate-400">
                      {step.target}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
