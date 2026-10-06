import React, { useState } from 'react';
import type { BenchmarkCase, HospitalEvent, VitalSigns } from '../../types';
import drMarcusPhoto from '../../assets/dr_marcus_vance.jpg';
import { ActiveTrajectoryStepper } from './ActiveTrajectoryStepper';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
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

  // Identify current selected case safely
  const currentCase = cases.find((c) => c.id === selectedCaseId) || (cases.length > 0 ? cases[0] : null);

  // Latest event summary
  const latestEvent = events.length > 0 ? events[events.length - 1] : null;

  // Filter events scoped to the selected case if encounter_id or patient_id matches
  const caseEvents = currentCase
    ? events.filter(
        (e) =>
          e.patient_id === currentCase.id ||
          (e.payload && (e.payload.patient_id === currentCase.id || e.payload.case_id === currentCase.id))
      )
    : events;

  const isCaseDischarged = (currentCase as any)?.status === 'discharged' || (currentCase as any)?.admission_status === 'DISCHARGED';

  // Determine stage active states based on latest events / simulation state
  const isTriageActive = isRunning && (activeDepartment === 'RECEPTION' || activeDepartment === 'NURSE_STATION');
  const isDoctorActive = isRunning && (activeDepartment.includes('DOCTOR') || activeDepartment.includes('EXAMINATION'));
  const isLabActive = isRunning && (activeDepartment === 'LABORATORY' || activeDepartment === 'RADIOLOGY' || activeDepartment === 'PHARMACY');
  const isDischargeActive = isCaseDischarged || (isRunning && (activeDepartment === 'DISCHARGE' || caseEvents.some((e) => e.event_type === 'CLINICAL_REPORT_GENERATED')));
  const isCasesActive = !isDischargeActive && !isDoctorActive && !isTriageActive && currentCase !== null;

  // Dynamic patient trajectory position percentage (0% to 100%)
  const getPatientProgress = () => {
    if (isDischargeActive) return 100;
    if (isLabActive) return 85;
    if (isDoctorActive) return 60;
    if (isTriageActive) return 35;
    if (isRunning) {
      // Dynamic live event-driven progression so it never stalls at 16%
      const eventProgress = Math.min(92, 25 + caseEvents.length * 8);
      return Math.max(25, eventProgress);
    }
    // When patient is in Cases Area awaiting workup:
    if (currentCase) return 75;
    return 0;
  };

  const patientProgress = getPatientProgress();

  // Safe fallback vital values
  const hr = activeVitals?.heart_rate ?? 78;
  const sys = activeVitals?.systolic_bp ?? 124;
  const dia = activeVitals?.diastolic_bp ?? 82;
  const map = Math.round((2 * dia + sys) / 3);
  const spo2 = activeVitals?.spo2_percent ?? 98;
  const rr = activeVitals?.respiratory_rate ?? 16;
  const temp = activeVitals?.temperature_c ?? 37.1;

  return (
    <div className="w-full h-full flex flex-col bg-[var(--ak-color-bg-app)] text-[var(--ak-color-text-primary)] overflow-y-auto p-4 md:p-6 select-none relative isolate">
      {/* ═══════════════════════════════════════════════════════════════════
          TOP ACTION BAR & DIAGRAM CONTROLS
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="w-full flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[var(--ak-color-border-subtle)] mb-5 z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[var(--ak-color-primary-soft)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-primary)]">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm md:text-base font-semibold text-[var(--ak-color-text-primary)] tracking-tight">
                Clinical pathway and encounter trajectory
              </h2>
              <Badge variant="neutral" size="sm">
                2D Schematic
              </Badge>
            </div>
            <p className="text-xs text-[var(--ak-color-text-muted)]">
              Admission triage &rarr; Attending examination &rarr; Active cases disposition &rarr; Discharge hub
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          {onToggleTo3D && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onToggleTo3D}
              leadingIcon={<Building2 className="w-3.5 h-3.5 text-[var(--ak-color-primary)]" />}
              title="Switch to 3D spatial simulation"
            >
              Open 3D view
            </Button>
          )}

          <Button
            variant={isRunning ? 'secondary' : 'primary'}
            size="sm"
            onClick={onRunSimulation}
            disabled={isRunning || !currentCase}
            leadingIcon={
              isRunning ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5 fill-current" />
              )
            }
          >
            {isRunning
              ? 'Traversing pathway...'
              : currentCase
              ? 'Simulate selected case'
              : 'Awaiting admission'}
          </Button>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          LIVE HUD VITALS TELEMETRY & ECG RHYTHM STRIP
          ═══════════════════════════════════════════════════════════════════ */}
      <Card className="p-3.5 mb-6 z-10 shrink-0">
        <div className="flex flex-col xl:flex-row items-stretch xl:items-center justify-between gap-4">
          {/* Patient Quick Info */}
          <div className="flex items-center gap-4 border-b xl:border-b-0 xl:border-r border-[var(--ak-color-border-subtle)] pb-3 xl:pb-0 pr-0 xl:pr-5 shrink-0">
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <Badge variant={currentCase?.acuity === 'Critical' ? 'danger' : 'warning'} size="sm">
                  {currentCase ? `ESI Level ${currentCase.acuity === 'Critical' ? '1' : '2'}` : 'Ready'}
                </Badge>
                <span className="font-mono text-xs text-[var(--ak-color-primary)] font-medium">
                  {currentCase?.id || 'PT-STANDBY'}
                </span>
                <span className="h-2 w-2 rounded-full bg-[var(--ak-color-success)] animate-pulse" />
              </div>
              <h3 className="text-base font-semibold text-[var(--ak-color-text-primary)] tracking-tight mt-0.5">
                {currentCase?.name || 'Awaiting admission'}
              </h3>
              <div className="font-mono text-[11px] text-[var(--ak-color-text-muted)]">
                {currentCase
                  ? `${currentCase.age}yo ${currentCase.sex} • Location: ${(currentCase as any).assigned_department || 'IM-Stepdown'}`
                  : 'System ready for new admissions'}
              </div>
            </div>
          </div>

          {/* ECG Lead II Rhythm Strip */}
          <div className="flex-1 min-w-[220px] max-w-lg h-14 bg-[var(--ak-color-text-primary)] rounded-lg relative overflow-hidden flex items-center px-3">
            <div className="absolute top-1 left-2 font-mono text-[9px] text-[var(--ak-color-primary-soft)] tracking-wider flex items-center gap-2 z-10">
              <span className="font-medium text-white/90">Lead II • ECG 25mm/s</span>
              <span className="border-[var(--ak-color-border-subtle)] font-medium">NSR Conduction</span>
            </div>
            <svg className="w-full h-8 stroke-white/80" fill="none" preserveAspectRatio="none" viewBox="0 0 500 40">
              <path
                d="M 0,20 L 40,20 L 50,18 L 55,20 L 70,20 L 75,5 L 82,36 L 88,14 L 92,20 L 110,20 L 125,16 L 140,20 L 180,20 L 190,18 L 195,20 L 210,20 L 215,5 L 222,36 L 228,14 L 232,20 L 250,20 L 265,16 L 280,20 L 320,20 L 330,18 L 335,20 L 350,20 L 355,5 L 362,36 L 368,14 L 372,20 L 390,20 L 405,16 L 420,20 L 460,20 L 470,18 L 475,20 L 500,20"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.8"
              />
            </svg>
            <div className="absolute inset-y-0 w-12 bg-gradient-to-r from-transparent via-white/20 to-transparent ecg-scanner pointer-events-none" />
          </div>

          {/* Tabular Telemetry Grid */}
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 shrink-0">
            {/* HR */}
            <div className="bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] p-2 rounded-lg flex flex-col justify-between">
              <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">Heart rate</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-lg font-bold text-[var(--ak-color-success)] leading-none tabular-nums">{hr}</span>
                <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">bpm</span>
              </div>
              <span className="font-mono text-[9px] text-[var(--ak-color-success)] mt-1">Normal sinus</span>
            </div>

            {/* NIBP */}
            <div className="bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] p-2 rounded-lg flex flex-col justify-between">
              <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">NIBP SYS/DIA</span>
              <div className="flex items-baseline gap-0.5 mt-0.5">
                <span className="font-mono text-base font-bold text-[var(--ak-color-text-primary)] leading-none tabular-nums">{sys}/{dia}</span>
              </div>
              <span className="font-mono text-[9px] text-[var(--ak-color-primary)] mt-1">MAP: {map} mmHg</span>
            </div>

            {/* SPO2 */}
            <div className="bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] p-2 rounded-lg flex flex-col justify-between">
              <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">SpO2</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-lg font-bold text-[var(--ak-color-primary)] leading-none tabular-nums">{spo2}</span>
                <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">%</span>
              </div>
              <span className="font-mono text-[9px] text-[var(--ak-color-text-muted)] mt-1">Room air</span>
            </div>

            {/* RESP */}
            <div className="bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] p-2 rounded-lg flex flex-col justify-between">
              <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">Resp rate</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-lg font-bold text-[var(--ak-color-text-primary)] leading-none tabular-nums">{rr}</span>
                <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">bpm</span>
              </div>
              <span className="font-mono text-[9px] text-[var(--ak-color-text-muted)] mt-1">Eupneic</span>
            </div>

            {/* TEMP */}
            <div className="bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] p-2 rounded-lg flex flex-col justify-between">
              <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">Core temp</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-lg font-bold text-[var(--ak-color-text-primary)] leading-none tabular-nums">{temp}</span>
                <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">°C</span>
              </div>
              <span className="font-mono text-[9px] text-[var(--ak-color-success)] mt-1">Normothermic</span>
            </div>

            {/* LACTATE */}
            <div className="bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] p-2 rounded-lg flex flex-col justify-between">
              <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">Lactate</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-lg font-bold text-[var(--ak-color-success)] leading-none tabular-nums">1.2</span>
                <span className="font-mono text-[10px] text-[var(--ak-color-text-muted)]">mmol</span>
              </div>
              <span className="font-mono text-[9px] text-[var(--ak-color-success)] mt-1">STAT normal</span>
            </div>
          </div>
        </div>
      </Card>

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
            className={`lg:col-span-3 flex flex-col rounded-xl bg-[var(--ak-color-bg-surface)] border transition-all duration-200 overflow-hidden ${
              isTriageActive || hoveredNode === 'INTAKE'
                ? 'border-[var(--ak-color-primary)] ring-1 ring-[var(--ak-color-primary)]/20'
                : 'border-[var(--ak-color-border-subtle)] hover:border-[var(--ak-color-border-strong)]'
            }`}
          >
            {/* Header */}
            <div className="px-3.5 py-2.5 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[var(--ak-color-primary)]" />
                <span className="text-xs font-mono font-semibold text-[var(--ak-color-text-primary)] tracking-wider uppercase">
                  1. Intake & Triage
                </span>
              </div>
              <Badge variant="primary" size="sm">
                Entry Gate
              </Badge>
            </div>

            {/* Body */}
            <div className="p-3.5 flex-1 flex flex-col justify-between gap-3">
              <div className="space-y-2.5">
                {/* Active Case Card */}
                <div className="p-3 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)]">
                  <div className="flex items-center justify-between text-[10px] text-[var(--ak-color-text-muted)] font-mono mb-1">
                    <span>Active admission</span>
                    <span className="text-[var(--ak-color-primary)] font-bold">{currentCase?.id || 'STANDBY'}</span>
                  </div>
                  <div className="font-semibold text-[var(--ak-color-text-primary)] text-xs">
                    {currentCase?.name || 'Awaiting patient admission'}
                  </div>
                  <div className="text-[11px] text-[var(--ak-color-text-secondary)] mt-1 flex items-start gap-1.5 leading-relaxed">
                    <Clock className="w-3 h-3 text-[var(--ak-color-primary)] shrink-0 mt-0.5" />
                    <span className="line-clamp-2">
                      {currentCase?.chief_complaint || 'Queue ready for manual admissions in Management Portal.'}
                    </span>
                  </div>
                </div>

                {/* Sub-Stations */}
                <div className="space-y-1.5">
                  <div
                    onClick={() => onOpenDepartmentStation?.('NURSE_STATION')}
                    className="p-2 rounded-lg bg-[var(--ak-color-bg-subtle)] hover:bg-[var(--ak-color-bg-app)] border border-[var(--ak-color-border-subtle)] flex items-center justify-between cursor-pointer transition text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <Stethoscope className="w-3.5 h-3.5 text-[var(--ak-color-primary)]" />
                      <span className="text-[var(--ak-color-text-primary)] font-medium">Nurse triage station</span>
                    </div>
                    <Badge variant="success" size="sm">
                      Online
                    </Badge>
                  </div>

                  {activeVitals && (
                    <div className="p-2 rounded-lg bg-[var(--ak-color-success-soft)] border border-[var(--ak-color-border-subtle)] text-xs">
                      <div className="flex items-center gap-1.5 text-[var(--ak-color-success)] font-mono text-[10px] font-bold mb-1">
                        <HeartPulse className="w-3 h-3" />
                        <span>Baseline vitals captured</span>
                      </div>
                      <div className="grid grid-cols-2 gap-1 text-[10px] text-[var(--ak-color-text-secondary)] font-mono">
                        <div>HR: <span className="text-[var(--ak-color-text-primary)] font-semibold">{activeVitals.heart_rate} bpm</span></div>
                        <div>BP: <span className="text-[var(--ak-color-text-primary)] font-semibold">{activeVitals.systolic_bp}/{activeVitals.diastolic_bp}</span></div>
                        <div>SpO2: <span className="text-[var(--ak-color-text-primary)] font-semibold">{activeVitals.spo2_percent}%</span></div>
                        <div>Temp: <span className="text-[var(--ak-color-text-primary)] font-semibold">{activeVitals.temperature_c}°C</span></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Trajectory Exit Arrow */}
              <div className="pt-2.5 border-t border-[var(--ak-color-border-subtle)] flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-[var(--ak-color-text-muted)] uppercase">Forwarded to:</span>
                <span className="flex items-center gap-1 text-[var(--ak-color-primary)] font-semibold text-[11px]">
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
            className={`lg:col-span-4 flex flex-col rounded-xl bg-[var(--ak-color-bg-surface)] border transition-all duration-200 overflow-hidden ${
              isDoctorActive || hoveredNode === 'DEPARTMENT'
                ? 'border-[var(--ak-color-primary)] ring-1 ring-[var(--ak-color-primary)]/20'
                : 'border-[var(--ak-color-border-subtle)] hover:border-[var(--ak-color-border-strong)]'
            }`}
          >
            {/* Header */}
            <div className="px-3.5 py-2.5 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[var(--ak-color-primary)]" />
                <span className="text-xs font-mono font-semibold text-[var(--ak-color-text-primary)] tracking-wider uppercase">
                  2. Attending Examination
                </span>
              </div>
              <Badge variant="success" size="sm">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--ak-color-success)] animate-pulse mr-1" />
                On duty
              </Badge>
            </div>

            {/* Doctor Profile Card */}
            <div className="p-3.5 flex-1 flex flex-col justify-between gap-3">
              <div className="p-3 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] flex items-center gap-3">
                <div className="relative shrink-0">
                  <img
                    src={drMarcusPhoto}
                    alt="Dr. Marcus Vance, MD, FACP"
                    className="w-14 h-14 rounded-lg object-cover border border-[var(--ak-color-border-subtle)]"
                  />
                  <span
                    className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-[var(--ak-color-success)] border-2 border-white"
                    title="Active and ready"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold text-[var(--ak-color-text-primary)] truncate">
                      Dr. Marcus Vance
                    </h4>
                    <span className="text-[9px] font-mono text-[var(--ak-color-primary)] bg-[var(--ak-color-primary-soft)] px-1 rounded border border-[var(--ak-color-border-subtle)]">
                      MD, FACP
                    </span>
                  </div>
                  <p className="text-[11px] text-[var(--ak-color-primary)] font-medium truncate">
                    Chief Attending Physician
                  </p>
                  <p className="text-[10px] text-[var(--ak-color-text-muted)] truncate">
                    Internal Medicine & Clinical Diagnostics
                  </p>
                  <div className="mt-1 flex items-center gap-1 text-[10px] text-[var(--ak-color-text-secondary)] font-mono font-medium">
                    <Sparkles className="w-2.5 h-2.5 text-[var(--ak-color-primary)]" />
                    <span>AI-assisted internal medicine</span>
                  </div>
                </div>
              </div>

              {/* Real-Time Doctor Activity Status */}
              <div className="p-2 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs">
                <div className="flex items-center justify-between mb-1 text-[9px] text-[var(--ak-color-primary)] font-mono uppercase tracking-wider font-semibold">
                  <span>Current physician activity</span>
                  <Activity className="w-3 h-3 text-[var(--ak-color-primary)] animate-pulse" />
                </div>
                <div className="font-mono text-xs text-[var(--ak-color-text-primary)] font-medium truncate">
                  {doctorAction || 'Evaluating patient case and clinical guidelines'}
                </div>
              </div>

              {/* Diagnostic Consult Action Button */}
              <button
                onClick={onOpenConsult}
                className={`w-full p-2 rounded-lg border text-left transition flex items-center gap-2 cursor-pointer group ${
                  isDoctorActive || isLabActive
                    ? 'bg-[var(--ak-color-primary-soft)] border-[var(--ak-color-primary)]'
                    : 'bg-[var(--ak-color-bg-subtle)] hover:bg-[var(--ak-color-bg-app)] border-[var(--ak-color-border-subtle)]'
                }`}
              >
                <FileText className="w-3.5 h-3.5 text-[var(--ak-color-primary)] group-hover:scale-105 transition-transform" />
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-medium text-[var(--ak-color-text-primary)] truncate">Dr. Vance consult</div>
                  <div className="text-[9px] text-[var(--ak-color-text-muted)] font-mono">Harrison's Principles 21st Edition</div>
                </div>
              </button>

              {/* Trajectory Exit Arrow */}
              <div className="pt-2 border-t border-[var(--ak-color-border-subtle)] flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-[var(--ak-color-text-muted)] uppercase">Path output:</span>
                <span className="flex items-center gap-1 text-[var(--ak-color-primary)] font-semibold text-[11px]">
                  Cases processing <ArrowRight className="w-3 h-3" />
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
            className={`lg:col-span-3 flex flex-col rounded-xl bg-[var(--ak-color-bg-surface)] border transition-all duration-200 overflow-hidden ${
              hoveredNode === 'CASES' || isCasesActive
                ? 'border-[var(--ak-color-primary)] ring-1 ring-[var(--ak-color-primary)]/20'
                : 'border-[var(--ak-color-border-subtle)] hover:border-[var(--ak-color-border-strong)]'
            }`}
          >
            {/* Header */}
            <div className="px-3.5 py-2.5 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[var(--ak-color-primary)]" />
                <span className="text-xs font-mono font-semibold text-[var(--ak-color-text-primary)] tracking-wider uppercase">
                  3. Cases Area
                </span>
              </div>
              <Badge variant="neutral" size="sm">
                {cases.length} in census
              </Badge>
            </div>

            {/* Cases Roster */}
            <div className="p-3 flex-1 flex flex-col justify-between gap-2.5">
              <div className="text-[10px] text-[var(--ak-color-text-muted)] font-mono mb-0.5 flex items-center justify-between">
                <span>Select case to route:</span>
                <span className="text-[var(--ak-color-text-muted)]">Live queue</span>
              </div>

              <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                {cases.length === 0 ? (
                  <div className="p-4 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-dashed border-[var(--ak-color-border-subtle)] text-center flex flex-col items-center justify-center">
                    <FileText className="w-5 h-5 text-[var(--ak-color-text-muted)] mb-1" />
                    <div className="text-xs font-medium text-[var(--ak-color-text-primary)]">No patient records yet</div>
                    <p className="text-[10px] text-[var(--ak-color-text-muted)] mt-1 leading-relaxed">
                      Admit patients in Clinical Intake to route them through hospital simulation.
                    </p>
                  </div>
                ) : (
                  cases.map((c) => {
                    const isSelected = c.id === selectedCaseId;
                    return (
                      <div
                        key={c.id}
                        onClick={() => onSelectCase(c.id)}
                        className={`p-2 rounded-lg border text-xs cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-[var(--ak-color-primary-soft)] border-[var(--ak-color-primary)]'
                            : 'bg-[var(--ak-color-bg-subtle)] border-[var(--ak-color-border-subtle)] hover:bg-[var(--ak-color-bg-app)]'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-0.5">
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono text-[10px] font-bold text-[var(--ak-color-primary)]">{c.id}</span>
                            <span className="font-medium text-[var(--ak-color-text-primary)] text-xs truncate max-w-[110px]">{c.name}</span>
                          </div>
                          <Badge variant={c.acuity === 'Critical' ? 'danger' : 'warning'} size="sm">
                            {c.acuity}
                          </Badge>
                        </div>
                        <p className="text-[10px] text-[var(--ak-color-text-secondary)] truncate">
                          {c.chief_complaint}
                        </p>
                        <div className="mt-1 flex items-center justify-between text-[10px] text-[var(--ak-color-text-muted)] font-mono">
                          <span>{c.age}yo {c.sex}</span>
                          {isSelected && (
                            <span className="text-[var(--ak-color-primary)] font-semibold flex items-center gap-0.5">
                              Selected <ChevronRight className="w-2.5 h-2.5" />
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Trajectory Exit Arrow */}
              <div className="pt-2 border-t border-[var(--ak-color-border-subtle)] flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-[var(--ak-color-text-muted)] uppercase">Next node:</span>
                <span className="flex items-center gap-1 text-[var(--ak-color-success)] font-semibold text-[11px]">
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
            className={`lg:col-span-2 flex flex-col rounded-xl bg-[var(--ak-color-bg-surface)] border transition-all duration-200 overflow-hidden ${
              isDischargeActive || hoveredNode === 'EXIT'
                ? 'border-[var(--ak-color-success)] ring-1 ring-[var(--ak-color-success)]/20'
                : 'border-[var(--ak-color-border-subtle)] hover:border-[var(--ak-color-border-strong)]'
            }`}
          >
            {/* Header */}
            <div className="px-3.5 py-2.5 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <DoorOpen className="w-3.5 h-3.5 text-[var(--ak-color-success)]" />
                <span className="text-xs font-mono font-semibold text-[var(--ak-color-text-primary)] tracking-wider uppercase">
                  4. Exit Point
                </span>
              </div>
              <Badge variant="success" size="sm">
                Final Hub
              </Badge>
            </div>

            {/* Body */}
            <div className="p-3 flex-1 flex flex-col justify-between gap-2.5">
              <div className="space-y-2">
                <div className="p-2 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-center">
                  <div className="w-7 h-7 rounded-full bg-[var(--ak-color-success-soft)] border border-[var(--ak-color-border-subtle)] text-[var(--ak-color-success)] flex items-center justify-center mx-auto mb-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </div>
                  <div className="text-xs font-semibold text-[var(--ak-color-text-primary)]">Patient cleared</div>
                  <div className="text-[10px] text-[var(--ak-color-text-muted)] mt-0.5 font-mono">Disposition finalized</div>
                </div>

                <div className="space-y-1 text-xs">
                  <div className="p-1.5 rounded bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] flex items-center justify-between text-[10px] font-mono">
                    <span className="text-[var(--ak-color-text-muted)]">Safety:</span>
                    <span className="text-[var(--ak-color-success)] font-semibold">100% Cleared</span>
                  </div>

                  <div className="p-1.5 rounded bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] flex items-center justify-between text-[10px] font-mono">
                    <span className="text-[var(--ak-color-text-muted)]">Plan:</span>
                    <span className="text-[var(--ak-color-primary)] font-semibold">Rx Grounded</span>
                  </div>

                  <div className="p-1.5 rounded bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] flex items-center justify-between text-[10px] font-mono">
                    <span className="text-[var(--ak-color-text-muted)]">Disposition:</span>
                    <span className="text-[var(--ak-color-success)] font-semibold">Discharge ready</span>
                  </div>
                </div>
              </div>

              {/* Status Badge */}
              <div className="pt-2 border-t border-[var(--ak-color-border-subtle)] text-center">
                <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[var(--ak-color-success)] font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--ak-color-success)] animate-pulse" />
                  Discharge ready
                </span>
              </div>
            </div>
          </div>

        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            DYNAMIC PATIENT TRAJECTORY STEPPER & STATE FLOW
            ═══════════════════════════════════════════════════════════════════ */}
        <ActiveTrajectoryStepper
          progress={patientProgress}
          isRunning={isRunning}
          currentCase={currentCase}
          latestEvent={latestEvent}
          activeDepartment={activeDepartment}
          doctorAction={doctorAction}
          onOpenDepartmentStation={onOpenDepartmentStation}
        />

      </div>
    </div>
  );
};
