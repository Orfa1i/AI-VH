import React, { useState } from 'react';
import {
  Activity,
  CheckCircle2,
  Clock,
  ExternalLink,
  MapPin,
  ShieldCheck,
  User,
} from 'lucide-react';
import type { BenchmarkCase, HospitalEvent } from '../../types';

export interface TrajectoryStageItem {
  id: string;
  stepNumber: number;
  label: string;
  title: string;
  department: string;
  stationId?: string;
  description: string;
  actionRequired: string;
  evidence: string;
  timestamp?: string;
  status: 'completed' | 'active' | 'upcoming';
}

export interface ActiveTrajectoryStepperProps {
  progress: number; // 0 to 100
  isRunning: boolean;
  currentCase?: BenchmarkCase | null;
  latestEvent?: HospitalEvent | null;
  activeDepartment?: string;
  doctorAction?: string;
  onSelectStage?: (stageId: string) => void;
  onOpenDepartmentStation?: (stationId: string) => void;
  className?: string;
}

export const ActiveTrajectoryStepper: React.FC<ActiveTrajectoryStepperProps> = ({
  progress,
  isRunning,
  currentCase,
  latestEvent,
  activeDepartment = 'RECEPTION',
  doctorAction = 'Reviewing Inpatient Charts',
  onSelectStage,
  onOpenDepartmentStation,
  className = '',
}) => {
  const [activeTooltipStageId, setActiveTooltipStageId] = useState<string | null>(null);

  // Normalize progress between 0 and 100
  const normalizedProgress = Math.min(100, Math.max(0, Math.round(progress)));

  // Derive stage status dynamically
  const isTriageComplete = normalizedProgress > 35 || (!isRunning && currentCase !== null && normalizedProgress >= 25);
  const isTriageActive = isRunning && (activeDepartment === 'RECEPTION' || activeDepartment === 'NURSE_STATION');

  const isExamComplete = normalizedProgress > 65;
  const isExamActive = isRunning && (activeDepartment.includes('DOCTOR') || activeDepartment.includes('EXAMINATION'));

  const isWorkupComplete = normalizedProgress > 85;
  const isWorkupActive = isRunning && (activeDepartment === 'LABORATORY' || activeDepartment === 'RADIOLOGY' || activeDepartment === 'PHARMACY');

  const isDischargeComplete = normalizedProgress >= 100;
  const isDischargeActive = isRunning && (normalizedProgress >= 90 || activeDepartment === 'DISCHARGE');

  const stages: TrajectoryStageItem[] = [
    {
      id: 'INTAKE',
      stepNumber: 1,
      label: 'GATEWAY',
      title: 'Clinical Intake & Triage',
      department: 'Triage & Nurse Station',
      stationId: 'NURSE_STATION',
      description: 'Patient identification, chief complaint intake, and objective vital sign telemetry recording.',
      actionRequired: 'Automated ESI Level calculation and baseline vitals acquisition.',
      evidence: currentCase ? `ESI Level ${currentCase.acuity === 'Critical' ? '1' : '2'} • Vitals Acquired` : 'Standby for triage queue admission',
      timestamp: currentCase ? 'T+00:00' : undefined,
      status: isTriageComplete && !isTriageActive ? 'completed' : isTriageActive || (currentCase && normalizedProgress < 35) ? 'active' : 'upcoming',
    },
    {
      id: 'EXAM',
      stepNumber: 2,
      label: 'ASSESSMENT',
      title: 'Attending Physician Examination',
      department: 'Internal Medicine Department',
      stationId: 'INTERNAL_MEDICINE',
      description: 'Differential diagnosis synthesis, physical findings analysis, and Harrison’s Principles RAG retrieval.',
      actionRequired: 'Attending physician evaluation and preliminary clinical orders.',
      evidence: doctorAction || 'Harrison’s Principles 21st Ed. Semantic Retrieval',
      timestamp: normalizedProgress >= 35 ? 'T+00:15' : undefined,
      status: isExamComplete && !isExamActive ? 'completed' : isExamActive || (normalizedProgress >= 35 && normalizedProgress < 65) ? 'active' : 'upcoming',
    },
    {
      id: 'WORKUP',
      stepNumber: 3,
      label: 'DIAGNOSTICS',
      title: 'Multidisciplinary Workup & Labs',
      department: 'Clinical Pathology & Imaging',
      stationId: 'LABORATORY',
      description: 'Serum biomarkers, high-sensitivity cardiac assays, diagnostic radiography, and pharmacy reconciliation.',
      actionRequired: 'Laboratory turn-around time validation and interaction verification.',
      evidence: 'STAT Troponin I, 12-Lead ECG & Chest Radiograph',
      timestamp: normalizedProgress >= 65 ? 'T+00:45' : undefined,
      status: isWorkupComplete && !isWorkupActive ? 'completed' : isWorkupActive || (normalizedProgress >= 65 && normalizedProgress < 95) ? 'active' : 'upcoming',
    },
    {
      id: 'DISCHARGE',
      stepNumber: 4,
      label: 'DISPOSITION',
      title: 'Discharge Hub & Disposition',
      department: 'Clinical Management Hub',
      stationId: 'DISCHARGE',
      description: 'Formal clinical report generation, evidence grounding verification, and discharge care planning.',
      actionRequired: 'Final clinical documentation sign-off and physician evaluation rubric routing.',
      evidence: isDischargeComplete ? 'Report Generated • 100% Evidence Grounded' : 'Disposition criteria pending diagnostics',
      timestamp: isDischargeComplete ? 'T+01:30' : undefined,
      status: isDischargeComplete ? 'completed' : isDischargeActive ? 'active' : 'upcoming',
    },
  ];

  const getStageHeaderSummary = () => {
    if (isDischargeComplete) return 'Discharge Gate Cleared • Clinical Report Finalized';
    if (isWorkupActive) return 'Diagnostic Workup In Progress • Biomarker & Imaging Analysis';
    if (isExamActive) return 'Attending Examination • Dr. Vance Harrison’s RAG Analysis';
    if (isTriageActive) return 'Triage Gateway • Objective Telemetry & Vitals Acquisition';
    if (isRunning) return 'Encounter Active • Routing Patient Trajectory...';
    return currentCase ? 'Patient Admitted • Clinical Trajectory Ready' : 'System Standby • Awaiting Patient Intake';
  };

  return (
    <section
      aria-label="Active Trajectory Sequence and State Flow"
      className={`w-full bg-white rounded-xl border border-slate-200/90 shadow-xs relative isolate transition-all duration-300 font-sans ${className}`}
    >
      {/* ── Top Micro-HUD Telemetry Header ── */}
      <div className="px-4 py-3 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-slate-50/80 via-white to-sky-50/30 rounded-t-xl">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-md bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 shadow-2xs">
            <Activity className="w-3.5 h-3.5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-slate-900 tracking-wider uppercase">
                ACTIVE TRAJECTORY SEQUENCE &amp; STATE FLOW
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-100 text-sky-800 border border-sky-200 tabular-nums">
                {normalizedProgress}% PROGRESS
              </span>
            </div>
          </div>
        </div>

        {/* Real-Time Live Ticker */}
        <div className="flex items-center gap-2 text-xs font-mono">
          {latestEvent ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-600 max-w-sm sm:max-w-md truncate">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping shrink-0" />
              <span className="text-[10px] text-slate-400 uppercase shrink-0">LATEST:</span>
              <span className="text-sky-800 font-semibold truncate text-[11px]">
                {latestEvent.summary || latestEvent.event_type}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
              <span>AWAITING SIMULATION STREAM</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Main Stepper Track & Process Flow ── */}
      <div className="p-4 sm:p-6">
        <div className="relative w-full">
          {/* Background Connecting Rail */}
          <div className="absolute top-5 left-6 right-6 h-1 bg-slate-100 rounded-full z-0 pointer-events-none">
            {/* Fluid Progress Line with SVG-Level Gradient Transitions */}
            <div
              className="h-full bg-gradient-to-r from-sky-500 via-indigo-500 to-emerald-500 rounded-full transition-all duration-700 ease-out shadow-[0_0_10px_rgba(14,165,233,0.3)]"
              style={{ width: `${normalizedProgress}%` }}
            />
          </div>

          {/* Stepper Nodes Grid: Responsive Horizontal Layout */}
          <div className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-2">
            {stages.map((stage) => {
              const isCompleted = stage.status === 'completed';
              const isActive = stage.status === 'active';
              const isTooltipOpen = activeTooltipStageId === stage.id;

              return (
                <div
                  key={stage.id}
                  className="flex flex-col items-center group relative cursor-pointer"
                  onMouseEnter={() => setActiveTooltipStageId(stage.id)}
                  onMouseLeave={() => setActiveTooltipStageId(null)}
                  onClick={() => {
                    onSelectStage?.(stage.id);
                    if (stage.stationId && onOpenDepartmentStation) {
                      onOpenDepartmentStation(stage.stationId);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      onSelectStage?.(stage.id);
                      if (stage.stationId && onOpenDepartmentStation) {
                        onOpenDepartmentStation(stage.stationId);
                      }
                    }
                  }}
                  aria-label={`${stage.title} - ${stage.status.toUpperCase()}`}
                >
                  {/* Node Icon Avatar with Adaptive Glow Physics */}
                  <div className="relative flex items-center justify-center mb-2.5">
                    {/* Active Halo Glow Animation */}
                    {isActive && (
                      <>
                        <span className="absolute -inset-2 rounded-full bg-sky-400/20 animate-ping pointer-events-none" />
                        <span className="absolute -inset-1 rounded-full bg-gradient-to-r from-sky-500/30 to-indigo-500/30 blur-xs pointer-events-none" />
                      </>
                    )}

                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-mono font-bold text-xs transition-all duration-300 relative z-10 ${
                        isCompleted
                          ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30 ring-4 ring-emerald-50 border border-emerald-400 scale-100 group-hover:scale-105'
                          : isActive
                          ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/40 ring-4 ring-sky-100 border-2 border-white scale-110'
                          : 'bg-white text-slate-400 border-2 border-slate-200 group-hover:border-slate-300 group-hover:text-slate-600'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-5 h-5 text-white stroke-[2.5]" />
                      ) : isActive ? (
                        <span className="flex items-center justify-center w-full h-full relative">
                          <span className="text-sm">{stage.stepNumber}</span>
                          <span className="absolute bottom-1 w-1 h-1 rounded-full bg-white animate-pulse" />
                        </span>
                      ) : (
                        <span>{stage.stepNumber}</span>
                      )}
                    </div>

                    {/* Active Patient Floating Pin when at this active node */}
                    {isActive && currentCase && (
                      <div className="absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap z-20 pointer-events-none animate-bounce">
                        <span className="px-2 py-0.5 rounded-full bg-slate-900 text-white text-[9px] font-mono font-semibold shadow-md flex items-center gap-1">
                          <User className="w-2.5 h-2.5 text-sky-400" />
                          <span>{currentCase.name.split(' ')[0]}</span>
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Stage Text & Status Badge */}
                  <div className="text-center px-1 w-full">
                    <div className="flex items-center justify-center gap-1 mb-0.5">
                      <span
                        className={`text-[9px] font-mono font-bold tracking-wider uppercase px-1.5 py-0.2 rounded ${
                          isCompleted
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : isActive
                            ? 'bg-sky-50 text-sky-700 border border-sky-300 font-semibold'
                            : 'bg-slate-50 text-slate-400 border border-slate-200'
                        }`}
                      >
                        {stage.label}
                      </span>
                      {stage.timestamp && (
                        <span className="text-[9px] font-mono text-slate-400">
                          {stage.timestamp}
                        </span>
                      )}
                    </div>

                    <h4
                      className={`text-xs font-semibold tracking-tight transition-colors line-clamp-1 ${
                        isCompleted
                          ? 'text-slate-900'
                          : isActive
                          ? 'text-sky-900 font-bold'
                          : 'text-slate-500'
                      }`}
                    >
                      {stage.title}
                    </h4>

                    <p className="text-[10px] text-slate-400 font-mono truncate mt-0.5 max-w-[150px] mx-auto">
                      {stage.department}
                    </p>
                  </div>

                  {/* ── Interactive Stage Detail Popover HUD ── */}
                  {isTooltipOpen && (
                    <div
                      className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 w-64 bg-slate-900 text-slate-100 rounded-xl p-3 shadow-xl border border-slate-700 text-left z-50 pointer-events-none animate-in fade-in zoom-in-95 duration-150"
                      role="tooltip"
                    >
                      {/* Popover Header */}
                      <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-800">
                        <div className="flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
                          <span className="font-mono text-[10px] text-sky-400 font-bold uppercase tracking-wider">
                            STAGE {stage.stepNumber}: {stage.label}
                          </span>
                        </div>
                        <span
                          className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded uppercase ${
                            isCompleted
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                              : isActive
                              ? 'bg-sky-950 text-sky-300 border border-sky-800'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {stage.status}
                        </span>
                      </div>

                      {/* Popover Body */}
                      <h5 className="text-xs font-bold text-white mb-1">{stage.title}</h5>
                      <p className="text-[11px] text-slate-300 leading-relaxed mb-2">
                        {stage.description}
                      </p>

                      <div className="mb-2 p-1.5 rounded bg-slate-800/80 border border-slate-700/60 text-[10px] text-slate-300">
                        <span className="text-sky-400 font-mono font-bold uppercase block mb-0.5">Clinical Protocol:</span>
                        <span>{stage.actionRequired}</span>
                      </div>

                      {/* Metadata Chips */}
                      <div className="space-y-1.5 text-[10px] font-mono bg-slate-950/70 p-2 rounded-lg border border-slate-800">
                        <div className="flex items-center justify-between text-slate-400">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-2.5 h-2.5 text-sky-400" />
                            <span>Station:</span>
                          </span>
                          <span className="text-slate-200 font-semibold truncate max-w-[130px]">
                            {stage.department}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-slate-400">
                          <span className="flex items-center gap-1">
                            <ShieldCheck className="w-2.5 h-2.5 text-emerald-400" />
                            <span>Evidence:</span>
                          </span>
                          <span className="text-slate-200 truncate max-w-[130px]">
                            {stage.evidence}
                          </span>
                        </div>
                        {stage.timestamp && (
                          <div className="flex items-center justify-between text-slate-400">
                            <span className="flex items-center gap-1">
                              <Clock className="w-2.5 h-2.5 text-amber-400" />
                              <span>Elapsed:</span>
                            </span>
                            <span className="text-amber-300 font-bold">
                              {stage.timestamp}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Click affordance indicator */}
                      <div className="mt-2 pt-1 border-t border-slate-800/80 flex items-center justify-between text-[9px] text-slate-400 font-mono">
                        <span>CLICK TO INSPECT STATION</span>
                        <ExternalLink className="w-2.5 h-2.5 text-slate-400" />
                      </div>

                      {/* Bottom Triangle Arrow */}
                      <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-x-4 border-x-transparent border-t-4 border-t-slate-900" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Metadata Telemetry & Clinical Alignment Footer ── */}
      <div className="px-4 py-2.5 bg-slate-50/90 border-t border-slate-200/80 rounded-b-xl flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-sky-500 animate-pulse" />
          <span className="text-[11px] font-mono text-slate-500 uppercase font-semibold">
            TRAJECTORY STATUS:
          </span>
          <span className="text-slate-800 font-medium text-xs">
            {getStageHeaderSummary()}
          </span>
        </div>

        <div className="flex items-center gap-3 font-mono text-[11px] text-slate-500">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">PATIENT ACUITY:</span>
            <span
              className={`font-bold px-1.5 py-0.2 rounded text-[10px] ${
                currentCase?.acuity === 'Critical'
                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              }`}
            >
              {currentCase?.acuity || 'Standard'}
            </span>
          </div>

          <span className="text-slate-300">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">PATIENT:</span>
            <span className="font-semibold text-slate-800">
              {currentCase ? `${currentCase.age}yo ${currentCase.sex}` : 'None'}
            </span>
          </div>

          <span className="text-slate-300">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">EVIDENCE:</span>
            <span className="font-semibold text-sky-700">100% GROUNDED</span>
          </div>
        </div>
      </div>
    </section>
  );
};
