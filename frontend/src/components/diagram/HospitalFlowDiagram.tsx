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
  Pill,
  Play,
  RefreshCw,
  Stethoscope,
  Sparkles,
  Layers,
  Building2
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
  onOpenPharmacy: () => void;
  onOpenTelemetry: () => void;
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
  onOpenPharmacy,
  onOpenTelemetry,
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
  const isPharmacyActive = isRunning && activeDepartment === 'PHARMACY';
  const isDischargeActive = events.some((e) => e.event_type === 'CLINICAL_REPORT_GENERATED' || e.event_type === 'TREATMENT_ORDERED');

  return (
    <div className="w-full h-full flex flex-col bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100 overflow-y-auto p-4 md:p-6 select-none relative isolate">
      {/* Background Subtle Grid Accent */}
      <div 
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(#38bdf8 1px, transparent 1px)`,
          backgroundSize: '24px 24px'
        }}
      />

      {/* Top Diagram Action & Metrics Bar */}
      <div className="w-full flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800/80 mb-6 z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-100 tracking-wide">
                Hospital Clinical Pathway & Flow Architecture
              </h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800">
                2D Process Model
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Clear clinical traversal from Patient Admission → Department & Doctor Examination → Active Cases → Exit / Discharge
            </p>
          </div>
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-3">
          {/* Run Encounter Simulation Trigger */}
          <button
            onClick={onRunSimulation}
            disabled={isRunning}
            className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition shadow-lg cursor-pointer ${
              isRunning
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse'
                : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-cyan-500/20'
            }`}
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Simulating Clinical Traversal...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Simulate Selected Case Pathway</span>
              </>
            )}
          </button>

          {/* Switch to 3D Spatial View (Optional toggle) */}
          {onToggleTo3D && (
            <button
              onClick={onToggleTo3D}
              className="px-3 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-cyan-300 text-xs font-medium border border-slate-700/80 flex items-center gap-1.5 transition cursor-pointer"
              title="Switch to 3D Spatial World"
            >
              <Building2 className="w-3.5 h-3.5 text-cyan-400" />
              <span>3D Spatial View</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Flow Diagram Area */}
      <div className="flex-1 w-full max-w-7xl mx-auto flex flex-col gap-6 z-10">
        {/* Dynamic Trajectory SVG Path Connectors (Desktop Horizontal Flow) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch relative">
          
          {/* ═══════════════════════════════════════════════════════════════════
              NODE 1: PATIENT INTAKE & ADMISSION POINT (Cols 1-3)
              ═══════════════════════════════════════════════════════════════════ */}
          <div 
            onMouseEnter={() => setHoveredNode('INTAKE')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`lg:col-span-3 flex flex-col rounded-2xl bg-slate-900/90 border transition-all duration-300 shadow-xl overflow-hidden ${
              isTriageActive || hoveredNode === 'INTAKE'
                ? 'border-cyan-500/80 ring-2 ring-cyan-500/20 bg-slate-900'
                : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            {/* Header */}
            <div className="px-4 py-3 bg-slate-800/50 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-base">🚑</span>
                <span className="text-xs font-bold text-slate-200 tracking-wide uppercase">
                  1. Intake & Triage
                </span>
              </div>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                Entry Gate
              </span>
            </div>

            {/* Body */}
            <div className="p-4 flex-1 flex flex-col justify-between gap-4">
              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                    <span>Active Case Entry</span>
                    <span className="font-mono text-cyan-400">{currentCase?.id}</span>
                  </div>
                  <div className="font-semibold text-slate-200 text-sm">
                    {currentCase?.name || 'Incoming Patient'}
                  </div>
                  <div className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                    <Clock className="w-3 h-3 text-cyan-400" />
                    <span>Chief Complaint:</span>
                    <span className="text-slate-300 font-medium truncate">{currentCase?.chief_complaint}</span>
                  </div>
                </div>

                {/* Sub-Stations */}
                <div className="space-y-1.5">
                  <div 
                    onClick={() => onOpenDepartmentStation?.('NURSE_STATION')}
                    className="p-2.5 rounded-lg bg-slate-800/40 hover:bg-slate-800/80 border border-slate-800 flex items-center justify-between cursor-pointer transition"
                  >
                    <div className="flex items-center gap-2">
                      <Stethoscope className="w-3.5 h-3.5 text-cyan-400" />
                      <span className="text-xs text-slate-300">Nurse Triage Station</span>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                      Active
                    </span>
                  </div>

                  {activeVitals && (
                    <div className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-xs">
                      <div className="flex items-center gap-1 text-emerald-400 font-medium mb-1">
                        <HeartPulse className="w-3 h-3" />
                        <span>Baseline Vitals Captured</span>
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

              {/* Transition Indicator */}
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-cyan-400">
                <span className="text-[11px] text-slate-400">Forwarded to Dept:</span>
                <span className="flex items-center gap-1 font-semibold text-cyan-300">
                  Internal Med <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          </div>

          {/* ═══════════════════════════════════════════════════════════════════
              NODE 2: CLINICAL DEPARTMENT BOX & DOCTOR PICTURE (Cols 4-7)
              ═══════════════════════════════════════════════════════════════════ */}
          <div 
            onMouseEnter={() => setHoveredNode('DEPARTMENT')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`lg:col-span-4 flex flex-col rounded-2xl bg-slate-900/90 border transition-all duration-300 shadow-xl overflow-hidden ${
              isDoctorActive || hoveredNode === 'DEPARTMENT'
                ? 'border-indigo-500/80 ring-2 ring-indigo-500/20 bg-slate-900'
                : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            {/* Department Box Header */}
            <div className="px-4 py-3 bg-gradient-to-r from-indigo-950/60 to-slate-800/60 border-b border-indigo-900/40 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-base">👨‍⚕️</span>
                <span className="text-xs font-bold text-indigo-300 tracking-wide uppercase">
                  2. Department: Internal Medicine
                </span>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Attending on Duty
              </span>
            </div>

            {/* Department Body & Doctor Card */}
            <div className="p-4 flex-1 flex flex-col justify-between gap-4">
              {/* Doctor Profile Card with Real Photo */}
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-indigo-900/40 shadow-inner flex items-center gap-3.5">
                <div className="relative shrink-0">
                  <img
                    src={drMarcusPhoto}
                    alt="Dr. Marcus Vance, MD, FACP"
                    className="w-16 h-16 rounded-xl object-cover border-2 border-indigo-500/60 shadow-md shadow-indigo-500/20"
                  />
                  <span 
                    className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-slate-900" 
                    title="Active & Ready"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-slate-100 truncate">
                      Dr. Marcus Vance
                    </h3>
                    <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/60 px-1.5 py-0.5 rounded border border-indigo-800/40">
                      MD, FACP
                    </span>
                  </div>
                  <p className="text-[11px] text-indigo-300 font-medium truncate">
                    Chief Attending Physician
                  </p>
                  <p className="text-[10px] text-slate-400 truncate">
                    Internal Medicine & Clinical Diagnostics
                  </p>

                  <div className="mt-1 flex items-center gap-1 text-[10px] text-emerald-400">
                    <Sparkles className="w-2.5 h-2.5" />
                    <span>MedGemma Aligned (4-bit RTX 4060)</span>
                  </div>
                </div>
              </div>

              {/* Real-Time Doctor Action Bar */}
              <div className="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-900/30 text-xs">
                <div className="flex items-center justify-between mb-1 text-[10px] text-indigo-400 uppercase tracking-wider font-semibold">
                  <span>Current Physician Activity</span>
                  <Activity className="w-3 h-3 text-indigo-400 animate-pulse" />
                </div>
                <div className="font-mono text-xs text-slate-200 font-medium truncate">
                  {doctorAction || 'Evaluating Patient Case & Clinical Guidelines'}
                </div>
              </div>

              {/* Department Diagnostics Sub-Units */}
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={onOpenConsult}
                  className={`p-2 rounded-lg border text-left transition flex items-center gap-2 cursor-pointer group ${
                    isDoctorActive || isLabActive
                      ? 'bg-indigo-950/60 border-indigo-500 shadow-sm shadow-indigo-500/20'
                      : 'bg-slate-800/60 hover:bg-slate-700/80 border-slate-700'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition-transform" />
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-slate-200 truncate">Dr. Vance RAG</div>
                    <div className="text-[9px] text-slate-400">Harrison's Knowledge</div>
                  </div>
                </button>

                <button
                  onClick={onOpenPharmacy}
                  className={`p-2 rounded-lg border text-left transition flex items-center gap-2 cursor-pointer group ${
                    isPharmacyActive
                      ? 'bg-amber-950/60 border-amber-500 shadow-sm shadow-amber-500/20'
                      : 'bg-slate-800/60 hover:bg-slate-700/80 border-slate-700'
                  }`}
                >
                  <Pill className="w-3.5 h-3.5 text-amber-400 group-hover:scale-110 transition-transform" />
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-slate-200 truncate">Pharmacy Safety</div>
                    <div className="text-[9px] text-slate-400">Contraindications</div>
                  </div>
                </button>
              </div>

              {/* Direct Path Output Indicator */}
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs text-indigo-300">
                <span className="text-[11px] text-slate-400">Path Output:</span>
                <span className="flex items-center gap-1 font-semibold text-indigo-200">
                  Cases Review Area <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          </div>

          {/* ═══════════════════════════════════════════════════════════════════
              NODE 3: CASES PROCESSING AREA (Cols 8-10)
              ═══════════════════════════════════════════════════════════════════ */}
          <div 
            onMouseEnter={() => setHoveredNode('CASES')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`lg:col-span-3 flex flex-col rounded-2xl bg-slate-900/90 border transition-all duration-300 shadow-xl overflow-hidden ${
              hoveredNode === 'CASES'
                ? 'border-sky-500/80 ring-2 ring-sky-500/20 bg-slate-900'
                : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            {/* Header */}
            <div className="px-4 py-3 bg-slate-800/50 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-base">📋</span>
                <span className="text-xs font-bold text-sky-300 tracking-wide uppercase">
                  3. Cases Area
                </span>
              </div>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-sky-950 text-sky-400 border border-sky-800/60">
                {cases.length} Records
              </span>
            </div>

            {/* Body: Interactive Cases List */}
            <div className="p-3 flex-1 flex flex-col justify-between gap-3">
              <div className="text-[11px] text-slate-400 mb-1 flex items-center justify-between">
                <span>Select Case to Route:</span>
                <span className="text-[10px] text-slate-500">Live Queue</span>
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {cases.map((c) => {
                  const isSelected = c.id === selectedCaseId;
                  return (
                    <div
                      key={c.id}
                      onClick={() => onSelectCase(c.id)}
                      className={`p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-sky-950/60 border-sky-500 shadow-md shadow-sky-500/10'
                          : 'bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-[10px] font-bold text-sky-400">{c.id}</span>
                          <span className="font-semibold text-slate-200">{c.name}</span>
                        </div>
                        <span className={`text-[9px] px-1.5 py-0.2 rounded font-bold uppercase ${
                          c.acuity === 'Critical'
                            ? 'bg-rose-950 text-rose-400 border border-rose-800'
                            : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}>
                          {c.acuity}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 truncate">
                        {c.chief_complaint}
                      </p>
                      <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-500">
                        <span>{c.age}yo {c.sex}</span>
                        {isSelected && (
                          <span className="text-sky-400 font-semibold flex items-center gap-0.5">
                            Selected <ChevronRight className="w-2.5 h-2.5" />
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Transition to Exit Point */}
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs text-sky-300">
                <span className="text-[11px] text-slate-400">Next Destination:</span>
                <span className="flex items-center gap-1 font-semibold text-emerald-300">
                  Discharge & Exit <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          </div>

          {/* ═══════════════════════════════════════════════════════════════════
              NODE 4: PATIENT EXIT POINT / DISCHARGE HUB (Cols 11-12)
              ═══════════════════════════════════════════════════════════════════ */}
          <div 
            onMouseEnter={() => setHoveredNode('EXIT')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`lg:col-span-2 flex flex-col rounded-2xl bg-slate-900/90 border transition-all duration-300 shadow-xl overflow-hidden ${
              isDischargeActive || hoveredNode === 'EXIT'
                ? 'border-emerald-500/80 ring-2 ring-emerald-500/20 bg-slate-900'
                : 'border-slate-800 hover:border-slate-700'
            }`}
          >
            {/* Header */}
            <div className="px-4 py-3 bg-emerald-950/40 border-b border-emerald-900/40 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <DoorOpen className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-emerald-300 tracking-wide uppercase">
                  4. Exit Point
                </span>
              </div>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-800">
                Final Hub
              </span>
            </div>

            {/* Body */}
            <div className="p-3 flex-1 flex flex-col justify-between gap-3">
              <div className="space-y-2">
                <div className="p-2.5 rounded-xl bg-slate-950/60 border border-emerald-900/30 text-center">
                  <div className="w-8 h-8 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto mb-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div className="text-xs font-bold text-slate-200">Patient Cleared</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Disposition Finalized</div>
                </div>

                <div className="space-y-1 text-xs">
                  <div className="p-2 rounded-lg bg-slate-800/40 border border-slate-800 flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Safety Verification:</span>
                    <span className="text-emerald-400 font-semibold">100% Cleared</span>
                  </div>

                  <div className="p-2 rounded-lg bg-slate-800/40 border border-slate-800 flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Clinical Plan:</span>
                    <span className="text-cyan-400 font-semibold">Rx Grounded</span>
                  </div>

                  <button
                    onClick={onOpenTelemetry}
                    className="w-full p-2 rounded-lg bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-left transition flex items-center justify-between text-[11px] cursor-pointer mt-1"
                  >
                    <span className="text-rose-300 font-medium">Inpatient Transfer</span>
                    <span className="text-[10px] text-slate-400">Bed Board →</span>
                  </button>
                </div>
              </div>

              {/* Status Badge */}
              <div className="pt-2 border-t border-slate-800 text-center">
                <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Exit Pathway Ready
                </span>
              </div>
            </div>
          </div>

        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            FLOW CONNECTOR VISUALIZATION BAR (Clear Graphic Representation)
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="w-full bg-slate-900/60 rounded-2xl border border-slate-800/80 p-4 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                Active Trajectory Sequence & State Flow
              </span>
            </div>
            {latestEvent && (
              <span className="text-[11px] text-slate-400 font-mono truncate max-w-md">
                Latest: <span className="text-cyan-300">{latestEvent.summary || latestEvent.event_type}</span>
              </span>
            )}
          </div>

          {/* Connected Progress Line */}
          <div className="relative flex items-center justify-between w-full px-4 py-2">
            {/* Connecting Track Line */}
            <div className="absolute left-8 right-8 top-1/2 -translate-y-1/2 h-1 bg-slate-800 z-0">
              <div 
                className="h-full bg-gradient-to-r from-cyan-500 via-indigo-500 to-emerald-500 transition-all duration-700"
                style={{
                  width: isDischargeActive ? '100%' : isDoctorActive ? '66%' : isTriageActive ? '33%' : '10%'
                }}
              />
            </div>

            {/* Step 1: Intake */}
            <div className="relative z-10 flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-md ${
                isTriageActive || isDoctorActive || isDischargeActive
                  ? 'bg-cyan-500 text-slate-950 ring-4 ring-cyan-500/20'
                  : 'bg-slate-800 text-slate-400 border border-slate-700'
              }`}>
                1
              </div>
              <span className="text-[10px] font-semibold text-slate-300 mt-1.5">Intake</span>
            </div>

            {/* Step 2: Department & Dr. Vance */}
            <div className="relative z-10 flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-md ${
                isDoctorActive || isDischargeActive
                  ? 'bg-indigo-500 text-white ring-4 ring-indigo-500/20'
                  : 'bg-slate-800 text-slate-400 border border-slate-700'
              }`}>
                2
              </div>
              <span className="text-[10px] font-semibold text-slate-300 mt-1.5">Dept & Dr. Vance</span>
            </div>

            {/* Step 3: Cases Area */}
            <div className="relative z-10 flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-md ${
                isDoctorActive || isDischargeActive
                  ? 'bg-sky-500 text-slate-950 ring-4 ring-sky-500/20'
                  : 'bg-slate-800 text-slate-400 border border-slate-700'
              }`}>
                3
              </div>
              <span className="text-[10px] font-semibold text-slate-300 mt-1.5">Cases Area</span>
            </div>

            {/* Step 4: Exit Point */}
            <div className="relative z-10 flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-md ${
                isDischargeActive
                  ? 'bg-emerald-500 text-slate-950 ring-4 ring-emerald-500/20'
                  : 'bg-slate-800 text-slate-400 border border-slate-700'
              }`}>
                4
              </div>
              <span className="text-[10px] font-semibold text-slate-300 mt-1.5">Patient Exit</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
