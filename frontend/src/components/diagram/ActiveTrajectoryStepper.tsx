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
  progress?: number; // 0 to 100
  activeStep?: 1 | 2 | 3 | 4;
  isRunning?: boolean;
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
  activeStep,
  isRunning = false,
  currentCase,
  latestEvent,
  activeDepartment = 'RECEPTION',
  doctorAction = 'Reviewing Inpatient Radiographs & Lab Panels',
  onSelectStage,
  onOpenDepartmentStation,
  className = '',
}) => {
  const [activeTooltipStageId, setActiveTooltipStageId] = useState<string | null>(null);

  // Compute effective active step (1 to 4) dynamically
  const getDerivedStep = (): 1 | 2 | 3 | 4 => {
    if (activeStep !== undefined) return activeStep;
    if (currentCase) {
      const isDischarged = (currentCase as any).status === 'discharged' || (currentCase as any).admission_status === 'DISCHARGED';
      if (isDischarged) return 4;
    }
    if (isRunning) {
      if (activeDepartment === 'RECEPTION' || activeDepartment === 'NURSE_STATION') return 1;
      if (activeDepartment.includes('DOCTOR') || activeDepartment.includes('EXAMINATION') || activeDepartment === 'INTERNAL_MEDICINE') return 2;
      if (activeDepartment === 'LABORATORY' || activeDepartment === 'RADIOLOGY' || activeDepartment === 'PHARMACY' || activeDepartment === 'CASES') return 3;
      if (activeDepartment === 'DISCHARGE') return 4;
    }
    // If progress is provided explicitly
    if (progress !== undefined) {
      if (progress >= 95) return 4;
      if (progress >= 70) return 3;
      if (progress >= 40) return 2;
      return 1;
    }
    // Default for admitted patient in queue: Step 3 (Cases Area)
    return currentCase ? 3 : 1;
  };

  const currentStep = getDerivedStep();

  // Progress percentage mapped to active step
  const effectiveProgress = progress !== undefined ? Math.round(progress) : (
    currentStep === 4 ? 100 : currentStep === 3 ? 75 : currentStep === 2 ? 50 : 25
  );

  const getStageStatus = (step: number): 'completed' | 'active' | 'upcoming' => {
    if (currentStep === 4) return 'completed';
    if (step < currentStep) return 'completed';
    if (step === currentStep) return 'active';
    return 'upcoming';
  };

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
      timestamp: 'T+00:00',
      status: getStageStatus(1),
    },
    {
      id: 'EXAM',
      stepNumber: 2,
      label: 'ASSESSMENT',
      title: 'Attending Examination',
      department: 'Internal Medicine Dept.',
      stationId: 'INTERNAL_MEDICINE',
      description: 'Differential diagnosis synthesis, physical findings analysis, and Harrison’s Principles RAG retrieval.',
      actionRequired: 'Attending physician evaluation and preliminary clinical orders.',
      evidence: doctorAction || 'Harrison’s Principles 21st Ed. Semantic Retrieval',
      timestamp: 'T+00:15',
      status: getStageStatus(2),
    },
    {
      id: 'WORKUP',
      stepNumber: 3,
      label: 'DIAGNOSTICS',
      title: 'Multidisciplinary Labs',
      department: 'Clinical Pathology & Imaging',
      stationId: 'LABORATORY',
      description: 'Serum biomarkers, high-sensitivity cardiac assays, diagnostic radiography, and pharmacy reconciliation.',
      actionRequired: 'Laboratory turn-around time validation and interaction verification.',
      evidence: 'STAT Gram Stain, Procalcitonin & Ceftriaxone Protocol',
      timestamp: 'T+00:45',
      status: getStageStatus(3),
    },
    {
      id: 'DISCHARGE',
      stepNumber: 4,
      label: 'DISPOSITION',
      title: 'Discharge Hub',
      department: 'Clinical Management Hub',
      stationId: 'DISCHARGE',
      description: 'Formal clinical report generation, evidence grounding verification, and discharge care planning.',
      actionRequired: 'Final clinical documentation sign-off and physician evaluation rubric routing.',
      evidence: currentStep === 4 ? 'Report Generated • 100% Evidence Grounded' : 'Disposition criteria pending diagnostics',
      timestamp: 'T+01:30',
      status: getStageStatus(4),
    },
  ];

  const getStageHeaderSummary = () => {
    if (currentStep === 4) return 'Discharge Gate Cleared • Clinical Report Finalized';
    if (currentStep === 3) return 'Cases Area • Multidisciplinary Labs & Pathology In Progress';
    if (currentStep === 2) return 'Attending Examination • Dr. Vance Harrison’s RAG Analysis';
    return currentCase ? 'Intake Gateway • Patient Triage Recorded' : 'System Standby • Awaiting Patient Intake';
  };

  const latestAuditText = latestEvent?.summary || (
    currentCase
      ? `Nurse Sarah Jenkins, RN brought patient ${currentCase.name} into Stepdown Unit (Bed 04-B)`
      : 'Telemetry event bus listening for hospital agent actions...'
  );

  return (
    <section
      aria-label="Active Trajectory Sequence and State Flow"
      className={`w-full bg-white rounded-xl border border-slate-200/90 shadow-2xs relative isolate transition-all duration-300 font-sans ${className}`}
    >
      {/* ── Top Micro-HUD Telemetry Header ── */}
      <div className="px-4 py-3 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-slate-50/90 via-white to-teal-50/20 rounded-t-xl">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-[#0d6e60] shadow-2xs">
            <Activity className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-slate-900 tracking-wider uppercase">
                ACTIVE TRAJECTORY SEQUENCE &amp; STATE FLOW
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-teal-50 text-[#0d6e60] border border-teal-200 tabular-nums">
                {effectiveProgress}% PROGRESS
              </span>
            </div>
          </div>
        </div>

        {/* Real-Time Live Audit Ticker */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100/80 border border-slate-200 text-slate-700 max-w-sm sm:max-w-xl truncate">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
            <span className="text-[10px] text-slate-500 font-bold uppercase shrink-0">LATEST AUDIT:</span>
            <span className="text-slate-800 font-medium truncate text-[11px]">
              {latestAuditText}
            </span>
          </div>
        </div>
      </div>

      {/* ── Main Stepper Track & Process Flow ── */}
      <div className="p-4 sm:p-6">
        <div className="relative w-full">
          {/* Background Connecting Rail */}
          <div className="absolute top-5 left-10 right-10 h-1.5 bg-slate-200 rounded-full z-0 pointer-events-none">
            {/* Deep Clinical Teal Filled Progress Line */}
            <div
              className="h-full bg-[#0d6e60] rounded-full transition-all duration-700 ease-out shadow-[0_0_8px_rgba(13,110,96,0.35)]"
              style={{ width: `${effectiveProgress}%` }}
            />
          </div>

          {/* Stepper Nodes Grid: Responsive 4-Column Layout */}
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
                  {/* Node Circle with Deep Teal Aesthetic */}
                  <div className="relative flex items-center justify-center mb-2.5">
                    {/* Active Halo Glow Animation */}
                    {isActive && (
                      <>
                        <span className="absolute -inset-2 rounded-full bg-teal-400/25 animate-ping pointer-events-none" />
                        <span className="absolute -inset-1 rounded-full bg-[#0d6e60]/20 blur-xs pointer-events-none" />
                      </>
                    )}

                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-mono font-bold text-xs transition-all duration-300 relative z-10 ${
                        isCompleted
                          ? 'bg-[#0d6e60] text-white shadow-md shadow-teal-900/25 border-2 border-[#0d6e60] scale-100 group-hover:scale-105'
                          : isActive
                          ? 'bg-[#0d6e60] text-white shadow-lg shadow-teal-900/35 ring-4 ring-teal-100 border-2 border-white scale-110'
                          : 'bg-white text-slate-400 border-2 border-slate-300 group-hover:border-slate-400 group-hover:text-slate-600'
                      }`}
                    >
                      {isCompleted || isActive ? (
                        <CheckCircle2 className="w-5 h-5 text-white stroke-[2.5]" />
                      ) : (
                        <span>{stage.stepNumber}</span>
                      )}
                    </div>

                    {/* Active Patient Floating Pin when at this active node */}
                    {isActive && currentCase && (
                      <div className="absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap z-20 pointer-events-none animate-bounce">
                        <span className="px-2 py-0.5 rounded-full bg-slate-900 text-white text-[9px] font-mono font-semibold shadow-md flex items-center gap-1 border border-slate-700">
                          <User className="w-2.5 h-2.5 text-teal-400" />
                          <span>{currentCase.name}</span>
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Stage Text & Status Badge matching Screenshot */}
                  <div className="text-center px-1 w-full">
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                      <span className="text-[9px] font-mono font-bold tracking-wider uppercase px-2 py-0.5 rounded bg-teal-50 text-[#0d6e60] border border-teal-200">
                        {stage.label}
                      </span>
                      {stage.timestamp && (
                        <span className="text-[10px] font-mono text-slate-400">
                          {stage.timestamp}
                        </span>
                      )}
                    </div>

                    <h4
                      className={`text-xs font-bold tracking-tight transition-colors line-clamp-1 ${
                        isCompleted || isActive ? 'text-slate-900 font-bold' : 'text-slate-500'
                      }`}
                    >
                      {stage.title}
                    </h4>

                    <p className="text-[11px] text-slate-500 truncate mt-0.5 max-w-[170px] mx-auto">
                      {stage.department}
                    </p>
                  </div>

                  {/* ── Interactive Stage Detail Popover HUD ── */}
                  {isTooltipOpen && (
                    <div
                      className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 w-64 bg-slate-900 text-slate-100 rounded-xl p-3 shadow-xl border border-slate-700 text-left z-50 pointer-events-none animate-in fade-in zoom-in-95 duration-150"
                      role="tooltip"
                    >
                      <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-800">
                        <div className="flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
                          <span className="font-mono text-[10px] text-teal-400 font-bold uppercase tracking-wider">
                            STAGE {stage.stepNumber}: {stage.label}
                          </span>
                        </div>
                        <span
                          className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded uppercase ${
                            isCompleted
                              ? 'bg-teal-950 text-teal-300 border border-teal-800'
                              : isActive
                              ? 'bg-sky-950 text-sky-300 border border-sky-800'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {stage.status}
                        </span>
                      </div>

                      <h5 className="text-xs font-bold text-white mb-1">{stage.title}</h5>
                      <p className="text-[11px] text-slate-300 leading-relaxed mb-2">
                        {stage.description}
                      </p>

                      <div className="mb-2 p-1.5 rounded bg-slate-800/80 border border-slate-700/60 text-[10px] text-slate-300">
                        <span className="text-teal-400 font-mono font-bold uppercase block mb-0.5">Clinical Protocol:</span>
                        <span>{stage.actionRequired}</span>
                      </div>

                      <div className="space-y-1.5 text-[10px] font-mono bg-slate-950/70 p-2 rounded-lg border border-slate-800">
                        <div className="flex items-center justify-between text-slate-400">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-2.5 h-2.5 text-teal-400" />
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

                      <div className="mt-2 pt-1 border-t border-slate-800/80 flex items-center justify-between text-[9px] text-slate-400 font-mono">
                        <span>CLICK TO INSPECT STATION</span>
                        <ExternalLink className="w-2.5 h-2.5 text-slate-400" />
                      </div>

                      <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-x-4 border-x-transparent border-t-4 border-t-slate-900" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Metadata Telemetry & Clinical Alignment Footer (Matching Screenshot) ── */}
      <div className="px-4 py-2.5 bg-slate-50/90 border-t border-slate-200/80 rounded-b-xl flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[11px] font-mono text-slate-500 uppercase font-semibold">
            TRAJECTORY STATUS:
          </span>
          <span className="text-slate-900 font-medium text-xs">
            {getStageHeaderSummary()}
          </span>
        </div>

        <div className="flex items-center gap-3 font-mono text-[11px] text-slate-500">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">PATIENT ACUITY:</span>
            <span className="font-bold px-1.5 py-0.2 rounded text-[10px] bg-rose-50 text-rose-700 border border-rose-200">
              {currentCase?.acuity === 'Critical' ? 'CRITICAL' : 'URGENT'}
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
            <span className="text-slate-400">EVIDENCE REASONING:</span>
            <span className="font-semibold text-[#0d6e60]">100% GROUNDED</span>
          </div>

          <span className="text-slate-300">|</span>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">AUDIT SIGN-OFF:</span>
            <span className="font-semibold text-slate-800">M. Vance, MD</span>
          </div>
        </div>
      </div>
    </section>
  );
};
