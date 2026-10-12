import React, { useEffect, useRef } from 'react';
import type { BenchmarkCase, HospitalEvent, VitalSigns } from '../../types';
import drMarcusPhoto from '../../assets/dr_marcus_vance.jpg';
import { ActiveTrajectoryStepper } from './ActiveTrajectoryStepper';
import {
  ArrowRight,
  CheckCircle2,
  DoorOpen,
  FileText,
  HeartPulse,
  Layers,
  Play,
  RefreshCw,
  Search,
  Sparkles,
  Stethoscope,
} from 'lucide-react';

export interface HospitalFlowDiagramProps {
  cases?: BenchmarkCase[];
  selectedCaseId?: string;
  onSelectCase?: (caseId: string) => void;
  onRunSimulation?: () => void;
  isRunning?: boolean;
  activeDepartment?: string;
  doctorAction?: string;
  events?: HospitalEvent[];
  activeVitals?: VitalSigns | null;
  onOpenDepartmentStation?: (stationId: string) => void;
  onToggleTo3D?: () => void;
  onFinalizeReport?: (patientId: string) => void;
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
  onFinalizeReport,
}) => {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState<string>('');

  // 1. Patient Census Cleanup Post-Discharge (Bug #3 fix):
  // Filter out any patient with status === 'discharged' from active census and queue arrays
  const activeCensus = cases
    .filter((c) => (c as any).status !== 'discharged' && (c as any).admission_status !== 'DISCHARGED')
    .filter((c) =>
      searchFilter
        ? c.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
          c.id.toLowerCase().includes(searchFilter.toLowerCase())
        : true
    );

  // Identify current selected case safely from activeCensus
  const currentCase = activeCensus.find((c) => c.id === selectedCaseId) || (activeCensus.length > 0 ? activeCensus[0] : null);

  // Latest event summary
  const latestEvent = events.length > 0 ? events[events.length - 1] : null;

  // 2. Stepper Dynamic Synchronization (Bug #1 fix):
  // Accurately map patient trajectory to 1 of 4 discrete clinical stages:
  // Step 1: Intake & Triage
  // Step 2: Attending Examination
  // Step 3: Cases Area / Workup
  // Step 4: Discharge & Exit
  const getActiveStep = (): 1 | 2 | 3 | 4 => {
    if (!currentCase) return 1;
    const isDischarged = (currentCase as any).status === 'discharged' || (currentCase as any).admission_status === 'DISCHARGED';
    if (isDischarged) return 4;

    if (isRunning) {
      if (activeDepartment === 'RECEPTION' || activeDepartment === 'NURSE_STATION') return 1;
      if (activeDepartment.includes('DOCTOR') || activeDepartment.includes('EXAMINATION') || activeDepartment === 'INTERNAL_MEDICINE') return 2;
      if (activeDepartment === 'LABORATORY' || activeDepartment === 'RADIOLOGY' || activeDepartment === 'PHARMACY' || activeDepartment === 'CASES') return 3;
      if (activeDepartment === 'DISCHARGE') return 4;
    }

    // When patient Charles Brown is in CASES AREA (Step 3: Cases Area / Workup)
    return 3;
  };

  const activeStep = getActiveStep();

  // Progress percentage mapped directly to activeStep
  const patientProgress = activeStep === 4 ? 100 : activeStep === 3 ? 75 : activeStep === 2 ? 50 : 25;

  const isTriageActive = isRunning && activeStep === 1;
  const isDoctorActive = isRunning && activeStep === 2;
  const isCasesActive = activeStep === 3;
  const isDischargeActive = activeStep === 4;

  // Telemetry values matching screenshot
  const hr = activeVitals?.heart_rate ?? 78;
  const sys = activeVitals?.systolic_bp ?? 124;
  const dia = activeVitals?.diastolic_bp ?? 82;
  const map = Math.round((2 * dia + sys) / 3);
  const spo2 = activeVitals?.spo2_percent ?? 98;
  const rr = activeVitals?.respiratory_rate ?? 16;
  const tempF = 98.6;
  const tempC = activeVitals?.temperature_c ?? 37.0;

  return (
    <div className="w-full h-full flex flex-col bg-[#f8fafc] text-slate-800 overflow-y-auto p-4 md:p-6 select-none relative isolate font-sans">
      {/* ═══════════════════════════════════════════════════════════════════
          SUB-HEADER & CLINICAL COMMAND BAR (Matching Screenshot)
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="w-full flex flex-wrap items-center justify-between gap-3 pb-3 mb-3 border-b border-slate-200 shrink-0">
        <div className="flex items-center gap-2.5">
          <button
            onClick={onRunSimulation}
            disabled={isRunning || !currentCase}
            className={`px-4 py-2 rounded-lg text-xs font-mono font-bold flex items-center gap-2 transition cursor-pointer shadow-xs active:scale-95 ${
              isRunning
                ? 'bg-amber-100 text-amber-800 border border-amber-300 animate-pulse'
                : !currentCase
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-300'
                : 'bg-[#0d6e60] hover:bg-[#0b5c50] text-white shadow-teal-900/20'
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

          {/* Mode Pill Toggle */}
          <div className="flex items-center rounded-lg bg-slate-100 p-0.5 border border-slate-200 text-xs font-mono">
            <span className="px-2.5 py-1 rounded bg-teal-50 text-[#0d6e60] font-bold border border-teal-200 shadow-2xs">
              2D SCHEMATIC
            </span>
            <span className="px-2.5 py-1 rounded text-slate-500 font-medium">
              ENCOUNTER TRAJECTORY
            </span>
          </div>
        </div>

        {/* Search Input Bar with Keyboard Shortcuts */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Patient ID or MRN..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="pl-8 pr-8 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-mono text-slate-800 placeholder-slate-400 w-48 sm:w-60 focus:outline-none focus:ring-1 focus:ring-[#0d6e60] shadow-2xs"
            />
            <kbd className="absolute right-2 top-1/2 -translate-y-1/2 px-1 bg-slate-100 rounded text-[9px] font-mono text-slate-400">
              ⌘K
            </kbd>
          </div>

          <button
            onClick={() => {
              if (activeCensus.length > 1) {
                const idx = activeCensus.findIndex((c) => c.id === currentCase?.id);
                const next = activeCensus[(idx + 1) % activeCensus.length];
                onSelectCase(next.id);
              }
            }}
            className="hidden sm:flex items-center gap-1 px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-700 shadow-2xs cursor-pointer"
          >
            <span>Switch Patient</span>
            <kbd className="text-[9px] text-slate-400 font-mono">⌥P</kbd>
          </button>
        </div>
      </div>

      {/* Pathway Sub-Breadcrumb Row */}
      <div className="w-full flex items-center justify-between pb-4 mb-4 border-b border-slate-200/80 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-[#0d6e60] shadow-2xs">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xs md:text-sm font-bold text-slate-900 tracking-wide font-mono uppercase">
                CLINICAL PATHWAY &amp; ENCOUNTER TRAJECTORY
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-teal-50 text-[#0d6e60] border border-teal-200 font-semibold">
                2D SCHEMATIC
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-sans mt-0.5">
              <span>Admission Triage</span>
              <ArrowRight className="w-3 h-3 text-slate-400" />
              <span>Attending Examination</span>
              <ArrowRight className="w-3 h-3 text-slate-400" />
              <span>Active Cases Disposition</span>
              <ArrowRight className="w-3 h-3 text-slate-400" />
              <span className="text-[#0d6e60] font-semibold">Discharge Hub</span>
            </div>
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-2">
          <button
            onClick={() => onRunSimulation()}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-700 shadow-2xs cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
            <span>Re-evaluate Pathway</span>
          </button>
          <button
            onClick={onRunSimulation}
            disabled={isRunning || !currentCase}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[#0d6e60] hover:bg-[#0b5c50] text-white rounded-lg text-xs font-mono font-bold shadow-xs cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>SIMULATE SELECTED CASE</span>
          </button>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          TELEMETRY HORIZON: 3 CARDS (Matching Screenshot)
          ═══════════════════════════════════════════════════════════════════ */}
      <section className="grid grid-cols-1 xl:grid-cols-12 gap-3.5 mb-5 shrink-0">
        {/* Card 1: Patient Demographics & Diagnosis (Cols 1 to 4) */}
        <div className="xl:col-span-4 bg-white border border-slate-200 rounded-xl p-4 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200">
                {currentCase ? `ESI LEVEL ${currentCase.acuity === 'Critical' ? '1' : '2'}` : 'READY'}
              </span>
              <div className="flex items-center gap-1 text-[11px] font-mono text-slate-600 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span>{currentCase?.id || 'STANDBY'}</span>
              </div>
            </div>

            <h3 className="text-2xl font-bold text-slate-900 tracking-tight">
              {currentCase?.name || 'Awaiting Admission'}
            </h3>

            <div className="flex items-center gap-2 text-xs font-mono mt-1 text-slate-600">
              <span className="font-bold">{currentCase ? `${currentCase.age}yo ${currentCase.sex}` : 'Standard'}</span>
              <span>•</span>
              <span className="text-[#0d6e60] font-bold">
                LOC: {(currentCase as any)?.assigned_department || 'IM-STEPDOWN (Bed 04-B)'}
              </span>
            </div>
          </div>

          <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold">
              Primary Diagnosis:
            </span>
            <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100 font-semibold text-xs font-sans">
              {currentCase ? 'Bacterial Pneumonia' : 'Undifferentiated'}
            </span>
          </div>
        </div>

        {/* Card 2: ECG Lead II Rhythm Strip (Cols 5 to 8) */}
        <div className="xl:col-span-4 bg-[#0f172a] border border-slate-800 text-white rounded-xl p-3 shadow-inner flex flex-col justify-between">
          <div className="flex items-center justify-between font-mono text-[9px] text-cyan-400 tracking-wider">
            <div className="flex items-center gap-1.5 font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
              <span>LEAD II • ECG 25MM/S NSR CONDUCTION</span>
            </div>
            <span className="text-slate-400 font-semibold">FILTER: 0.05-40HZ</span>
          </div>

          {/* Glowing Waveform */}
          <div className="h-10 relative overflow-hidden flex items-center px-1">
            <svg className="w-full h-8 stroke-cyan-400" fill="none" preserveAspectRatio="none" viewBox="0 0 500 40">
              <path
                className="drop-shadow-[0_0_8px_rgba(34,211,238,0.85)]"
                d="M 0,20 L 40,20 L 50,18 L 55,20 L 70,20 L 75,5 L 82,36 L 88,14 L 92,20 L 110,20 L 125,16 L 140,20 L 180,20 L 190,18 L 195,20 L 210,20 L 215,5 L 222,36 L 228,14 L 232,20 L 250,20 L 265,16 L 280,20 L 320,20 L 330,18 L 335,20 L 350,20 L 355,5 L 362,36 L 368,14 L 372,20 L 390,20 L 405,16 L 420,20 L 460,20 L 470,18 L 475,20 L 500,20"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.8"
              />
            </svg>
            <div className="absolute inset-y-0 w-12 bg-gradient-to-r from-transparent via-cyan-400/25 to-transparent ecg-scanner pointer-events-none" />
          </div>

          <div className="flex items-center justify-between text-[10px] font-mono text-slate-300 pt-1 border-t border-slate-800">
            <div>QRS DURATION: <span className="font-bold text-white">88ms</span></div>
            <div>QTc INTERVAL: <span className="font-bold text-white">412ms</span></div>
            <div>ST DEVIATION: <span className="font-bold text-emerald-400">0.02 mV</span></div>
          </div>
        </div>

        {/* Card 3: Continuous Telemetry Readout (Cols 9 to 12) */}
        <div className="xl:col-span-4 bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-mono text-[10px] font-bold text-slate-600 uppercase tracking-wider">
              CONTINUOUS TELEMETRY READOUT
            </span>
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200 text-[10px] font-mono font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse" />
              <span>Live Sync</span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-200">
              <div className="text-[9px] font-mono text-slate-500 uppercase">HEART RATE</div>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-xl font-bold text-slate-900 leading-none">{hr}</span>
                <span className="font-mono text-[9px] text-slate-500 font-bold">BPM</span>
              </div>
              <div className="text-[9px] font-mono text-emerald-600 font-semibold mt-1">Normal Sinus</div>
            </div>

            <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-200">
              <div className="text-[9px] font-mono text-slate-500 uppercase">NIBP SYS/DIA</div>
              <div className="flex items-baseline gap-0.5 mt-0.5">
                <span className="font-mono text-lg font-bold text-slate-900 leading-none">{sys}/{dia}</span>
              </div>
              <div className="text-[9px] font-mono text-slate-500 mt-1">MAP: {map} mmHg</div>
            </div>

            <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-200">
              <div className="text-[9px] font-mono text-slate-500 uppercase">SPO2 %</div>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-xl font-bold text-[#0d6e60] leading-none">{spo2}</span>
                <span className="font-mono text-[9px] text-slate-500 font-bold">%</span>
              </div>
              <div className="text-[9px] font-mono text-slate-500 mt-1">Room Air (Ambient)</div>
            </div>
          </div>

          <div className="mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono text-slate-500">
            <div>Respirations: <span className="font-bold text-slate-800">{rr} bpm</span></div>
            <div>Temp: <span className="font-bold text-slate-800">{tempF} °F ({tempC} °C)</span></div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════
          MAIN 4-STAGE CLINICAL TRAVERSAL GRID (Equal 4-Column Layout)
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="w-full flex-1 flex flex-col gap-5 z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-stretch relative">

          {/* ── NODE 1: 1. INTAKE & TRIAGE ── */}
          <div
            onMouseEnter={() => setHoveredNode('INTAKE')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`flex flex-col rounded-xl bg-white border transition-all duration-200 shadow-2xs overflow-hidden ${
              isTriageActive || hoveredNode === 'INTAKE'
                ? 'border-[#0d6e60] ring-1 ring-[#0d6e60]/20'
                : 'border-slate-200'
            }`}
          >
            <div className="px-3.5 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-xs font-mono font-bold text-slate-900 tracking-wider uppercase">
                  1. INTAKE &amp; TRIAGE
                </span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-100 text-slate-700">
                ENTRY GATE
              </span>
            </div>

            <div className="p-3.5 flex-1 flex flex-col justify-between gap-3">
              <div className="space-y-2.5">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono mb-0.5">
                    <span>ACTIVE ADMISSION</span>
                    <span className="text-[#0d6e60] font-bold">{currentCase?.id || 'STANDBY'}</span>
                  </div>
                  <div className="font-bold text-slate-900 text-xs">
                    {currentCase?.name || 'Awaiting Patient Admission'}
                  </div>
                  <div className="text-[11px] text-slate-600 mt-1 flex items-start gap-1.5 leading-snug">
                    <HeartPulse className="w-3.5 h-3.5 text-[#0d6e60] shrink-0 mt-0.5" />
                    <span>{currentCase?.chief_complaint || 'Pneumonia Primary Presentation'}</span>
                  </div>
                </div>

                <div
                  onClick={() => onOpenDepartmentStation?.('NURSE_STATION')}
                  className="p-2.5 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 flex items-center justify-between cursor-pointer transition text-xs shadow-2xs"
                >
                  <div className="flex items-center gap-2">
                    <Stethoscope className="w-3.5 h-3.5 text-[#0d6e60]" />
                    <span className="text-slate-800 font-medium">Nurse Triage Station</span>
                  </div>
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                    ONLINE
                  </span>
                </div>

                <div className="space-y-1 text-[11px] text-slate-600 font-mono pl-1">
                  <div>Triage Acuity: <span className="font-semibold text-slate-900">Emergent</span></div>
                  <div>Assessment Complete</div>
                  <div>Intake Nurse: <span className="font-semibold text-slate-900">Sarah Jenkins, BSN RN</span></div>
                  <div>Arrival Delta: <span className="font-bold text-slate-900">T+00:00:00</span></div>
                </div>
              </div>

              <div className="pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-slate-400 uppercase">FORWARDED TO:</span>
                <span className="flex items-center gap-1 text-[#0d6e60] font-bold text-[11px]">
                  Internal Med <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          </div>

          {/* ── NODE 2: 2. ATTENDING EXAM ── */}
          <div
            onMouseEnter={() => setHoveredNode('EXAM')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`flex flex-col rounded-xl bg-white border transition-all duration-200 shadow-2xs overflow-hidden ${
              isDoctorActive || hoveredNode === 'EXAM'
                ? 'border-[#0d6e60] ring-1 ring-[#0d6e60]/20'
                : 'border-slate-200'
            }`}
          >
            <div className="px-3.5 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-xs font-mono font-bold text-slate-900 tracking-wider uppercase">
                  2. ATTENDING EXAM
                </span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-50 text-sky-700 border border-sky-200">
                ON DUTY
              </span>
            </div>

            <div className="p-3.5 flex-1 flex flex-col justify-between gap-3">
              <div className="space-y-2.5">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center gap-3">
                  <img
                    src={drMarcusPhoto}
                    alt="Dr. Marcus Vance"
                    className="w-12 h-12 rounded-lg object-cover border border-slate-300 shadow-2xs shrink-0"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 text-xs truncate">Dr. Marcus Vance</span>
                      <span className="text-[9px] font-mono bg-white px-1 rounded border border-slate-300 font-bold">MD, FACP</span>
                    </div>
                    <p className="text-[10px] text-slate-500 truncate">Chief Attending Physician</p>
                    <div className="mt-1 flex items-center gap-1 text-[9px] text-[#0d6e60] font-mono font-semibold">
                      <Sparkles className="w-2.5 h-2.5" />
                      <span>Clinical AI Aligned (RTX 4500)</span>
                    </div>
                  </div>
                </div>

                <div className="p-2 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                  <div className="text-[9px] font-mono text-slate-400 uppercase font-semibold mb-0.5">
                    CURRENT PHYSICIAN ACTIVITY
                  </div>
                  <div className="font-mono text-[11px] text-slate-800 font-medium truncate">
                    {doctorAction}
                  </div>
                </div>

                <button
                  onClick={onOpenConsult}
                  className="w-full p-2.5 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-left transition flex items-center justify-between cursor-pointer shadow-2xs group"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5 text-[#0d6e60]" />
                    <div className="text-xs font-semibold text-slate-800">
                      Dr. Vance RAG Consult
                      <div className="text-[9px] font-mono text-slate-400 font-normal">Harrison's Principles 21st Ed.</div>
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              <div className="pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-slate-400 uppercase">PATH OUTPUT:</span>
                <span className="flex items-center gap-1 text-[#0d6e60] font-bold text-[11px]">
                  Cases Processing <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          </div>

          {/* ── NODE 3: 3. CASES AREA (With Live Census Queue & Lab Checklist) ── */}
          <div
            onMouseEnter={() => setHoveredNode('CASES')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`flex flex-col rounded-xl bg-white border transition-all duration-200 shadow-2xs overflow-hidden ${
              isCasesActive || hoveredNode === 'CASES'
                ? 'border-[#0d6e60] ring-1 ring-[#0d6e60]/20'
                : 'border-slate-200'
            }`}
          >
            <div className="px-3.5 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-xs font-mono font-bold text-slate-900 tracking-wider uppercase">
                  3. CASES AREA
                </span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-50 text-sky-700 border border-sky-200">
                {activeCensus.length} IN CENSUS
              </span>
            </div>

            <div className="p-3.5 flex-1 flex flex-col justify-between gap-3">
              <div className="space-y-2.5">
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span>SELECT CASE TO ROUTE:</span>
                  <div className="flex items-center gap-1 text-emerald-700 font-bold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span>LIVE QUEUE</span>
                  </div>
                </div>

                {/* Case Selected Card */}
                {currentCase ? (
                  <div className="p-2.5 rounded-lg bg-teal-50/40 border border-teal-200 shadow-2xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono text-[10px] font-bold text-[#0d6e60]">{currentCase.id}</span>
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200">
                        {currentCase.acuity === 'Critical' ? 'CRITICAL' : 'URGENT'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="font-bold text-slate-900 text-xs">{currentCase.name}</div>
                      <span className="px-1.5 py-0.5 rounded bg-[#0d6e60] text-white text-[9px] font-mono font-bold flex items-center gap-0.5">
                        <span>SELECTED</span>
                        <span>✓</span>
                      </span>
                    </div>

                    <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                      Pneumonia • {currentCase.age}yo {currentCase.sex}
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-slate-50 border border-dashed border-slate-300 text-center text-xs text-slate-500">
                    No Active Patients in Queue
                  </div>
                )}

                {/* Clinical Checklist / Diagnostics */}
                <div className="space-y-1.5 p-2 rounded-lg bg-slate-50 border border-slate-200 text-[10px] font-mono">
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Sputum Gram Stain:</span>
                    <span className="font-bold text-slate-900">Streptococcus pneumoniae</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Procalcitonin Level:</span>
                    <span className="font-bold text-slate-900">0.42 ng/mL (Decreasing)</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>IV Antibiotics:</span>
                    <span className="font-bold text-[#0d6e60]">Ceftriaxone Completed</span>
                  </div>
                </div>
              </div>

              <div className="pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-slate-400 uppercase">NEXT NODE:</span>
                <span className="flex items-center gap-1 text-[#0d6e60] font-bold text-[11px]">
                  Discharge &amp; Exit <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          </div>

          {/* ── NODE 4: 4. EXIT POINT (Discharge Hub) ── */}
          <div
            onMouseEnter={() => setHoveredNode('EXIT')}
            onMouseLeave={() => setHoveredNode(null)}
            className={`flex flex-col rounded-xl bg-white border transition-all duration-200 shadow-2xs overflow-hidden ${
              isDischargeActive || hoveredNode === 'EXIT'
                ? 'border-emerald-500 ring-1 ring-emerald-500/20'
                : 'border-slate-200'
            }`}
          >
            <div className="px-3.5 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <DoorOpen className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-xs font-mono font-bold text-slate-900 tracking-wider uppercase">
                  4. EXIT POINT
                </span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                FINAL HUB
              </span>
            </div>

            <div className="p-3.5 flex-1 flex flex-col justify-between gap-3">
              <div className="space-y-2.5">
                <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-200 text-center">
                  <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-1 shadow-2xs">
                    <CheckCircle2 className="w-4 h-4 stroke-[2.5]" />
                  </div>
                  <div className="text-xs font-bold text-slate-900">Patient Cleared</div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">Disposition Protocol Finalized</div>
                </div>

                <div className="space-y-1.5 text-[10px] font-mono">
                  <div className="p-1.5 rounded bg-slate-50 border border-slate-200 flex items-center justify-between">
                    <span className="text-slate-500">SAFETY AUDIT:</span>
                    <span className="font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.2 rounded border border-indigo-100">
                      100% CLEARED
                    </span>
                  </div>

                  <div className="p-1.5 rounded bg-slate-50 border border-slate-200 flex items-center justify-between">
                    <span className="text-slate-500">TREATMENT PLAN:</span>
                    <span className="font-bold text-slate-800">Rx GROUNDED (Oral Switch)</span>
                  </div>

                  <div className="p-1.5 rounded bg-slate-50 border border-slate-200 flex items-center justify-between">
                    <span className="text-slate-500">DISPOSITION:</span>
                    <span className="font-bold text-emerald-700">DISCHARGE READY</span>
                  </div>
                </div>

                {/* Finalize Discharge Action Button */}
                <button
                  onClick={() => {
                    if (currentCase && onFinalizeReport) {
                      onFinalizeReport(currentCase.id);
                    }
                  }}
                  disabled={!currentCase || isRunning}
                  className="w-full py-2 px-3 rounded-lg font-mono text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-xs bg-teal-50 hover:bg-teal-100 text-[#0d6e60] border border-teal-300 active:scale-95"
                  title="Finalize Patient Discharge and Move Report to Doctor Review"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#0d6e60]" />
                  <span>DISCHARGE READY &amp; CLEARED</span>
                </button>
              </div>

              <div className="pt-2 border-t border-slate-100 text-center">
                <span className="inline-flex items-center gap-1.5 text-[10px] font-mono text-emerald-700 font-bold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  DISCHARGE READY &amp; CLEARED
                </span>
              </div>
            </div>
          </div>

        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            DYNAMIC PATIENT TRAJECTORY STEPPER & STATE FLOW (Matching Screenshot)
            ═══════════════════════════════════════════════════════════════════ */}
        <ActiveTrajectoryStepper
          progress={patientProgress}
          activeStep={activeStep}
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

export default HospitalFlowDiagram;
