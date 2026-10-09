import React, { useState } from 'react';
import type { BenchmarkCase, HospitalEvent, VitalSigns } from '../../types';
import agentObstetrics from '../../assets/vh-agent-obstetrics-512.png';
import agentEmergency from '../../assets/vh-agent-emergency-512.png';
import agentInternalMed from '../../assets/vh-agent-internal-medicine-512.png';
import agentNeurology from '../../assets/vh-agent-neurology-512.png';
import agentCardiology from '../../assets/vh-agent-cardiology-512.png';
import agentSurgery from '../../assets/vh-agent-surgery-512.png';
import { ActiveTrajectoryStepper } from './ActiveTrajectoryStepper';
import { Badge } from '../ui/Badge';
import {
  Baby,
  BookOpen,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileText,
  HeartPulse,
  Layers,
  Lock,
  RefreshCw,
  RotateCcw,
  Sparkles,
  Stethoscope,
  Users,
} from 'lucide-react';

export interface HospitalFlowDiagramProps {
  cases: BenchmarkCase[];
  selectedCaseId: string;
  onSelectCase: (caseId: string) => void;
  onRunSimulation?: () => void;
  isRunning: boolean;
  activeDepartment: string;
  doctorAction: string;
  events: HospitalEvent[];
  activeVitals: VitalSigns | null;
  onOpenDepartmentStation?: (stationId: string) => void;
  onToggleTo3D?: () => void;
  onNavigateTab?: (tab: string) => void;
  onBackToPortal?: () => void;
}

interface SpecialistAgentDetail {
  id: string;
  name: string;
  specialty: string;
  avatar: string;
  percentage: number;
  book: string;
  roleTag: string;
  rationale: string;
  clinicalOpinion: string;
}

export const HospitalFlowDiagram: React.FC<HospitalFlowDiagramProps> = ({
  cases,
  selectedCaseId,
  onSelectCase,
  onRunSimulation: _onRunSimulation,
  isRunning,
  activeDepartment,
  doctorAction,
  events,
  activeVitals: _activeVitals,
  onOpenDepartmentStation,
  onNavigateTab,
  onBackToPortal,
}) => {
  // Case room state
  const [selectedAgentId, setSelectedAgentId] = useState<string>('ALL');
  const [isFindingsExpanded, setIsFindingsExpanded] = useState<boolean>(true);
  const [hasConsensus, setHasConsensus] = useState<boolean>(false);
  const [isSynthesizing, setIsSynthesizing] = useState<boolean>(false);
  const [activeStep, setActiveStep] = useState<number>(3); // 1: Triage, 2: Attending exam, 3: Case room, 4: Sign-off
  const [showTechnicalStepper, setShowTechnicalStepper] = useState<boolean>(false);

  // Is the current view showcasing the demonstration case VH-0417 or a census case?
  const isDemoCase = selectedCaseId === 'VH-0417' || !selectedCaseId || selectedCaseId === 'CASE-101';
  const currentCase = cases.find((c) => c.id === selectedCaseId);

  // The 6 specialists for the demonstration case VH-0417 (Preeclampsia with severe features)
  const DEMO_SPECIALISTS: SpecialistAgentDetail[] = [
    {
      id: 'OBSTETRICS',
      name: 'Dr. Claire Laurent, MD',
      specialty: 'Obstetrics',
      avatar: agentObstetrics,
      percentage: 48,
      book: 'Williams Obstetrics (26th Ed)',
      roleTag: 'Lead Maternal-Fetal Specialist',
      rationale: 'Primary hypertensive disorder of pregnancy (>160/110) at 34+2 weeks requiring emergent seizure prophylaxis and fetal viability monitoring.',
      clinicalOpinion:
        'Initiate Magnesium Sulfate seizure prophylaxis immediately: 4 g IV loading dose over 20 min, followed by 1–2 g/h continuous infusion. Continuous CTG monitoring (Baseline 145 bpm, Category I verified). Severe preeclampsia confirmed. Target delivery planning following maternal stabilization; administer Betamethasone 12 mg IM for neonatal lung maturity.',
    },
    {
      id: 'EMERGENCY',
      name: 'Dr. Malik Sterling, MD',
      specialty: 'Emergency Medicine',
      avatar: agentEmergency,
      percentage: 22,
      book: "Tintinalli's Emergency Medicine (9th Ed)",
      roleTag: 'Acuity & Resuscitation',
      rationale: 'Severe acute hypertension (168/112 mmHg) posing imminent risk of maternal stroke, placental abruption, or eclamptic convulsions.',
      clinicalOpinion:
        'Emergent blood pressure reduction required within 30–60 minutes. Administer IV Labetalol 20 mg bolus over 2 min; repeat 40–80 mg every 10 min (maximum 300 mg) or IV Hydralazine 5–10 mg. Re-check BP every 10 min. Goal is to lower systolic BP to 140–150 and diastolic to 90–100 mmHg without precipitating placental hypoperfusion.',
    },
    {
      id: 'INTERNAL_MEDICINE',
      name: 'Dr. Marcus Vance, MD, FACP',
      specialty: 'Internal Medicine',
      avatar: agentInternalMed,
      percentage: 14,
      book: "Harrison's Principles of Internal Medicine (21st Ed)",
      roleTag: 'Multisystem Diagnostics',
      rationale: 'Hepatic transaminitis (AST 142, ALT 156), marked LDH elevation (720 U/L), and thrombocytopenia (88k) indicating partial HELLP syndrome spectrum.',
      clinicalOpinion:
        'Laboratory pattern demonstrates microangiopathic hemolysis and end-organ endothelial damage. Insert an indwelling urinary catheter with hourly urometer measurement to monitor acute renal impairment (baseline creatinine 87 µmol/L). Serial complete blood count and coagulation panel every 4–6 hours.',
    },
    {
      id: 'NEUROLOGY',
      name: 'Dr. Julian Thorne, MD',
      specialty: 'Neurology',
      avatar: agentNeurology,
      percentage: 8,
      book: "Adams and Victor's Neurology (11th Ed)",
      roleTag: 'Neurovascular Assessment',
      rationale: 'Severe persistent frontal/occipital headache, photopsia (flashing lights), and 2 beats of ankle clonus confirming cortical hyperexcitability.',
      clinicalOpinion:
        'Symptoms indicate acute cerebral vasospasm and loss of autoregulation. Maintain seizure precautions (padded bed rails, suction standby). Low threshold for non-contrast brain MRI / MR venography to evaluate Posterior Reversible Encephalopathy Syndrome (PRES) or cerebral venous sinus thrombosis if neurologic symptoms fail to abate with MgSO4.',
    },
    {
      id: 'CARDIOLOGY',
      name: 'Dr. Elena Rostova, MD',
      specialty: 'Cardiology',
      avatar: agentCardiology,
      percentage: 5,
      book: "Braunwald's Heart Disease (12th Ed)",
      roleTag: 'Hemodynamic Stabilization',
      rationale: 'Marked left ventricular afterload mismatch with resting tachycardia (HR 104 bpm) and hyperdynamic vascular resistance.',
      clinicalOpinion:
        'Strict total fluid restriction to 80 mL/h (or 1 mL/kg/h) to protect against acute cardiogenic pulmonary edema, a major contributor to preeclamptic maternal morbidity. Continuous SpO2 pulse oximetry monitoring. Chest examination clear at present.',
    },
    {
      id: 'SURGERY',
      name: 'Dr. Sarah Lin, MD',
      specialty: 'General Surgery',
      avatar: agentSurgery,
      percentage: 3,
      book: "Schwartz's Principles of Surgery (11th Ed)",
      roleTag: 'Acute Abdomen Exclusion',
      rationale: 'Right upper quadrant and epigastric tenderness requiring differential exclusion of subcapsular hepatic hematoma versus surgical cholecystitis.',
      clinicalOpinion:
        'RUQ tenderness is predominantly secondary to hepatic distension of Glisson’s capsule from severe preeclampsia/HELLP. Emergent bedside focused hepatobiliary ultrasound recommended to evaluate subcapsular liver hematoma and exclude acute calculous cholecystitis. Surgical intervention not indicated unless hepatic capsular rupture occurs.',
    },
  ];

  // Dynamic router specialists for other cases
  const getDynamicSpecialists = (): SpecialistAgentDetail[] => {
    if (isDemoCase) return DEMO_SPECIALISTS;
    return [
      {
        id: 'CARDIOLOGY',
        name: 'Dr. Elena Rostova, MD',
        specialty: 'Cardiology',
        avatar: agentCardiology,
        percentage: 62,
        book: "Braunwald's Heart Disease (12th Ed)",
        roleTag: 'Primary Cardiac Lead',
        rationale: 'Acutely presenting cardiac ischemia / NSTEMI with chest pressure and troponin elevation.',
        clinicalOpinion: 'Initiate emergent heparin protocol, dual antiplatelet therapy, and schedule coronary angiography.',
      },
      {
        id: 'EMERGENCY',
        name: 'Dr. Malik Sterling, MD',
        specialty: 'Emergency Medicine',
        avatar: agentEmergency,
        percentage: 20,
        book: "Tintinalli's Emergency Medicine (9th Ed)",
        roleTag: 'Resuscitation Specialist',
        rationale: 'Hemodynamic triage and continuous cardiac telemetry monitoring.',
        clinicalOpinion: 'Maintain continuous 12-lead ECG monitoring and sublingual nitroglycerin as tolerated.',
      },
      {
        id: 'INTERNAL_MEDICINE',
        name: 'Dr. Marcus Vance, MD, FACP',
        specialty: 'Internal Medicine',
        avatar: agentInternalMed,
        percentage: 12,
        book: "Harrison's Principles of Internal Medicine (21st Ed)",
        roleTag: 'Chief Attending',
        rationale: 'Multisystem metabolic and guideline-directed medical therapy evaluation.',
        clinicalOpinion: 'Review renal function and baseline lipid panel prior to medical therapy escalation.',
      },
      {
        id: 'SURGERY',
        name: 'Dr. Sarah Lin, MD',
        specialty: 'General Surgery',
        avatar: agentSurgery,
        percentage: 4,
        book: "Schwartz's Principles of Surgery (11th Ed)",
        roleTag: 'Cardiothoracic Backup',
        rationale: 'Surgical standby in the event of refractory ischemic instability.',
        clinicalOpinion: 'Cardiothoracic surgical team notified for emergent CABG if multivessel disease identified.',
      },
      {
        id: 'NEUROLOGY',
        name: 'Dr. Julian Thorne, MD',
        specialty: 'Neurology',
        avatar: agentNeurology,
        percentage: 2,
        book: "Adams and Victor's Neurology (11th Ed)",
        roleTag: 'Neurology Consult',
        rationale: 'Baseline neurological status assessment before anticoagulation.',
        clinicalOpinion: 'No focal neurological deficits detected. Neurological safety cleared for therapeutic anticoagulation.',
      },
    ];
  };

  const specialists = getDynamicSpecialists();

  // Trigger consensus simulation
  const handleToggleConsensus = () => {
    setIsSynthesizing(true);
    setTimeout(() => {
      setHasConsensus((prev) => !prev);
      setIsSynthesizing(false);
    }, 700);
  };

  const filteredSpecialists =
    selectedAgentId === 'ALL'
      ? specialists
      : specialists.filter((s) => s.id === selectedAgentId);

  return (
    <div className="w-full flex flex-col bg-[var(--ak-color-bg-app)] text-[var(--ak-color-text-primary)] select-none relative isolate">
      {/* ═══════════════════════════════════════════════════════════════════
          BREADCRUMBS & 4-STAGE TRAVERSAL HEADER
          1. Triage -> 2. Attending exam -> 3. Case room -> 4. Physician sign-off
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-[var(--ak-color-bg-surface)] border-b border-[var(--ak-color-border-subtle)]">
        {/* Breadcrumb Links */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <button
            type="button"
            onClick={onBackToPortal}
            className="text-[var(--ak-color-primary)] hover:underline font-semibold flex items-center gap-1 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Virtual Hospital</span>
          </button>
          <span className="text-[var(--ak-color-text-muted)]">/</span>
          <button
            type="button"
            onClick={() => onNavigateTab?.('STAFF')}
            className="text-[var(--ak-color-text-secondary)] hover:text-[var(--ak-color-primary)] font-medium transition cursor-pointer"
          >
            Staff Roster
          </button>
          <span className="text-[var(--ak-color-text-muted)]">/</span>
          <span className="text-[var(--ak-color-text-primary)] font-semibold">Case Room</span>
        </div>

        {/* 4-Step Trajectory Pathway */}
        <div className="flex items-center gap-1.5 sm:gap-3 overflow-x-auto text-xs font-mono">
          {[
            { num: 1, label: 'Triage' },
            { num: 2, label: 'Attending exam' },
            { num: 3, label: 'Case room' },
            { num: 4, label: 'Physician sign-off' },
          ].map((step) => {
            const isCurrent = activeStep === step.num;
            const isDone = activeStep > step.num;
            return (
              <button
                key={step.num}
                type="button"
                onClick={() => setActiveStep(step.num)}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full transition text-[11px] cursor-pointer ${
                  isCurrent
                    ? 'bg-[var(--ak-color-primary)] text-white font-semibold shadow-xs'
                    : isDone
                    ? 'bg-[var(--ak-color-success-soft)] text-[var(--ak-color-success)] border border-[var(--ak-color-success)]/30'
                    : 'bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-muted)] hover:text-[var(--ak-color-text-primary)]'
                }`}
              >
                <span className="font-bold">{step.num}.</span>
                <span>{step.label}</span>
                {isCurrent && <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
              </button>
            );
          })}
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {cases.length > 0 && (
            <select
              value={selectedCaseId}
              onChange={(e) => onSelectCase(e.target.value)}
              className="text-xs font-mono px-2 py-1 rounded border border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)] cursor-pointer"
            >
              <option value="VH-0417">VH-0417 (31F Severe Preeclampsia Demo)</option>
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} - {c.name} ({c.acuity})
                </option>
              ))}
            </select>
          )}

          <button
            type="button"
            onClick={handleToggleConsensus}
            disabled={isSynthesizing}
            className={`px-3 py-1 text-xs font-medium rounded-lg flex items-center gap-1.5 transition cursor-pointer ${
              hasConsensus
                ? 'bg-[var(--ak-color-success-soft)] text-[var(--ak-color-success)] border border-[var(--ak-color-success)]'
                : 'bg-[var(--ak-color-primary)] text-white hover:opacity-90'
            }`}
          >
            {isSynthesizing ? (
              <>
                <RefreshCw className="w-3 h-3 animate-spin" />
                <span>Synthesizing...</span>
              </>
            ) : hasConsensus ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Consensus Reached (6/6)</span>
              </>
            ) : (
              <>
                <RotateCcw className="w-3 h-3" />
                <span>Simulate Agent Agreement</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* ═══════════════════════════════════════════════════════════════════
            CASE HEADER & CHIEF FINDINGS SUMMARY STRIP
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="bg-[var(--ak-color-bg-surface)] border border-[var(--ak-color-border-subtle)] rounded-xl p-5 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
            <Badge variant="primary" size="sm">
              Synthetic demonstration case
            </Badge>
            <span className="text-[11px] font-mono text-[var(--ak-color-text-muted)]">
              Encounter ID: {currentCase?.id || 'VH-0417'} · ESI Level 1/2 Emergency
            </span>
          </div>

          <h1 className="text-xl sm:text-2xl font-bold text-[var(--ak-color-text-primary)] tracking-tight font-sans">
            {isDemoCase
              ? 'VH-0417 · 31 F · 34 + 2 weeks pregnant'
              : `${currentCase?.id} · ${currentCase?.age}yo ${currentCase?.sex} · ${currentCase?.name}`}
          </h1>

          <p className="text-sm text-[var(--ak-color-text-secondary)] mt-1.5 font-medium leading-relaxed">
            {isDemoCase
              ? 'Severe headache for 6 h, flashing lights, right upper abdominal pain.'
              : currentCase?.chief_complaint || 'Evaluating admitted clinical presentation.'}
          </p>

          {/* High-Acuity Metrics Highlight Strip */}
          <div className="mt-4 pt-3.5 border-t border-[var(--ak-color-border-subtle)] flex flex-wrap items-center gap-2 text-xs font-mono">
            {isDemoCase ? (
              <>
                <span className="px-2.5 py-1 rounded bg-red-500/10 text-red-600 dark:text-red-400 font-bold border border-red-500/20">
                  BP 168/112
                </span>
                <span className="px-2.5 py-1 rounded bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)] font-bold border border-[var(--ak-color-border-subtle)]">
                  HR 104
                </span>
                <span className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 font-bold border border-amber-500/20">
                  Platelets 88
                </span>
                <span className="px-2.5 py-1 rounded bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)] font-bold border border-[var(--ak-color-border-subtle)]">
                  AST / ALT 142 / 156
                </span>
                <span className="px-2.5 py-1 rounded bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)] font-bold border border-[var(--ak-color-border-subtle)]">
                  LDH 720
                </span>
                <span className="px-2.5 py-1 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 font-bold border border-purple-500/20">
                  Urine protein 3+
                </span>
                <span className="px-2.5 py-1 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 font-bold border border-blue-500/20">
                  Clonus 2 beats
                </span>
              </>
            ) : (
              <>
                <span className="px-2.5 py-1 rounded bg-red-500/10 text-red-600 font-bold border border-red-500/20">
                  BP 138/88
                </span>
                <span className="px-2.5 py-1 rounded bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)] font-bold border border-[var(--ak-color-border-subtle)]">
                  HR 78 bpm
                </span>
                <span className="px-2.5 py-1 rounded bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)] font-bold border border-[var(--ak-color-border-subtle)]">
                  SpO2 98%
                </span>
              </>
            )}
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            ALL FINDINGS COLLAPSIBLE SECTION (VITALS, LABS, EXAMINATION)
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="bg-[var(--ak-color-bg-surface)] border border-[var(--ak-color-border-subtle)] rounded-xl overflow-hidden shadow-xs">
          <button
            type="button"
            onClick={() => setIsFindingsExpanded((prev) => !prev)}
            className="w-full px-5 py-3.5 bg-[var(--ak-color-bg-subtle)] flex items-center justify-between text-left cursor-pointer transition hover:bg-[var(--ak-color-bg-surface)]"
          >
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-[var(--ak-color-primary)]" />
              <h2 className="text-sm font-semibold text-[var(--ak-color-text-primary)] tracking-wide uppercase font-mono">
                All findings
              </h2>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-[var(--ak-color-text-muted)]">
              <span>{isFindingsExpanded ? 'Hide clinical telemetry' : 'Show full panel'}</span>
              {isFindingsExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </div>
          </button>

          {isFindingsExpanded && (
            <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-5 border-t border-[var(--ak-color-border-subtle)]">
              {/* Column 1: Vitals */}
              <div className="space-y-3">
                <div className="flex items-center gap-1.5 pb-1 border-b border-[var(--ak-color-border-subtle)]">
                  <HeartPulse className="w-4 h-4 text-red-500" />
                  <h3 className="text-xs font-bold text-[var(--ak-color-text-primary)] uppercase tracking-wider font-mono">
                    Vitals
                  </h3>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-baseline p-2 rounded bg-[var(--ak-color-bg-subtle)]">
                    <span className="text-[var(--ak-color-text-muted)] font-mono">Blood pressure</span>
                    <span className="font-bold text-red-600 dark:text-red-400 font-mono">168/112 mmHg</span>
                  </div>
                  <div className="flex justify-between items-baseline p-2 rounded bg-[var(--ak-color-bg-subtle)]">
                    <span className="text-[var(--ak-color-text-muted)] font-mono">Heart rate</span>
                    <span className="font-semibold text-[var(--ak-color-text-primary)] font-mono">104 bpm</span>
                  </div>
                  <div className="flex justify-between items-baseline p-2 rounded bg-[var(--ak-color-bg-subtle)]">
                    <span className="text-[var(--ak-color-text-muted)] font-mono">SpO₂</span>
                    <span className="font-semibold text-[var(--ak-color-text-primary)] font-mono">97 %</span>
                  </div>
                  <div className="flex justify-between items-baseline p-2 rounded bg-[var(--ak-color-bg-subtle)]">
                    <span className="text-[var(--ak-color-text-muted)] font-mono">Resp. rate</span>
                    <span className="font-semibold text-[var(--ak-color-text-primary)] font-mono">18 /min</span>
                  </div>
                  <div className="flex justify-between items-baseline p-2 rounded bg-[var(--ak-color-bg-subtle)]">
                    <span className="text-[var(--ak-color-text-muted)] font-mono">Temperature</span>
                    <span className="font-semibold text-[var(--ak-color-text-primary)] font-mono">37.0 °C</span>
                  </div>
                  <div className="flex justify-between items-baseline p-2 rounded bg-purple-500/10 border border-purple-500/20">
                    <span className="text-purple-700 dark:text-purple-300 font-medium font-mono flex items-center gap-1">
                      <Baby className="w-3.5 h-3.5" /> Fetal HR
                    </span>
                    <span className="font-bold text-purple-700 dark:text-purple-300 font-mono">145 bpm · CTG Cat. I</span>
                  </div>
                </div>
              </div>

              {/* Column 2: Labs · 14:13 */}
              <div className="space-y-3">
                <div className="flex items-center gap-1.5 pb-1 border-b border-[var(--ak-color-border-subtle)]">
                  <FileText className="w-4 h-4 text-[var(--ak-color-primary)]" />
                  <h3 className="text-xs font-bold text-[var(--ak-color-text-primary)] uppercase tracking-wider font-mono">
                    Labs · 14:13
                  </h3>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 rounded bg-amber-500/10 border border-amber-500/20 flex flex-col justify-between">
                    <span className="text-[10px] text-[var(--ak-color-text-muted)] font-mono">Platelets</span>
                    <span className="text-sm font-bold text-amber-600 dark:text-amber-400 font-mono">88 ×10⁹/L</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex flex-col justify-between">
                    <span className="text-[10px] text-[var(--ak-color-text-muted)] font-mono">AST</span>
                    <span className="text-sm font-bold text-[var(--ak-color-text-primary)] font-mono">142 U/L</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex flex-col justify-between">
                    <span className="text-[10px] text-[var(--ak-color-text-muted)] font-mono">ALT</span>
                    <span className="text-sm font-bold text-[var(--ak-color-text-primary)] font-mono">156 U/L</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex flex-col justify-between">
                    <span className="text-[10px] text-[var(--ak-color-text-muted)] font-mono">LDH</span>
                    <span className="text-sm font-bold text-[var(--ak-color-text-primary)] font-mono">720 U/L</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex flex-col justify-between">
                    <span className="text-[10px] text-[var(--ak-color-text-muted)] font-mono">Haemoglobin</span>
                    <span className="text-sm font-semibold text-[var(--ak-color-text-primary)] font-mono">10.9 g/dL</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex flex-col justify-between">
                    <span className="text-[10px] text-[var(--ak-color-text-muted)] font-mono">Creatinine</span>
                    <span className="text-sm font-semibold text-[var(--ak-color-text-primary)] font-mono">87 µmol/L</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex flex-col justify-between">
                    <span className="text-[10px] text-[var(--ak-color-text-muted)] font-mono">Glucose</span>
                    <span className="text-sm font-semibold text-[var(--ak-color-text-primary)] font-mono">5.1 mmol/L</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex flex-col justify-between">
                    <span className="text-[10px] text-[var(--ak-color-text-muted)] font-mono">Fibrinogen</span>
                    <span className="text-sm font-semibold text-[var(--ak-color-text-primary)] font-mono">3.4 g/L</span>
                  </div>
                </div>
              </div>

              {/* Column 3: Examination */}
              <div className="space-y-3">
                <div className="flex items-center gap-1.5 pb-1 border-b border-[var(--ak-color-border-subtle)]">
                  <Stethoscope className="w-4 h-4 text-emerald-500" />
                  <h3 className="text-xs font-bold text-[var(--ak-color-text-primary)] uppercase tracking-wider font-mono">
                    Examination
                  </h3>
                </div>

                <ul className="space-y-2 text-xs text-[var(--ak-color-text-secondary)]">
                  <li className="flex items-start gap-2 p-2 rounded bg-[var(--ak-color-bg-subtle)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--ak-color-primary)] mt-1.5 shrink-0" />
                    <span>Brisk reflexes, 2 beats of ankle clonus</span>
                  </li>
                  <li className="flex items-start gap-2 p-2 rounded bg-[var(--ak-color-bg-subtle)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--ak-color-primary)] mt-1.5 shrink-0" />
                    <span>Right upper quadrant and epigastric tenderness</span>
                  </li>
                  <li className="flex items-start gap-2 p-2 rounded bg-[var(--ak-color-bg-subtle)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--ak-color-primary)] mt-1.5 shrink-0" />
                    <span>GCS 15, no focal deficit</span>
                  </li>
                  <li className="flex items-start gap-2 p-2 rounded bg-[var(--ak-color-bg-subtle)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--ak-color-primary)] mt-1.5 shrink-0" />
                    <span>Chest clear to auscultation</span>
                  </li>
                  <li className="flex items-start gap-2 p-2 rounded bg-[var(--ak-color-bg-subtle)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--ak-color-primary)] mt-1.5 shrink-0" />
                    <span>G2 P1, no prior steroids, no asthma</span>
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            MEDGEMMA ROUTER & SPECIALIST ASSIGNMENT PERCENTAGES
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="bg-[var(--ak-color-bg-surface)] border border-[var(--ak-color-border-subtle)] rounded-xl p-5 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-[var(--ak-color-primary-soft)] text-[var(--ak-color-primary)] flex items-center justify-center border border-[var(--ak-color-border-subtle)] shadow-xs">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-[var(--ak-color-text-primary)] tracking-tight">
                    MedGemma router
                  </h2>
                  <Badge variant="primary" size="sm">
                    {isRunning ? 'Routing the case…' : 'Multi-Agent Matrix'}
                  </Badge>
                </div>
                <p className="text-xs text-[var(--ak-color-text-muted)]">
                  Autonomous case triage and consensus routing based on clinical presentation.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 font-mono text-xs">
              <span className="text-[var(--ak-color-text-muted)]">Routing confidence:</span>
              <span className="font-bold text-[var(--ak-color-primary)]">98.4%</span>
              <span className="w-2 h-2 rounded-full bg-[var(--ak-color-success)] animate-pulse" />
            </div>
          </div>

          {/* Router Assignment Percentages Grid */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between text-xs font-mono text-[var(--ak-color-text-muted)] pb-1 border-b border-[var(--ak-color-border-subtle)]">
              <span>SPECIALTY DESTINATION</span>
              <span>ASSIGNMENT WEIGHT</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {specialists.map((spec) => {
                const isSelected = selectedAgentId === spec.id;
                return (
                  <div
                    key={spec.id}
                    onClick={() => setSelectedAgentId(isSelected ? 'ALL' : spec.id)}
                    className={`p-3 rounded-lg border transition-all cursor-pointer flex flex-col justify-between gap-2 ${
                      isSelected
                        ? 'border-[var(--ak-color-primary)] bg-[var(--ak-color-primary-soft)]'
                        : 'border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-subtle)] hover:border-[var(--ak-color-primary)]/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <img
                          src={spec.avatar}
                          alt={spec.name}
                          className="w-8 h-8 rounded-lg object-cover border border-[var(--ak-color-border-subtle)]"
                        />
                        <div>
                          <div className="text-xs font-bold text-[var(--ak-color-text-primary)]">
                            {spec.specialty}
                          </div>
                          <div className="text-[10px] text-[var(--ak-color-text-muted)] font-mono">
                            {spec.name}
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <span className="font-mono text-sm font-bold text-[var(--ak-color-primary)]">
                          {spec.percentage}%
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-[var(--ak-color-bg-app)] h-2 rounded-full overflow-hidden border border-[var(--ak-color-border-subtle)]">
                      <div
                        className="h-full bg-[var(--ak-color-primary)] rounded-full transition-all duration-500"
                        style={{ width: `${spec.percentage}%` }}
                      />
                    </div>

                    <div className="text-[10px] text-[var(--ak-color-text-muted)] truncate">
                      {spec.rationale}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            SPECIALIST AGENTS (INDEPENDENT REVIEW)
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="bg-[var(--ak-color-bg-surface)] border border-[var(--ak-color-border-subtle)] rounded-xl p-5 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div>
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-[var(--ak-color-primary)]" />
                <h2 className="text-base font-bold text-[var(--ak-color-text-primary)] tracking-tight">
                  Specialist agents
                </h2>
                <Badge variant="outline" size="sm">
                  Independent review
                </Badge>
              </div>
              <p className="text-xs text-[var(--ak-color-text-muted)] mt-0.5">
                MedGemma router · Case routed to six specialists. Select an agent, here or in the router above, to read only its messages.
              </p>
            </div>

            {/* Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
              <button
                type="button"
                onClick={() => setSelectedAgentId('ALL')}
                className={`px-2.5 py-1 rounded-md transition cursor-pointer ${
                  selectedAgentId === 'ALL'
                    ? 'bg-[var(--ak-color-primary)] text-white font-semibold'
                    : 'bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-muted)] hover:text-[var(--ak-color-text-primary)]'
                }`}
              >
                All (6)
              </button>
              {specialists.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setSelectedAgentId(s.id)}
                  className={`px-2.5 py-1 rounded-md transition cursor-pointer flex items-center gap-1 ${
                    selectedAgentId === s.id
                      ? 'bg-[var(--ak-color-primary)] text-white font-semibold'
                      : 'bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-muted)] hover:text-[var(--ak-color-text-primary)]'
                  }`}
                >
                  <span>{s.specialty}</span>
                  <span className="opacity-70 text-[10px]">({s.percentage}%)</span>
                </button>
              ))}
            </div>
          </div>

          {/* Specialist Cards Stream */}
          <div className="space-y-4">
            {filteredSpecialists.map((spec) => (
              <div
                key={spec.id}
                className="p-4 rounded-xl border border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-subtle)] space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-[var(--ak-color-border-subtle)]">
                  <div className="flex items-center gap-3">
                    <img
                      src={spec.avatar}
                      alt={spec.name}
                      className="w-10 h-10 rounded-xl object-cover border border-[var(--ak-color-primary)] shadow-xs"
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-[var(--ak-color-text-primary)]">
                          {spec.name}
                        </span>
                        <Badge variant="primary" size="sm">
                          {spec.roleTag}
                        </Badge>
                      </div>
                      <div className="text-xs text-[var(--ak-color-text-muted)] flex items-center gap-2 mt-0.5">
                        <span className="text-[var(--ak-color-primary)] font-medium">{spec.specialty}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1 font-mono text-[11px]">
                          <BookOpen className="w-3 h-3 text-[var(--ak-color-primary)]" />
                          <span>{spec.book}</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 font-mono text-xs">
                    <Badge variant="success" size="sm">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--ak-color-success)] animate-pulse mr-1" />
                      Opinion logged
                    </Badge>
                  </div>
                </div>

                <div className="text-xs text-[var(--ak-color-text-primary)] leading-relaxed bg-[var(--ak-color-bg-surface)] p-3.5 rounded-lg border border-[var(--ak-color-border-subtle)] font-sans">
                  {spec.clinicalOpinion}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            WORKING DIAGNOSIS & MULTI-AGENT CONSENSUS GATE
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Working Diagnosis Card */}
          <div className="bg-[var(--ak-color-bg-surface)] border border-[var(--ak-color-border-subtle)] rounded-xl p-5 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-semibold text-[var(--ak-color-text-muted)] uppercase tracking-wider">
                  Working diagnosis
                </span>
                <Badge variant={hasConsensus ? 'success' : 'warning'} size="sm">
                  {hasConsensus ? 'Consensus Achieved' : 'Differential Open'}
                </Badge>
              </div>

              <h2 className="text-xl font-bold text-[var(--ak-color-text-primary)] tracking-tight">
                {isDemoCase ? 'Preeclampsia with severe features' : 'Acute Myocardial Ischemia / NSTEMI'}
              </h2>

              <div className="flex items-center gap-2 mt-2 font-mono text-xs text-[var(--ak-color-text-secondary)]">
                <span>Confidence:</span>
                <span className="font-bold text-[var(--ak-color-primary)]">
                  {hasConsensus ? '0.94' : '0.62'}
                </span>
                <span>•</span>
                <span>{hasConsensus ? '6 of 6 agree' : '0 of 6 agree'}</span>
              </div>

              <div className="mt-4 pt-3 border-t border-[var(--ak-color-border-subtle)] space-y-2 text-xs">
                <div>
                  <span className="font-semibold text-[var(--ak-color-text-primary)]">Less likely: </span>
                  <span className="text-[var(--ak-color-text-secondary)]">
                    acute fatty liver, acute cholecystitis, TTP / HUS.
                  </span>
                </div>
                <div>
                  <span className="font-semibold text-amber-600 dark:text-amber-400">Watch for: </span>
                  <span className="text-[var(--ak-color-text-secondary)]">
                    a focal deficit or seizure despite magnesium (PRES, venous thrombosis).
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-[var(--ak-color-border-subtle)] text-[11px] font-mono text-[var(--ak-color-text-muted)] flex items-center justify-between">
              <span>Grounding: Harrison RAG + Williams OB</span>
              <span className="text-[var(--ak-color-success)] font-medium">Clinically Grounded</span>
            </div>
          </div>

          {/* Plan Gate Card */}
          <div className="bg-[var(--ak-color-bg-surface)] border border-[var(--ak-color-border-subtle)] rounded-xl p-5 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-semibold text-[var(--ak-color-text-muted)] uppercase tracking-wider">
                  Clinical Action Plan
                </span>
                <Badge variant={hasConsensus ? 'success' : 'neutral'} size="sm">
                  {hasConsensus ? '7 of 7 agreed' : '0 of 7 agreed'}
                </Badge>
              </div>

              <h3 className="text-base font-bold text-[var(--ak-color-text-primary)]">
                {hasConsensus ? 'Multidisciplinary Treatment Consensus' : 'Plan locked pending specialist agreement'}
              </h3>

              {hasConsensus ? (
                <div className="mt-3 space-y-2 text-xs text-[var(--ak-color-text-secondary)] max-h-48 overflow-y-auto pr-1">
                  <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-800 dark:text-emerald-300 font-medium flex items-start gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    <span>1. IV Magnesium sulfate 4g loading dose over 20 min, then 1-2g/h maintenance infusion.</span>
                  </div>
                  <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-800 dark:text-emerald-300 font-medium flex items-start gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    <span>2. IV Labetalol 20mg IV bolus every 10-20 min (or Hydralazine) targeting BP 140-150 / 90-100.</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex items-start gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[var(--ak-color-primary)] shrink-0 mt-0.5" />
                    <span>3. Strict fluid balance restriction (80 mL/h) and Foley catheter with hourly urometer tracking.</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex items-start gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[var(--ak-color-primary)] shrink-0 mt-0.5" />
                    <span>4. Continuous electronic fetal monitoring (CTG Cat. I confirmed, reassuring baseline 145 bpm).</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex items-start gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[var(--ak-color-primary)] shrink-0 mt-0.5" />
                    <span>5. Antenatal corticosteroids (Betamethasone 12mg IM q24h x 2 doses) for fetal pulmonary maturity.</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex items-start gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[var(--ak-color-primary)] shrink-0 mt-0.5" />
                    <span>6. Emergent bedside right upper quadrant ultrasound to evaluate hepatic capsule & exclude hematoma.</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--ak-color-bg-subtle)] flex items-start gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[var(--ak-color-primary)] shrink-0 mt-0.5" />
                    <span>7. Multidisciplinary delivery planning following maternal hemodynamic stabilization.</span>
                  </div>
                </div>
              ) : (
                <div className="mt-4 p-6 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-dashed border-[var(--ak-color-border-subtle)] text-center flex flex-col items-center justify-center">
                  <Lock className="w-6 h-6 text-[var(--ak-color-text-muted)] mb-2" />
                  <p className="text-xs text-[var(--ak-color-text-muted)] font-mono">
                    Available when the agents agree.
                  </p>
                  <button
                    type="button"
                    onClick={handleToggleConsensus}
                    className="mt-3 text-xs text-[var(--ak-color-primary)] hover:underline font-semibold cursor-pointer"
                  >
                    Simulate agent agreement
                  </button>
                </div>
              )}
            </div>

            <div className="mt-5 pt-3 border-t border-[var(--ak-color-border-subtle)]">
              <p className="text-[11px] text-[var(--ak-color-text-muted)] italic leading-relaxed">
                Synthetic case for demonstration. The physician confirms, edits or rejects every recommendation before it reaches the patient.
              </p>
            </div>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            OPTIONAL TECHNICAL ENCOUNTER TRAJECTORY STEPPER (EXPANDABLE)
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="pt-2">
          <button
            type="button"
            onClick={() => setShowTechnicalStepper((prev) => !prev)}
            className="flex items-center gap-1.5 text-xs font-mono text-[var(--ak-color-text-muted)] hover:text-[var(--ak-color-primary)] transition cursor-pointer"
          >
            <span>{showTechnicalStepper ? 'Hide technical stepper' : 'View underlying sequence & state flow'}</span>
            {showTechnicalStepper ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showTechnicalStepper && (
            <div className="mt-3 animate-in fade-in duration-200">
              <ActiveTrajectoryStepper
                progress={hasConsensus ? 85 : 35}
                isRunning={isRunning}
                currentCase={currentCase}
                latestEvent={events.length > 0 ? events[events.length - 1] : null}
                activeDepartment={activeDepartment}
                doctorAction={doctorAction}
                onOpenDepartmentStation={onOpenDepartmentStation}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HospitalFlowDiagram;
