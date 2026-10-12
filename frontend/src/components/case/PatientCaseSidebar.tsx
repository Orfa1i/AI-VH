import React, { useState } from 'react';
import {
  User,
  HeartPulse,
  Activity,
  AlertCircle,
  FileText,
  CheckCircle2,
  ChevronDown,
  Copy,
  Check,
  Bed,
  Pill,
  ShieldAlert,
  Thermometer,
  Layers,
  ChevronUp,
} from 'lucide-react';
import type { PatientRecord } from '../../types';

export interface VitalItemData {
  label: string;
  val: string;
  unit: string;
  status: 'normal' | 'abnormal' | 'critical' | 'low' | 'high';
  refRange?: string;
  icon?: React.ReactNode;
}

export interface LabItemData {
  name: string;
  val: string;
  ref?: string;
  flag?: string;
  status?: 'normal' | 'low' | 'high' | 'critical';
}

export interface ImagingItemData {
  title: string;
  mod: string;
  desc: string;
}

export interface PlanItemData {
  id: string;
  t: string;
  done?: boolean;
  own?: string[];
}

export interface PatientCaseSidebarProps {
  patient?: PatientRecord | null;
  activeCase?: any;
  className?: string;
  onPlanItemToggle?: (itemId: string) => void;
  onDischarge?: (patientId: string) => void;
}

export const PatientCaseSidebar: React.FC<PatientCaseSidebarProps> = ({
  patient,
  activeCase,
  className = '',
  onPlanItemToggle,
  onDischarge,
}) => {
  // Accordion state
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    complaint: true,
    vitals: true,
    history: true,
    labs: false,
    plan: true,
  });

  const [copiedMrn, setCopiedMrn] = useState<boolean>(false);
  const [planState, setPlanState] = useState<Record<string, boolean>>({});

  const toggleSection = (sectionKey: string) => {
    setOpenSections((prev) => ({
      ...prev,
      [sectionKey]: !prev[sectionKey],
    }));
  };

  const areAllExpanded = Object.values(openSections).every(Boolean);

  const toggleAllSections = () => {
    const nextVal = !areAllExpanded;
    setOpenSections({
      complaint: nextVal,
      vitals: nextVal,
      history: nextVal,
      labs: nextVal,
      plan: nextVal,
    });
  };

  // Resolve patient details combining PatientRecord and activeCase fallback
  const caseData = patient?.case_data;
  const name = patient?.name || activeCase?.name || 'Elena Vance';
  const mrn = patient?.mrn || activeCase?.mrn || '#VH-8921-OB';
  const age = patient?.age ?? activeCase?.age ?? 32;
  const sex = patient?.sex || activeCase?.sex || 'Female';
  const department = patient?.assigned_department || activeCase?.assigned_department || 'OBSTETRICS';
  const bedNumber = patient?.bed_number || activeCase?.bed_number || 'OB-BAY-01';
  const admissionStatus = patient?.admission_status || activeCase?.admission_status || 'ADMITTED';
  const triageAcuity = patient?.triage_acuity || activeCase?.triage_acuity || 'EMERGENT';
  const chiefComplaint =
    patient?.chief_complaint ||
    activeCase?.chief_complaint ||
    'Severe throbbing frontal headache, blurred vision with floaters, sharp right upper quadrant pain.';
  const hpi =
    patient?.history_of_present_illness ||
    caseData?.history_of_present_illness ||
    activeCase?.hpi ||
    'Patient presenting with acute-onset symptoms. Monitored for clinical triage and multidisciplinary deliberation.';
  const pmhx: string[] =
    patient?.past_medical_history ||
    caseData?.past_medical_history ||
    activeCase?.pmhx || [
      'Nulliparous until current gestation',
      'Gestational hypertension diagnosed at 28 weeks',
    ];
  const medications: string[] =
    patient?.medications ||
    caseData?.medications ||
    activeCase?.medications || [
      'Prenatal multivitamins PO Daily',
      'Labetalol 100mg PO BID',
    ];
  const allergies: string[] =
    patient?.allergies ||
    caseData?.allergies ||
    activeCase?.allergies || ['Sulfa drugs (Hives)'];

  // Handle MRN copy
  const handleCopyMrn = () => {
    navigator.clipboard?.writeText(mrn);
    setCopiedMrn(true);
    setTimeout(() => setCopiedMrn(false), 1800);
  };

  // Resolve Vitals
  const vitalsList: VitalItemData[] = React.useMemo(() => {
    if (activeCase?.vitals && Array.isArray(activeCase.vitals)) {
      return activeCase.vitals.map((v: any) => ({
        label: v.label || 'Vital',
        val: v.val || '—',
        unit: v.unit || '',
        status: v.status || 'normal',
        refRange: v.refRange,
      }));
    }

    const bv = patient?.baseline_vitals || caseData?.baseline_vitals;
    const hr = bv?.heart_rate ?? 88;
    const sbp = bv?.systolic_bp ?? 178;
    const dbp = bv?.diastolic_bp ?? 112;
    const rr = bv?.respiratory_rate ?? 18;
    const spo2 = bv?.spo2_percent ?? 98;
    const temp = bv?.temperature_c ?? 36.8;
    const pain = bv?.pain_score ?? 7;

    return [
      {
        label: 'BP',
        val: `${sbp}/${dbp}`,
        unit: 'mmHg',
        status: sbp >= 160 || dbp >= 110 ? 'critical' : sbp >= 140 ? 'abnormal' : 'normal',
        refRange: '90-120 / 60-80',
        icon: <Activity className="w-3.5 h-3.5" />,
      },
      {
        label: 'Heart Rate',
        val: String(hr),
        unit: 'bpm',
        status: hr >= 120 ? 'critical' : hr >= 100 || hr < 60 ? 'abnormal' : 'normal',
        refRange: '60-100',
        icon: <HeartPulse className="w-3.5 h-3.5" />,
      },
      {
        label: 'Resp Rate',
        val: String(rr),
        unit: '/min',
        status: rr >= 28 ? 'critical' : rr >= 20 || rr < 12 ? 'abnormal' : 'normal',
        refRange: '12-20',
        icon: <Activity className="w-3.5 h-3.5" />,
      },
      {
        label: 'SpO₂',
        val: `${spo2}%`,
        unit: 'RA',
        status: spo2 < 92 ? 'critical' : spo2 < 95 ? 'abnormal' : 'normal',
        refRange: '≥95%',
        icon: <Activity className="w-3.5 h-3.5" />,
      },
      {
        label: 'Temperature',
        val: `${temp}°C`,
        unit: '',
        status: temp >= 38.5 ? 'critical' : temp >= 37.8 || temp < 36.0 ? 'abnormal' : 'normal',
        refRange: '36.5-37.5',
        icon: <Thermometer className="w-3.5 h-3.5" />,
      },
      {
        label: 'Pain / GCS',
        val: `${pain}/10`,
        unit: '',
        status: pain >= 8 ? 'critical' : pain >= 5 ? 'abnormal' : 'normal',
        refRange: '0-10 scale',
        icon: <AlertCircle className="w-3.5 h-3.5" />,
      },
    ];
  }, [patient, activeCase, caseData]);

  // Resolve Labs
  const labsList: LabItemData[] = React.useMemo(() => {
    if (activeCase?.labs && Array.isArray(activeCase.labs)) {
      return activeCase.labs;
    }
    if (caseData?.labs && Array.isArray(caseData.labs)) {
      return caseData.labs;
    }
    return [
      { name: 'Platelets', val: '62 ×10⁹/L', ref: '150-400', flag: 'Low', status: 'critical' },
      { name: 'AST / ALT', val: '210 / 195 U/L', ref: '<35', flag: 'High', status: 'critical' },
      { name: 'LDH', val: '680 U/L', ref: '140-280', flag: 'High', status: 'high' },
      { name: 'Urine PCR', val: '1.8 mg/mg', ref: '<0.3', flag: 'High', status: 'high' },
    ];
  }, [activeCase, caseData]);

  // Resolve Imaging - only included if there is actual data related to the case
  const imagingList: ImagingItemData[] = React.useMemo(() => {
    if (activeCase?.imaging && Array.isArray(activeCase.imaging) && activeCase.imaging.length > 0) {
      return activeCase.imaging;
    }
    if (caseData?.imaging && Array.isArray(caseData.imaging) && caseData.imaging.length > 0) {
      return caseData.imaging;
    }
    const findings = (activeCase as any)?.imaging_findings || (caseData as any)?.imaging_findings;
    if (findings && typeof findings === 'object' && !Array.isArray(findings) && Object.keys(findings).length > 0) {
      return Object.entries(findings).map(([title, desc]) => ({
        title,
        mod: 'Diagnostic Study',
        desc: String(desc),
      }));
    }
    return [];
  }, [activeCase, caseData]);

  // Resolve Plan
  const planItems: PlanItemData[] = React.useMemo(() => {
    if (activeCase?.plan && Array.isArray(activeCase.plan)) {
      return activeCase.plan;
    }
    return [
      { id: 'mag_sulfate', t: 'IV Magnesium Sulfate loading & maintenance infusion', done: true, own: ['ob', 'em'] },
      { id: 'bp_control', t: 'IV Labetalol titration for SBP <160, DBP <105 mmHg', done: true, own: ['ob', 'ca'] },
      { id: 'fetal_monitoring', t: 'Continuous external fetal cardiotocography monitoring', done: true, own: ['ob'] },
      { id: 'urgent_delivery', t: 'Expedited multidisciplinary cesarean delivery evaluation', done: false, own: ['ob', 'su'] },
    ];
  }, [activeCase]);

  // Acuity styling helper
  const getAcuityStyle = (acuity: string) => {
    const a = acuity.toUpperCase();
    if (a.includes('RESUSCITATION') || a.includes('ESI 1')) {
      return 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900';
    }
    if (a.includes('EMERGENT') || a.includes('ESI 2')) {
      return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900';
    }
    if (a.includes('URGENT') || a.includes('ESI 3')) {
      return 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-900';
    }
    return 'bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
  };

  // Status background style for vitals
  const getVitalCardStyle = (status: VitalItemData['status']) => {
    switch (status) {
      case 'critical':
        return 'bg-rose-50/70 dark:bg-rose-950/30 border-rose-200/80 dark:border-rose-800/40 text-rose-950 dark:text-rose-200';
      case 'abnormal':
      case 'high':
      case 'low':
        return 'bg-amber-50/70 dark:bg-amber-950/30 border-amber-200/80 dark:border-amber-800/40 text-amber-950 dark:text-amber-200';
      case 'normal':
      default:
        return 'bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200/60 dark:border-emerald-800/30 text-emerald-950 dark:text-emerald-200';
    }
  };

  const getVitalBadgeStyle = (status: VitalItemData['status']) => {
    switch (status) {
      case 'critical':
        return 'bg-rose-100 text-rose-800 dark:bg-rose-900/50 dark:text-rose-200';
      case 'abnormal':
      case 'high':
      case 'low':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200';
      case 'normal':
      default:
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200';
    }
  };

  const handleTogglePlan = (id: string) => {
    setPlanState((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
    onPlanItemToggle?.(id);
  };

  return (
    <aside
      aria-label="Patient Case Sidebar"
      className={`w-full max-w-[380px] h-full flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 select-none shadow-xs text-slate-800 dark:text-slate-100 ${className}`}
    >
      {/* =========================================================================
          1. FIXED HEADER: Patient Summary Card
          ========================================================================= */}
      <div className="sticky top-0 z-20 shrink-0 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 p-4 transition-colors">
        <div className="flex items-start justify-between gap-2 mb-2.5">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-9 h-9 rounded-full bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800/60 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-sm shrink-0">
              <User className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <h2 className="text-base font-bold text-slate-900 dark:text-white truncate tracking-tight font-sans">
                {name}
              </h2>
              <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-mono">
                <span className="font-semibold text-slate-700 dark:text-slate-300">{mrn}</span>
                <button
                  type="button"
                  onClick={handleCopyMrn}
                  title="Copy MRN"
                  className="p-0.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors cursor-pointer"
                  aria-label="Copy Medical Record Number"
                >
                  {copiedMrn ? (
                    <Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-1 shrink-0">
            {/* Admission Status */}
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              {admissionStatus}
            </span>
            {/* Triage Acuity Tag */}
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${getAcuityStyle(
                triageAcuity
              )}`}
            >
              {triageAcuity}
            </span>
          </div>
        </div>

        {/* Demographics & Location Quick Strip */}
        <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 dark:bg-slate-800/60 rounded-lg p-2 border border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
            <span className="text-[11px] text-slate-400 font-medium">Demog:</span>
            <span className="font-semibold font-mono">
              {age}y · {sex.slice(0, 1).toUpperCase()}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300 truncate">
            <Bed className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="truncate font-semibold text-[11px] font-mono">
              {bedNumber} ({department.slice(0, 4)})
            </span>
          </div>
        </div>

        {/* Global Expand / Collapse Control */}
        <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
          <span className="font-medium tracking-tight">Clinical Dossier Sections</span>
          <button
            type="button"
            onClick={toggleAllSections}
            className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-semibold transition-colors cursor-pointer"
          >
            {areAllExpanded ? (
              <>
                <ChevronUp className="w-3.5 h-3.5" /> Collapse all
              </>
            ) : (
              <>
                <ChevronDown className="w-3.5 h-3.5" /> Expand all
              </>
            )}
          </button>
        </div>
      </div>

      {/* =========================================================================
          2. SCROLLABLE ACCORDION CONTAINER (Custom Thin Scrollbar)
          ========================================================================= */}
      <div className="flex-1 overflow-y-auto custom-thin-scrollbar p-3 space-y-2.5">
        {/* Section 1: Chief Complaint */}
        <div className="rounded-xl border border-slate-200/90 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900/60 shadow-2xs">
          <button
            type="button"
            onClick={() => toggleSection('complaint')}
            aria-expanded={openSections.complaint}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <div className="p-1 rounded bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800/40">
                <AlertCircle className="w-3.5 h-3.5" />
              </div>
              <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-sans">
                Chief Complaint
              </span>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${
                openSections.complaint ? 'rotate-180' : ''
              }`}
            />
          </button>

          {openSections.complaint && (
            <div className="p-3 pt-0 text-xs text-slate-700 dark:text-slate-300 space-y-2">
              <div className="p-2.5 rounded-lg bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/70 dark:border-amber-800/30 text-amber-950 dark:text-amber-200 font-medium leading-relaxed">
                "{chiefComplaint}"
              </div>
            </div>
          )}
        </div>

        {/* Section 2: Vital Signs (Grid Layout with Subtle Status Tints) */}
        <div className="rounded-xl border border-slate-200/90 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900/60 shadow-2xs">
          <button
            type="button"
            onClick={() => toggleSection('vitals')}
            aria-expanded={openSections.vitals}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <div className="p-1 rounded bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40">
                <HeartPulse className="w-3.5 h-3.5" />
              </div>
              <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-sans">
                Vital Signs & Telemetry
              </span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                6 Parameters
              </span>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${
                openSections.vitals ? 'rotate-180' : ''
              }`}
            />
          </button>

          {openSections.vitals && (
            <div className="p-3 pt-0">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {vitalsList.map((v, i) => (
                  <div
                    key={i}
                    className={`p-2.5 rounded-lg border flex flex-col justify-between transition-colors ${getVitalCardStyle(
                      v.status
                    )}`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-300 truncate">
                        {v.label}
                      </span>
                      <span
                        className={`text-[9px] font-bold uppercase px-1 py-0.2 rounded ${getVitalBadgeStyle(
                          v.status
                        )}`}
                      >
                        {v.status}
                      </span>
                    </div>

                    <div className="flex items-baseline gap-1 my-0.5">
                      <span className="text-base font-extrabold font-mono tracking-tight">{v.val}</span>
                      {v.unit && (
                        <span className="text-[10px] text-slate-500 dark:text-slate-400 font-sans">{v.unit}</span>
                      )}
                    </div>

                    {v.refRange && (
                      <div className="text-[9px] text-slate-400 dark:text-slate-500 font-mono mt-0.5 truncate">
                        Ref: {v.refRange}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Section 3: Clinical History (HPI, PMHx, Meds, Allergies) */}
        <div className="rounded-xl border border-slate-200/90 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900/60 shadow-2xs">
          <button
            type="button"
            onClick={() => toggleSection('history')}
            aria-expanded={openSections.history}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <div className="p-1 rounded bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800/40">
                <FileText className="w-3.5 h-3.5" />
              </div>
              <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-sans">
                Clinical History
              </span>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${
                openSections.history ? 'rotate-180' : ''
              }`}
            />
          </button>

          {openSections.history && (
            <div className="p-3 pt-0 space-y-3 text-xs">
              {/* HPI */}
              <div>
                <span className="font-semibold text-slate-500 dark:text-slate-400 uppercase text-[10px] tracking-wider block mb-1">
                  History of Present Illness (HPI)
                </span>
                <p className="text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
                  {hpi}
                </p>
              </div>

              {/* Past Medical History */}
              <div>
                <span className="font-semibold text-slate-500 dark:text-slate-400 uppercase text-[10px] tracking-wider block mb-1">
                  Past Medical History
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {pmhx.map((c, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded text-[11px] font-medium border border-slate-200 dark:border-slate-700"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>

              {/* Medications */}
              <div>
                <span className="font-semibold text-slate-500 dark:text-slate-400 uppercase text-[10px] tracking-wider block mb-1">
                  Current Medications
                </span>
                <ul className="space-y-1">
                  {medications.map((m, i) => (
                    <li
                      key={i}
                      className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/40 px-2 py-1 rounded border border-slate-100 dark:border-slate-800 text-[11px]"
                    >
                      <Pill className="w-3 h-3 text-indigo-500 shrink-0" />
                      <span className="truncate">{m}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Allergies */}
              <div>
                <span className="font-semibold text-slate-500 dark:text-slate-400 uppercase text-[10px] tracking-wider block mb-1">
                  Drug Allergies & Adverse Reactions
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {allergies.length > 0 ? (
                    allergies.map((a, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900"
                      >
                        <ShieldAlert className="w-3 h-3" />
                        {a}
                      </span>
                    ))
                  ) : (
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold text-[11px]">
                      NKDA (No Known Drug Allergies)
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Section 4: Diagnostic Labs & Imaging */}
        <div className="rounded-xl border border-slate-200/90 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900/60 shadow-2xs">
          <button
            type="button"
            onClick={() => toggleSection('labs')}
            aria-expanded={openSections.labs}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <div className="p-1 rounded bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-800/40">
                <Layers className="w-3.5 h-3.5" />
              </div>
              <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-sans">
                Labs & Diagnostic Workup
              </span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                {labsList.length} Labs
              </span>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${
                openSections.labs ? 'rotate-180' : ''
              }`}
            />
          </button>

          {openSections.labs && (
            <div className="p-3 pt-0 space-y-3 text-xs">
              {/* Labs Table */}
              <div className="space-y-1.5">
                {labsList.map((l, i) => {
                  const isCrit = l.status === 'critical' || l.flag === 'Critical';
                  const isAbn = isCrit || l.status === 'high' || l.status === 'low' || l.flag === 'High' || l.flag === 'Low';
                  return (
                    <div
                      key={i}
                      className={`flex items-center justify-between p-2 rounded-lg border text-[11px] ${
                        isCrit
                          ? 'bg-rose-50/50 dark:bg-rose-950/30 border-rose-200 dark:border-rose-900 text-rose-950 dark:text-rose-200'
                          : isAbn
                          ? 'bg-amber-50/50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900 text-amber-950 dark:text-amber-200'
                          : 'bg-slate-50 dark:bg-slate-800/40 border-slate-100 dark:border-slate-800 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <span className="font-semibold">{l.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold">{l.val}</span>
                        {l.flag && (
                          <span
                            className={`text-[9px] font-bold uppercase px-1 rounded ${
                              isCrit
                                ? 'bg-rose-200 text-rose-800 dark:bg-rose-900 dark:text-rose-200'
                                : 'bg-amber-200 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
                            }`}
                          >
                            {l.flag}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Imaging */}
              {imagingList.length > 0 && (
                <div>
                  <span className="font-semibold text-slate-500 dark:text-slate-400 uppercase text-[10px] tracking-wider block mb-1.5">
                    Imaging & Diagnostic Studies
                  </span>
                  <div className="space-y-1.5">
                    {imagingList.map((img, i) => (
                      <div
                        key={i}
                        className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-bold text-[11px] text-slate-800 dark:text-slate-200">{img.title}</span>
                          <span className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400 font-semibold">{img.mod}</span>
                        </div>
                        <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">{img.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Section 5: Clinical Plan & Orders */}
        <div className="rounded-xl border border-slate-200/90 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900/60 shadow-2xs">
          <button
            type="button"
            onClick={() => toggleSection('plan')}
            aria-expanded={openSections.plan}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <div className="p-1 rounded bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400 border border-teal-200 dark:border-teal-800/40">
                <CheckCircle2 className="w-3.5 h-3.5" />
              </div>
              <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-sans">
                Active Clinical Plan
              </span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                {planItems.length} Orders
              </span>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${
                openSections.plan ? 'rotate-180' : ''
              }`}
            />
          </button>

          {openSections.plan && (
            <div className="p-3 pt-0 space-y-2">
              {planItems.map((pl) => {
                const isChecked = planState[pl.id] ?? pl.done ?? false;
                return (
                  <div
                    key={pl.id}
                    onClick={() => handleTogglePlan(pl.id)}
                    className={`flex items-start gap-2.5 p-2 rounded-lg border transition-colors cursor-pointer ${
                      isChecked
                        ? 'bg-slate-50/60 dark:bg-slate-800/30 border-slate-200/60 dark:border-slate-800 opacity-80'
                        : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-2xs hover:border-indigo-300 dark:hover:border-indigo-700'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => {}} // Controlled by container onClick
                      className="mt-0.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                    />
                    <div className="min-w-0 flex-1">
                      <p
                        className={`text-xs leading-snug ${
                          isChecked
                            ? 'line-through text-slate-400 dark:text-slate-500'
                            : 'text-slate-800 dark:text-slate-200 font-medium'
                        }`}
                      >
                        {pl.t}
                      </p>
                      {pl.own && pl.own.length > 0 && (
                        <div className="flex items-center gap-1 mt-1">
                          {pl.own.map((o) => (
                            <span
                              key={o}
                              className="text-[9px] font-mono uppercase font-bold px-1 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                            >
                              {o}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* =========================================================================
          3. FOOTER: Clinical Quick Action Toolbar
          ========================================================================= */}
      {onDischarge && (
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <button
            type="button"
            onClick={() => onDischarge(patient?.id || activeCase?.id || '')}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 transition-colors cursor-pointer flex items-center justify-center gap-1.5"
          >
            Discharge Patient from Ward
          </button>
        </div>
      )}
    </aside>
  );
};
