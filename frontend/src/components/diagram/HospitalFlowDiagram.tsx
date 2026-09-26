import React, { useState } from 'react';
import type { BenchmarkCase, HospitalEvent, VitalSigns } from '../../types';
import drMarcusPhoto from '../../assets/dr_marcus_vance.jpg';
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  Clock,
  DoorOpen,
  FileText,
  HeartPulse,
  Play,
  RefreshCw,
  Stethoscope,
  Sparkles,
  Layers,
  Building2,
  User
} from 'lucide-react';

interface HospitalFlowDiagramProps {
  cases: BenchmarkCase[];
  selectedCaseId: string;
  onSelectCase: (caseId: string) => void;
  onRunSimulation: () => void;
  isRunning: boolean;
  activeDepartment: string;
  doctorAction: string;
  events: HospitalEvent[];
  activeVitals: VitalSigns | null;
  onOpenConsult: () => void;
  onOpenDepartmentStation?: (stationId: string) => void;
  onToggleTo3D?: () => void;
}

export const HospitalFlowDiagram: React.FC<HospitalFlowDiagramProps> = ({
  cases,
  selectedCaseId,
  onSelectCase,
  onRunSimulation,
  isRunning,
  activeDepartment,
  doctorAction,
  events,
  activeVitals,
  onOpenConsult,
  onOpenDepartmentStation,
  onToggleTo3D,
}) => {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // Identify current selected case
  const currentCase = cases.find((c) => c.id === selectedCaseId) || cases[0];

  // Latest event summary
  const latestEvent = events.length > 0 ? events[events.length - 1] : null;

  // Determine stage active states based on latest events / simulation state
  const isTriageActive = isRunning && (activeDepartment === 'RECEPTION' || activeDepartment === 'NURSE_STATION');
  const isDoctorActive = isRunning && (activeDepartment.includes('DOCTOR') || activeDepartment.includes('EXAMINATION'));
  const isLabActive = isRunning && activeDepartment === 'LABORATORY';
  const isDischargeActive = events.some((e) => e.event_type === 'CLINICAL_REPORT_GENERATED' || e.event_type === 'TREATMENT_ORDERED');

  // Dynamic patient trajectory position percentage (0% to 100%)
  const getPatientProgress = () => {
    if (isDischargeActive) return 96;
    if (isLabActive) return 65;
    if (isDoctorActive) return 40;
    if (isTriageActive) return 14;
    if (isRunning) return 28;
    return 6;
  };

  const patientProgress = getPatientProgress();

  const getStageDescription = () => {
    if (isDischargeActive) return 'Discharge Gate Cleared & Disposition Finalized';
    if (isLabActive) return 'Clinical Laboratory Biomarker Analysis';
    if (isDoctorActive) return 'Attending Physician Examination (Dr. Marcus Vance)';
    if (isTriageActive) return 'Nurse Triage & Objective Vital Telemetry Capture';
    if (isRunning) return 'Routing to Assigned Clinical Station...';
    return 'Patient Admitted & Queued in Clinical Pathway';
  };

  // Safe fallback vital values
  const hr = activeVitals?.heart_rate ?? 78;
  const sys = activeVitals?.systolic_bp ?? 124;
  const dia = activeVitals?.diastolic_bp ?? 82;
  const map = Math.round((2 * dia + sys) / 3);
  const spo2 = activeVitals?.spo2_percent ?? 98;
  const rr = activeVitals?.respiratory_rate ?? 16;
  const temp = activeVitals?.temperature_c ?? 37.1;

  return (
    <div className="w-full h-full flex flex-col bg-slate-950 text-slate-100 overflow-y-auto p-4 md:p-6 select-none relative isolate telemetry-grid">
      {/* ═══════════════════════════════════════════════════════════════════
          TOP ACTION BAR & DIAGRAM CONTROLS
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="w-full flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800/80 mb-5 z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-inner">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm md:text-base font-bold text-slate-100 tracking-wide font-headline-sm">
                CLINICAL PATHWAY & ENCOUNTER TRAJECTORY
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-sky-950/80 text-sky-400 border border-sky-800/60 font-semibold">
                2D SCHEMATIC
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Admission Triage &rarr; Attending Examination &rarr; Active Cases Disposition &rarr; Discharge Hub
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          {onToggleTo3D && (
            <button
              onClick={onToggleTo3D}
              className="px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-sky-300 text-xs font-mono font-medium border border-slate-700/80 flex items-center gap-1.5 transition cursor-pointer"
              title="Switch to 3D Spatial World"
            >
              <Building2 className="w-3.5 h-3.5 text-sky-400" />
              <span>3D SIMULATION</span>
            </button>
          )}

          <button
            onClick={onRunSimulation}
            disabled={isRunning}
            className={`px-4 py-1.5 rounded text-xs font-mono font-bold flex items-center gap-2 transition cursor-pointer shadow-sm ${
              isRunning
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse'
                : 'bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold shadow-sky-500/20 active:scale-95'
            }`}
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>TRAVERSAL IN PROGRESS...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>SIMULATE SELECTED CASE</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          LIVE HUD VITALS TELEMETRY & ECG RHYTHM STRIP (Stitch Screen 1)
          ═══════════════════════════════════════════════════════════════════ */}
      <section className="bg-slate-900/80 border border-slate-800 rounded hud-bracket p-3.5 mb-6 backdrop-blur-md z-10 shrink-0">
        <div className="flex flex-col xl:flex-row items-stretch xl:items-center justify-between gap-4">
          {/* Patient Quick Info */}
          <div className="flex items-center gap-4 border-b xl:border-b-0 xl:border-r border-slate-800/80 pb-3 xl:pb-0 pr-0 xl:pr-5 shrink-0">
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-rose-950/60 text-rose-400 border border-rose-800/60">
                  {currentCase ? `ESI LEVEL ${currentCase.acuity === 'Critical' ? '1' : '2'}` : 'READY'}
                </span>
                <span className="font-mono text-xs text-sky-400 font-semibold tracking-wider">
                  {currentCase?.id || 'PT-STANDBY'}
                </span>
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <h3 className="text-base font-bold text-slate-100 tracking-tight mt-0.5">
                {currentCase?.name || 'Awaiting Admission'}
              </h3>
              <div className="font-mono text-[11px] text-slate-400">
                {currentCase ? `${currentCase.age}yo ${currentCase.sex} • LOC: ${(currentCase as any).assigned_department || 'IM-STEPDOWN'}` : 'System ready for new admissions'}
              </div>
            </div>
          </div>

          {/* ECG Lead II Rhythm Strip */}
          <div className="flex-1 min-w-[220px] max-w-lg h-14 bg-slate-950/90 border border-slate-800 rounded relative overflow-hidden flex items-center px-3">
            <div className="absolute top-1 left-2 font-mono text-[9px] text-sky-400 tracking-widest flex items-center gap-2 z-10">
              <span className="font-semibold">LEAD II • ECG 25mm/s</span>
              <span className="text-emerald-400 font-semibold">NSR CONDUCTION</span>
            </div>
            <svg className="w-full h-8 stroke-sky-400" fill="none" preserveAspectRatio="none" viewBox="0 0 500 40">
              <path
                className="drop-shadow-[0_0_6px_rgba(56,189,248,0.7)]"
                d="M 0,20 L 40,20 L 50,18 L 55,20 L 70,20 L 75,5 L 82,36 L 88,14 L 92,20 L 110,20 L 125,16 L 140,20 L 180,20 L 190,18 L 195,20 L 210,20 L 215,5 L 222,36 L 228,14 L 232,20 L 250,20 L 265,16 L 280,20 L 320,20 L 330,18 L 335,20 L 350,20 L 355,5 L 362,36 L 368,14 L 372,20 L 390,20 L 405,16 L 420,20 L 460,20 L 470,18 L 475,20 L 500,20"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.8"
              />
            </svg>
            <div className="absolute inset-y-0 w-12 bg-gradient-to-r from-transparent via-sky-400/25 to-transparent ecg-scanner pointer-events-none" />
          </div>

          {/* Tabular Telemetry Grid */}
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 shrink-0">
            {/* HR */}
            <div className="bg-slate-950/60 border border-slate-800 p-2 rounded flex flex-col justify-between">
              <span className="font-mono text-[10px] text-slate-400">HEART RATE</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-lg font-bold text-emerald-400 leading-none tabular-nums">{hr}</span>
                <span className="font-mono text-[10px] text-slate-500">BPM</span>
              </div>
              <span className="font-mono text-[9px] text-emerald-400/80 mt-1">Normal Sinus</span>
            </div>

            {/* NIBP */}
            <div className="bg-slate-950/60 border border-slate-800 p-2 rounded flex flex-col justify-between">
              <span className="font-mono text-[10px] text-slate-400">NIBP SYS/DIA</span>
              <div className="flex items-baseline gap-0.5 mt-0.5">
                <span className="font-mono text-base font-bold text-slate-200 leading-none tabular-nums">{sys}/{dia}</span>
              </div>
              <span className="font-mono text-[9px] text-sky-400 mt-1">MAP: {map} mmHg</span>
            </div>

            {/* SPO2 */}
            <div className="bg-slate-950/60 border border-slate-800 p-2 rounded flex flex-col justify-between">
              <span className="font-mono text-[10px] text-slate-400">SPO2 %</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-lg font-bold text-sky-400 leading-none tabular-nums">{spo2}</span>
                <span className="font-mono text-[10px] text-slate-500">%</span>
              </div>
              <span className="font-mono text-[9px] text-slate-400 mt-1">Room Air</span>
            </div>

            {/* RESP */}
            <div className="bg-slate-950/60 border border-slate-800 p-2 rounded flex flex-col justify-between">
              <span className="font-mono text-[10px] text-slate-400">RESP RATE</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-lg font-bold text-slate-200 leading-none tabular-nums">{rr}</span>
                <span className="font-mono text-[10px] text-slate-500">bpm</span>
              </div>
              <span className="font-mono text-[9px] text-slate-400 mt-1">Eupneic</span>
            </div>

            {/* TEMP */}
            <div className="bg-slate-950/60 border border-slate-800 p-2 rounded flex flex-col justify-between">
              <span className="font-mono text-[10px] text-slate-400">TEMP CORE</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-lg font-bold text-slate-200 leading-none tabular-nums">{temp}</span>
                <span className="font-mono text-[10px] text-slate-500">°C</span>
              </div>
              <span className="font-mono text-[9px] text-emerald-400 mt-1">Normothermic</span>
            </div>

            {/* LACTATE */}
            <div className="bg-slate-950/60 border border-slate-800 p-2 rounded flex flex-col justify-between">
              <span className="font-mono text-[10px] text-slate-400">LACTATE</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-lg font-bold text-emerald-400 leading-none tabular-nums">1.2</span>
                <span className="font-mono text-[10px] text-slate-500">mmol</span>
              </div>
              <span className="font-mono text-[9px] text-emerald-400 mt-1">STAT Normal</span>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          MAIN FLOW DIAGRAM NODES GRID (4-STAGE CLINICAL TRAVERSAL)
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="w-full flex-1 flex flex-col gap-6 z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch relative">

          {/* ═══════════════════════════════════════════════════════════════════
              NODE 1: CLINICAL INTAKE & NURSE TRIAGE (Cols 1-3)
              ═══════════════════════════════════════════════════════════════════ */}
          <div
            onMouseEnter={() => setHoveredNode('INTAKE')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`lg:col-span-3 flex flex-col rounded bg-slate-900/90 border transition-all duration-200 shadow-lg hud-bracket overflow-hidden ${
              isTriageActive || hoveredNode === 'INTAKE'
                ? 'border-sky-500 ring-1 ring-sky-500/30'
                : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            {/* Header */}
            <div className="px-3.5 py-2.5 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-sky-400" />
                <span className="text-xs font-mono font-bold text-slate-200 tracking-wider uppercase">
                  1. INTAKE & TRIAGE
                </span>
              </div>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-sky-950/80 text-sky-400 border border-sky-800/60">
                ENTRY GATE
              </span>
            </div>

            {/* Body */}
            <div className="p-3.5 flex-1 flex flex-col justify-between gap-3">
              <div className="space-y-2.5">
                {/* Active Case Card */}
                <div className="p-3 rounded bg-slate-950/80 border border-slate-800/90">
                  <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono mb-1">
                    <span>ACTIVE ADMISSION</span>
                    <span className="text-sky-400 font-bold">{currentCase?.id || 'STANDBY'}</span>
                  </div>
                  <div className="font-semibold text-slate-100 text-xs">
                    {currentCase?.name || 'Awaiting Patient Admission'}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1 flex items-start gap-1.5 leading-relaxed">
                    <Clock className="w-3 h-3 text-sky-400 shrink-0 mt-0.5" />
                    <span className="text-slate-300 font-normal line-clamp-2">
                      {currentCase?.chief_complaint || 'Queue ready for manual admissions in Management Portal.'}
                    </span>
                  </div>
                </div>

                {/* Sub-Stations */}
                <div className="space-y-1.5">
                  <div
                    onClick={() => onOpenDepartmentStation?.('NURSE_STATION')}
                    className="p-2 rounded bg-slate-800/40 hover:bg-slate-800/80 border border-slate-800 flex items-center justify-between cursor-pointer transition text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <Stethoscope className="w-3.5 h-3.5 text-sky-400" />
                      <span className="text-slate-300 font-medium">Nurse Triage Station</span>
                    </div>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/80">
                      ONLINE
                    </span>
                  </div>

                  {activeVitals && (
                    <div className="p-2 rounded bg-emerald-950/20 border border-emerald-800/40 text-xs">
                      <div className="flex items-center gap-1.5 text-emerald-400 font-mono text-[10px] font-bold mb-1">
                        <HeartPulse className="w-3 h-3" />
                        <span>BASELINE VITALS CAPTURED</span>
                      </div>
                      <div className="grid grid-cols-2 gap-1 text-[10px] text-slate-400 font-mono">
                        <div>HR: <span className="text-slate-200">{activeVitals.heart_rate} bpm</span></div>
                        <div>BP: <span className="text-slate-200">{activeVitals.systolic_bp}/{activeVitals.diastolic_bp}</span></div>
                        <div>SpO2: <span className="text-slate-200">{activeVitals.spo2_percent}%</span></div>
                        <div>Temp: <span className="text-slate-200">{activeVitals.temperature_c}°C</span></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Trajectory Exit Arrow */}
              <div className="pt-2.5 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-slate-400 uppercase">Forwarded To:</span>
                <span className="flex items-center gap-1 text-sky-400 font-semibold text-[11px]">
                  Internal Med <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          </div>

          {/* ═══════════════════════════════════════════════════════════════════
              NODE 2: ATTENDING EXAMINATION & DR. MARCUS VANCE (Cols 4-7)
              ═══════════════════════════════════════════════════════════════════ */}
          <div
            onMouseEnter={() => setHoveredNode('DEPARTMENT')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`lg:col-span-4 flex flex-col rounded bg-slate-900/90 border transition-all duration-200 shadow-lg hud-bracket overflow-hidden ${
              isDoctorActive || hoveredNode === 'DEPARTMENT'
                ? 'border-indigo-500 ring-1 ring-indigo-500/30'
                : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            {/* Header */}
            <div className="px-3.5 py-2.5 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-400" />
                <span className="text-xs font-mono font-bold text-indigo-300 tracking-wider uppercase">
                  2. ATTENDING EXAMINATION
                </span>
              </div>
              <span className="px-2 py-0.2 rounded text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                ON DUTY
              </span>
            </div>

            {/* Doctor Profile Card */}
            <div className="p-3.5 flex-1 flex flex-col justify-between gap-3">
              <div className="p-3 rounded bg-slate-950/80 border border-indigo-900/40 shadow-inner flex items-center gap-3">
                <div className="relative shrink-0">
                  <img
                    src={drMarcusPhoto}
                    alt="Dr. Marcus Vance, MD, FACP"
                    className="w-14 h-14 rounded object-cover border border-sky-400/40 shadow-sm"
                  />
                  <span
                    className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-slate-950"
                    title="Active & Ready"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-100 truncate">
                      Dr. Marcus Vance
                    </h4>
                    <span className="text-[9px] font-mono text-sky-400 bg-sky-950/60 px-1 rounded border border-sky-800/40">
                      MD, FACP
                    </span>
                  </div>
                  <p className="text-[11px] text-indigo-300 font-medium truncate">
                    Chief Attending Physician
                  </p>
                  <p className="text-[10px] text-slate-400 truncate">
                    Internal Medicine & Clinical Diagnostics
                  </p>
                  <div className="mt-1 flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                    <Sparkles className="w-2.5 h-2.5" />
                    <span>Clinical AI Aligned (RTX 4060)</span>
                  </div>
                </div>
              </div>

              {/* Real-Time Doctor Activity Status */}
              <div className="p-2 rounded bg-slate-950/60 border border-slate-800 text-xs">
                <div className="flex items-center justify-between mb-1 text-[9px] text-indigo-400 font-mono uppercase tracking-wider font-semibold">
                  <span>Current Physician Activity</span>
                  <Activity className="w-3 h-3 text-indigo-400 animate-pulse" />
                </div>
                <div className="font-mono text-xs text-slate-200 font-medium truncate">
                  {doctorAction || 'Evaluating Patient Case & Clinical Guidelines'}
                </div>
              </div>

              {/* Diagnostic Consult Action Button */}
              <button
                onClick={onOpenConsult}
                className={`w-full p-2 rounded border text-left transition flex items-center gap-2 cursor-pointer group ${
                  isDoctorActive || isLabActive
                    ? 'bg-sky-950/60 border-sky-500 shadow-sm shadow-sky-500/20'
                    : 'bg-slate-800/40 hover:bg-slate-800/80 border-slate-700'
                }`}
              >
                <FileText className="w-3.5 h-3.5 text-sky-400 group-hover:scale-110 transition-transform" />
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-semibold text-slate-200 truncate">Dr. Vance RAG Consult</div>
                  <div className="text-[9px] text-slate-400 font-mono">Harrison's Principles 21st Edition</div>
                </div>
              </button>

              {/* Trajectory Exit Arrow */}
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-slate-400 uppercase">Path Output:</span>
                <span className="flex items-center gap-1 text-indigo-300 font-semibold text-[11px]">
                  Cases Processing <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          </div>

          {/* ═══════════════════════════════════════════════════════════════════
              NODE 3: ACTIVE CASES PROCESSING AREA (Cols 8-10)
              ═══════════════════════════════════════════════════════════════════ */}
          <div
            onMouseEnter={() => setHoveredNode('CASES')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`lg:col-span-3 flex flex-col rounded bg-slate-900/90 border transition-all duration-200 shadow-lg hud-bracket overflow-hidden ${
              hoveredNode === 'CASES'
                ? 'border-sky-500 ring-1 ring-sky-500/30'
                : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            {/* Header */}
            <div className="px-3.5 py-2.5 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-sky-400" />
                <span className="text-xs font-mono font-bold text-sky-300 tracking-wider uppercase">
                  3. CASES AREA
                </span>
              </div>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-sky-950 text-sky-400 border border-sky-800/60">
                {cases.length} IN CENSUS
              </span>
            </div>

            {/* Cases Roster */}
            <div className="p-3 flex-1 flex flex-col justify-between gap-2.5">
              <div className="text-[10px] text-slate-400 font-mono mb-0.5 flex items-center justify-between">
                <span>SELECT CASE TO ROUTE:</span>
                <span className="text-slate-500">LIVE QUEUE</span>
              </div>

              <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                {cases.length === 0 ? (
                  <div className="p-4 rounded bg-slate-950/40 border border-dashed border-slate-800 text-center flex flex-col items-center justify-center">
                    <FileText className="w-5 h-5 text-slate-600 mb-1" />
                    <div className="text-xs font-semibold text-slate-300">No Patient Records Yet</div>
                    <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">
                      Admit real patients in Clinical Intake to route them through the hospital simulation.
                    </p>
                  </div>
                ) : (
                  cases.map((c) => {
                    const isSelected = c.id === selectedCaseId;
                    return (
                      <div
                        key={c.id}
                        onClick={() => onSelectCase(c.id)}
                        className={`p-2 rounded border text-xs cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-sky-950/60 border-sky-500 shadow-sm shadow-sky-500/10'
                            : 'bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-0.5">
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono text-[10px] font-bold text-sky-400">{c.id}</span>
                            <span className="font-semibold text-slate-200 text-xs truncate max-w-[110px]">{c.name}</span>
                          </div>
                          <span
                            className={`text-[9px] px-1 py-0.2 rounded font-mono font-bold uppercase ${
                              c.acuity === 'Critical'
                                ? 'bg-rose-950 text-rose-400 border border-rose-800'
                                : 'bg-amber-950 text-amber-400 border border-amber-800'
                            }`}
                          >
                            {c.acuity}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400 truncate">
                          {c.chief_complaint}
                        </p>
                        <div className="mt-1 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                          <span>{c.age}yo {c.sex}</span>
                          {isSelected && (
                            <span className="text-sky-400 font-semibold flex items-center gap-0.5">
                              SELECTED <ChevronRight className="w-2.5 h-2.5" />
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Trajectory Exit Arrow */}
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-slate-400 uppercase">Next Node:</span>
                <span className="flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                  Discharge & Exit <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          </div>

          {/* ═══════════════════════════════════════════════════════════════════
              NODE 4: PATIENT EXIT POINT & DISCHARGE HUB (Cols 11-12)
              ═══════════════════════════════════════════════════════════════════ */}
          <div
            onMouseEnter={() => setHoveredNode('EXIT')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`lg:col-span-2 flex flex-col rounded bg-slate-900/90 border transition-all duration-200 shadow-lg hud-bracket overflow-hidden ${
              isDischargeActive || hoveredNode === 'EXIT'
                ? 'border-emerald-500 ring-1 ring-emerald-500/30'
                : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            {/* Header */}
            <div className="px-3.5 py-2.5 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <DoorOpen className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-xs font-mono font-bold text-emerald-300 tracking-wider uppercase">
                  4. EXIT POINT
                </span>
              </div>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-800">
                FINAL HUB
              </span>
            </div>

            {/* Body */}
            <div className="p-3 flex-1 flex flex-col justify-between gap-2.5">
              <div className="space-y-2">
                <div className="p-2 rounded bg-slate-950/60 border border-emerald-900/30 text-center">
                  <div className="w-7 h-7 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto mb-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </div>
                  <div className="text-xs font-bold text-slate-200">Patient Cleared</div>
                  <div className="text-[10px] text-slate-400 mt-0.5 font-mono">Disposition Finalized</div>
                </div>

                <div className="space-y-1 text-xs">
                  <div className="p-1.5 rounded bg-slate-800/40 border border-slate-800 flex items-center justify-between text-[10px] font-mono">
                    <span className="text-slate-400">SAFETY:</span>
                    <span className="text-emerald-400 font-semibold">100% CLEARED</span>
                  </div>

                  <div className="p-1.5 rounded bg-slate-800/40 border border-slate-800 flex items-center justify-between text-[10px] font-mono">
                    <span className="text-slate-400">PLAN:</span>
                    <span className="text-sky-400 font-semibold">Rx GROUNDED</span>
                  </div>

                  <div className="p-1.5 rounded bg-slate-800/40 border border-slate-800 flex items-center justify-between text-[10px] font-mono">
                    <span className="text-slate-400">DISPOSITION:</span>
                    <span className="text-emerald-400 font-semibold">CLEARED FOR DISCHARGE</span>
                  </div>
                </div>
              </div>

              {/* Status Badge */}
              <div className="pt-2 border-t border-slate-800 text-center">
                <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  DISCHARGE READY
                </span>
              </div>
            </div>
          </div>

        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            DYNAMIC PATIENT TRAJECTORY PROGRESS LINE (SVG PULSE FLOW)
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="w-full bg-slate-900/80 rounded border border-slate-800 p-3.5 shadow-lg hud-bracket">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-sky-400" />
              <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
                ACTIVE TRAJECTORY SEQUENCE &amp; STATE FLOW
              </span>
            </div>
            {latestEvent && (
              <span className="text-[11px] text-slate-400 font-mono truncate max-w-md">
                LATEST: <span className="text-sky-300 font-semibold">{latestEvent.summary || latestEvent.event_type}</span>
              </span>
            )}
          </div>

          {/* Connected Progress Line with Animated Patient Avatar */}
          <div className="relative flex items-center justify-between w-full px-4 py-3 min-h-[64px]">
            {/* Connecting Track Line */}
            <div className="absolute left-8 right-8 top-1/2 -translate-y-1/2 h-1 bg-slate-800 rounded-full z-0 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-sky-400 via-indigo-400 to-emerald-400 transition-all duration-1000 ease-out"
                style={{ width: `${patientProgress}%` }}
              />
            </div>

            {/* Dynamic Animated Patient Node */}
            <div
              className="absolute top-1/2 -translate-y-1/2 z-20 transition-all duration-1000 ease-out pointer-events-none"
              style={{ left: `calc(${patientProgress}% - 14px)` }}
            >
              <div className="flex flex-col items-center">
                {/* Floating Patient Chip */}
                <div className="px-2 py-0.2 rounded bg-sky-400 text-slate-950 font-mono font-bold text-[9px] shadow-lg shadow-sky-400/40 whitespace-nowrap mb-1 flex items-center gap-1 animate-bounce">
                  <span>{currentCase?.name || 'Patient'}</span>
                  <span className="opacity-80">({patientProgress}%)</span>
                </div>
                {/* Pin Head */}
                <div className="relative">
                  <div className="w-6 h-6 rounded-full bg-sky-400 border-2 border-slate-950 shadow-md shadow-sky-400/50 flex items-center justify-center text-slate-950">
                    <User className="w-3.5 h-3.5 fill-slate-950" />
                  </div>
                  {isRunning && (
                    <span className="absolute -inset-1 rounded-full border border-sky-400 animate-ping" />
                  )}
                </div>
              </div>
            </div>

            {/* Step 1: Intake */}
            <div className="relative z-10 flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all shadow-md ${
                  isTriageActive || isDoctorActive || isDischargeActive
                    ? 'bg-sky-400 text-slate-950 ring-2 ring-sky-400/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
              >
                1
              </div>
              <span className="text-[10px] font-mono font-semibold text-slate-300 mt-1">INTAKE</span>
            </div>

            {/* Step 2: Attending */}
            <div className="relative z-10 flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all shadow-md ${
                  isDoctorActive || isDischargeActive
                    ? 'bg-indigo-500 text-white ring-2 ring-indigo-500/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
              >
                2
              </div>
              <span className="text-[10px] font-mono font-semibold text-slate-300 mt-1">DEPT &amp; DR. VANCE</span>
            </div>

            {/* Step 3: Cases Area */}
            <div className="relative z-10 flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all shadow-md ${
                  isDoctorActive || isDischargeActive
                    ? 'bg-sky-400 text-slate-950 ring-2 ring-sky-400/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
              >
                3
              </div>
              <span className="text-[10px] font-mono font-semibold text-slate-300 mt-1">CASES AREA</span>
            </div>

            {/* Step 4: Exit Point */}
            <div className="relative z-10 flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all shadow-md ${
                  isDischargeActive
                    ? 'bg-emerald-400 text-slate-950 ring-2 ring-emerald-400/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
              >
                4
              </div>
              <span className="text-[10px] font-mono font-semibold text-slate-300 mt-1">PATIENT EXIT</span>
            </div>
          </div>

          {/* Real-Time Location Banner */}
          <div className="mt-1 pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
              <span className="text-slate-400 font-mono text-[11px]">TRAJECTORY STATUS:</span>
              <span className="text-sky-300 font-semibold">{getStageDescription()}</span>
            </div>
            <div className="font-mono text-[10px] text-slate-500">
              ACUITY: <span className="text-slate-300">{currentCase?.acuity || 'Standard'}</span> | AGE: <span className="text-slate-300">{currentCase?.age}yo {currentCase?.sex}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
