import React, { useState } from 'react';
import type { BenchmarkCase, PatientRecord } from '../../types';
import {
  UserPlus,
  CheckCircle2,
  RotateCcw,
  ArrowRight,
  ShieldAlert,
  Activity,
  HeartPulse,
  Thermometer,
  Layers,
  FileSpreadsheet,
  Zap,
} from 'lucide-react';

interface CaseIntakeAdmissionSectionProps {
  cases: BenchmarkCase[];
  onPatientAdmitted: (patient: PatientRecord) => void;
  onAdmitAndSimulate?: (caseId: string) => void;
}

export const CaseIntakeAdmissionSection: React.FC<CaseIntakeAdmissionSectionProps> = ({
  onPatientAdmitted,
  onAdmitAndSimulate,
}) => {
  // Form fields (blank defaults for real-world admission testing)
  const [name, setName] = useState('');
  const [age, setAge] = useState<number | ''>('');
  const [sex, setSex] = useState<'Male' | 'Female' | 'Other'>('Male');
  const [triageAcuity, setTriageAcuity] = useState<string>('EMERGENT');
  const [assignedDepartment, setAssignedDepartment] = useState<string>('EMERGENCY');
  const [bedNumber, setBedNumber] = useState<string>('');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [hpi, setHpi] = useState('');
  const [pastMedicalHistory, setPastMedicalHistory] = useState('');
  const [medications, setMedications] = useState('');
  const [allergies, setAllergies] = useState('');

  // Vitals
  const [heartRate, setHeartRate] = useState<number>(75);
  const [systolicBp, setSystolicBp] = useState<number>(120);
  const [diastolicBp, setDiastolicBp] = useState<number>(80);
  const [respiratoryRate, setRespiratoryRate] = useState<number>(16);
  const [spo2, setSpo2] = useState<number>(98.0);
  const [temperature, setTemperature] = useState<number>(37.0);

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [lastAdmitted, setLastAdmitted] = useState<PatientRecord | null>(null);

  const handleResetForm = () => {
    setName('');
    setAge('');
    setSex('Male');
    setTriageAcuity('EMERGENT');
    setAssignedDepartment('EMERGENCY');
    setBedNumber('');
    setChiefComplaint('');
    setHpi('');
    setPastMedicalHistory('');
    setMedications('');
    setAllergies('');
    setHeartRate(75);
    setSystolicBp(120);
    setDiastolicBp(80);
    setRespiratoryRate(16);
    setSpo2(98.0);
    setTemperature(37.0);
    setSuccessMessage(null);
  };

  const handleApplyNormalVitals = () => {
    setHeartRate(72);
    setSystolicBp(120);
    setDiastolicBp(80);
    setRespiratoryRate(16);
    setSpo2(98.5);
    setTemperature(37.0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !chiefComplaint.trim()) {
      alert('Please provide patient name and chief complaint.');
      return;
    }

    setIsSubmitting(true);
    setSuccessMessage(null);

    const payload = {
      name: name.trim(),
      age: Number(age) || 0,
      sex,
      triage_acuity: triageAcuity,
      assigned_department: assignedDepartment,
      bed_number: bedNumber.trim() || `${assignedDepartment.substring(0, 3)}-01`,
      chief_complaint: chiefComplaint.trim(),
      history_of_present_illness: hpi.trim(),
      past_medical_history: pastMedicalHistory.split(',').map((s) => s.trim()).filter(Boolean),
      medications: medications.split(',').map((s) => s.trim()).filter(Boolean),
      allergies: allergies.split(',').map((s) => s.trim()).filter(Boolean),
      baseline_vitals: {
        heart_rate: Number(heartRate),
        systolic_bp: Number(systolicBp),
        diastolic_bp: Number(diastolicBp),
        respiratory_rate: Number(respiratoryRate),
        spo2: Number(spo2),
        temperature_c: Number(temperature),
      },
    };

    try {
      const res = await fetch('/api/patients/admit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || 'Failed to admit patient');
      }

      const admittedPatient: PatientRecord = await res.json();
      setLastAdmitted(admittedPatient);
      setSuccessMessage(
        `Patient ${admittedPatient.name} successfully admitted with MRN ${admittedPatient.mrn}. Bed assigned: ${admittedPatient.bed_number}.`
      );
      onPatientAdmitted(admittedPatient);
    } catch (err: any) {
      console.error('Admission failed:', err);
      alert(`Admission Error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickEncounter = () => {
    if (!lastAdmitted) return;
    if (onAdmitAndSimulate) {
      onAdmitAndSimulate(lastAdmitted.id);
    }
  };

  return (
    <div className="flex-1 p-4 md:p-6 bg-[#f8fafc] overflow-y-auto max-w-7xl mx-auto w-full telemetry-grid text-slate-900">
      {/* ═══════════════════════════════════════════════════════════════════
          TOP HEADER: CLINICAL ADMISSION PORTAL
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 shadow-xs">
              <UserPlus className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 tracking-wide font-sans uppercase">
                Clinical Case Intake &amp; Admission Portal
              </h2>
              <p className="text-xs text-slate-500 mt-0.5 font-sans">
                Authenticate real patient records with verified MRNs, ESI acuity scoring, bed allocations, and baseline telemetry.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Baseline Actions */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleApplyNormalVitals}
            className="px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs font-mono font-medium flex items-center gap-1.5 transition cursor-pointer shadow-xs"
          >
            <Zap className="w-3.5 h-3.5 text-emerald-600" />
            <span>Normal Baseline Vitals</span>
          </button>
          <button
            type="button"
            onClick={handleResetForm}
            className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-mono font-medium flex items-center gap-1.5 transition cursor-pointer shadow-xs"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
            <span>Reset Form</span>
          </button>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          SUCCESS NOTIFICATION CARD (DOUBLE-BEZEL LIGHT)
          ═══════════════════════════════════════════════════════════════════ */}
      {successMessage && lastAdmitted && (
        <div className="mb-6 relative rounded-2xl p-0.5 bg-gradient-to-r from-emerald-400 via-emerald-300 to-slate-200 shadow-sm animate-in fade-in duration-300">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              </div>
              <div>
                <div className="text-xs font-mono font-bold text-emerald-800 uppercase tracking-wider">
                  PATIENT ADMITTED TO HOSPITAL LEDGER
                </div>
                <p className="text-xs text-slate-700 mt-0.5 font-sans leading-relaxed">{successMessage}</p>
                <div className="flex flex-wrap items-center gap-2.5 mt-2 text-[10px] font-mono text-emerald-700">
                  <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200">
                    MRN: <strong className="text-slate-900">{lastAdmitted.mrn}</strong>
                  </span>
                  <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200">
                    ACUITY: <strong className="text-slate-900">{lastAdmitted.triage_acuity}</strong>
                  </span>
                  <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200">
                    BED: <strong className="text-slate-900">{lastAdmitted.bed_number}</strong>
                  </span>
                </div>
              </div>
            </div>

            {onAdmitAndSimulate && (
              <button
                onClick={handleQuickEncounter}
                className="group relative px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold rounded-xl shadow-sm transition-all flex items-center gap-2 shrink-0 cursor-pointer active:scale-[0.98]"
              >
                <span>DISPATCH TO PATHWAY</span>
                <div className="w-5 h-5 rounded-md bg-white/20 flex items-center justify-center group-hover:translate-x-0.5 transition-transform">
                  <ArrowRight className="w-3.5 h-3.5 text-white" />
                </div>
              </button>
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          MAIN INTAKE FORM (DOUBLE-BEZEL CONCENTRIC LIGHT CARDS)
          ═══════════════════════════════════════════════════════════════════ */}
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Section 1: Demographics & Emergency Severity Index (ESI) */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-sky-200 via-slate-200 to-slate-200 shadow-sm border border-slate-200">
          <div className="p-5 rounded-[calc(1rem-2px)] bg-white">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-xs font-mono font-bold text-sky-800 uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-sky-600" />
                1. PATIENT DEMOGRAPHICS &amp; BED ALLOCATION
              </h3>
              <span className="font-mono text-[10px] text-slate-500">MANDATORY CLINICAL ADMISSION FIELDS</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-[11px] font-mono text-slate-600 mb-1.5">PATIENT FULL NAME *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Jane Smith"
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-xl px-3.5 py-2.5 font-medium focus:bg-white focus:ring-1 focus:ring-sky-500 focus:border-sky-500 focus:outline-none transition shadow-2xs"
                  required
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-600 mb-1.5">AGE *</label>
                <input
                  type="number"
                  value={age}
                  onChange={(e) => setAge(e.target.value === '' ? '' : Number(e.target.value))}
                  min={1}
                  max={120}
                  placeholder="Age in years"
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-xl px-3.5 py-2.5 font-mono focus:bg-white focus:ring-1 focus:ring-sky-500 focus:border-sky-500 focus:outline-none transition tabular-nums shadow-2xs"
                  required
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-600 mb-1.5">BIOLOGICAL SEX</label>
                <select
                  value={sex}
                  onChange={(e) => setSex(e.target.value as any)}
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-xl px-3.5 py-2.5 focus:bg-white focus:ring-1 focus:ring-sky-500 focus:border-sky-500 focus:outline-none font-mono transition shadow-2xs cursor-pointer"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-600 mb-1.5">ASSIGNED DEPARTMENT</label>
                <select
                  value={assignedDepartment}
                  onChange={(e) => setAssignedDepartment(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-xl px-3.5 py-2.5 focus:bg-white focus:ring-1 focus:ring-sky-500 focus:border-sky-500 focus:outline-none font-mono transition shadow-2xs cursor-pointer"
                >
                  <option value="EMERGENCY">Emergency Department</option>
                  <option value="CARDIOLOGY">Cardiology / CCU</option>
                  <option value="ICU">Medical ICU (MICU)</option>
                  <option value="INTERNAL_MEDICINE">Internal Medicine</option>
                  <option value="STEP_DOWN">Inpatient Step-Down Wing</option>
                </select>
              </div>
            </div>

            {/* Triage Acuity (ESI 1 to 5 Selectable Cards) */}
            <div className="mt-5 pt-4 border-t border-slate-100">
              <label className="block text-[11px] font-mono text-slate-600 mb-2.5">
                EMERGENCY SEVERITY INDEX (ESI) TRIAGE RATING
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {[
                  { id: 'RESUSCITATION', label: 'ESI 1', title: 'Resuscitation', color: 'rose', desc: 'Immediate life threat' },
                  { id: 'EMERGENT', label: 'ESI 2', title: 'Emergent', color: 'amber', desc: 'High-risk / Severe vitals' },
                  { id: 'URGENT', label: 'ESI 3', title: 'Urgent', color: 'yellow', desc: 'Multiple resources needed' },
                  { id: 'LESS_URGENT', label: 'ESI 4', title: 'Less Urgent', color: 'sky', desc: 'One resource needed' },
                  { id: 'NON_URGENT', label: 'ESI 5', title: 'Non-Urgent', color: 'emerald', desc: 'Clinical evaluation only' },
                ].map((lvl) => {
                  const isSelected = triageAcuity === lvl.id;
                  return (
                    <div
                      key={lvl.id}
                      onClick={() => setTriageAcuity(lvl.id)}
                      className={`relative rounded-xl p-0.5 cursor-pointer transition-all duration-200 text-left ${
                        isSelected
                          ? lvl.color === 'rose'
                            ? 'bg-rose-500 shadow-xs'
                            : lvl.color === 'amber'
                            ? 'bg-amber-500 shadow-xs'
                            : lvl.color === 'yellow'
                            ? 'bg-yellow-500 shadow-xs'
                            : lvl.color === 'sky'
                            ? 'bg-sky-500 shadow-xs'
                            : 'bg-emerald-500 shadow-xs'
                          : 'bg-slate-200 hover:bg-slate-300'
                      }`}
                    >
                      <div
                        className={`p-3 rounded-[calc(0.75rem-1px)] transition-all ${
                          isSelected
                            ? 'bg-white text-slate-900 border-2 border-transparent'
                            : 'bg-slate-50 hover:bg-white text-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`text-[10px] font-mono font-bold ${
                            isSelected
                              ? lvl.color === 'rose' ? 'text-rose-700'
                                : lvl.color === 'amber' ? 'text-amber-700'
                                : lvl.color === 'yellow' ? 'text-yellow-700'
                                : lvl.color === 'sky' ? 'text-sky-700'
                                : 'text-emerald-700'
                              : 'text-slate-500'
                          }`}>
                            {lvl.label}
                          </span>
                          {isSelected && <span className="w-2 h-2 rounded-full bg-sky-600 animate-pulse" />}
                        </div>
                        <div className="text-xs font-semibold text-slate-900 mt-1 font-sans">{lvl.title}</div>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">{lvl.desc}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Clinical Presentation & Medical History */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-amber-200 via-slate-200 to-slate-200 shadow-sm border border-slate-200">
          <div className="p-5 rounded-[calc(1rem-2px)] bg-white">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-xs font-mono font-bold text-amber-800 uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-600" />
                2. CLINICAL PRESENTATION &amp; MEDICAL HISTORY
              </h3>
              <span className="font-mono text-[10px] text-slate-500">DIAGNOSTIC EVIDENCE PROFILE</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-[11px] font-mono text-slate-600 mb-1.5">
                  CHIEF COMPLAINT (PRESENTING PROBLEM) *
                </label>
                <input
                  type="text"
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  placeholder="e.g., Acute substernal crushing chest pressure radiating to jaw and left arm"
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-xl px-3.5 py-2.5 font-medium focus:bg-white focus:ring-1 focus:ring-amber-500 focus:border-amber-500 focus:outline-none transition shadow-2xs"
                  required
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-[11px] font-mono text-slate-600 mb-1.5">
                  HISTORY OF PRESENT ILLNESS (HPI)
                </label>
                <textarea
                  value={hpi}
                  onChange={(e) => setHpi(e.target.value)}
                  placeholder="Onset, character, severity, radiation, aggravating or alleviating factors, associated symptoms..."
                  rows={2}
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-xl px-3.5 py-2.5 focus:bg-white focus:ring-1 focus:ring-amber-500 focus:border-amber-500 focus:outline-none resize-none leading-relaxed transition font-sans shadow-2xs"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-600 mb-1.5">
                  PAST MEDICAL HISTORY (COMMA-SEPARATED)
                </label>
                <input
                  type="text"
                  value={pastMedicalHistory}
                  onChange={(e) => setPastMedicalHistory(e.target.value)}
                  placeholder="e.g., Hypertension, Type 2 DM, Prior MI, Hyperlipidemia"
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-xl px-3.5 py-2.5 focus:bg-white focus:ring-1 focus:ring-amber-500 focus:border-amber-500 focus:outline-none transition shadow-2xs"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-600 mb-1.5">
                  ACTIVE OUTPATIENT MEDICATIONS
                </label>
                <input
                  type="text"
                  value={medications}
                  onChange={(e) => setMedications(e.target.value)}
                  placeholder="e.g., Metformin 1000mg BID, Atorvastatin 40mg QHS, Lisinopril 20mg"
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-xl px-3.5 py-2.5 focus:bg-white focus:ring-1 focus:ring-amber-500 focus:border-amber-500 focus:outline-none transition shadow-2xs"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-[11px] font-mono text-rose-700 mb-1.5 flex items-center gap-1.5 font-semibold">
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                  <span>DRUG ALLERGIES &amp; ADVERSE REACTIONS (CRITICAL CLINICAL SAFETY PROFILE)</span>
                </label>
                <input
                  type="text"
                  value={allergies}
                  onChange={(e) => setAllergies(e.target.value)}
                  placeholder="e.g., Penicillin (Anaphylaxis), Sulfa (Rash), or NKDA"
                  className="w-full bg-rose-50/60 border border-rose-300 text-rose-950 text-xs rounded-xl px-3.5 py-2.5 focus:bg-white focus:ring-1 focus:ring-rose-500 focus:border-rose-500 focus:outline-none font-medium transition shadow-2xs"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Baseline Intake Vitals (Lead II Synchronized Hardware Tiles) */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-emerald-200 via-slate-200 to-slate-200 shadow-sm border border-slate-200">
          <div className="p-5 rounded-[calc(1rem-2px)] bg-white">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-xs font-mono font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-600" />
                3. BASELINE TRIAGE VITALS (TELEMETRY SEED)
              </h3>
              <span className="font-mono text-[10px] text-emerald-700 font-semibold">LEAD II SYNCHRONIZED</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              {/* HR */}
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 focus-within:border-emerald-500 focus-within:bg-white transition shadow-2xs">
                <label className="block text-[10px] font-mono text-slate-500 mb-1 flex items-center gap-1">
                  <HeartPulse className="w-3 h-3 text-emerald-600" />
                  HEART RATE
                </label>
                <div className="flex items-baseline gap-1">
                  <input
                    type="number"
                    value={heartRate}
                    onChange={(e) => setHeartRate(Number(e.target.value))}
                    className="w-full bg-transparent text-emerald-700 text-base font-bold font-mono focus:outline-none tabular-nums"
                  />
                  <span className="text-[10px] font-mono text-slate-400">BPM</span>
                </div>
              </div>

              {/* Sys BP */}
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 focus-within:border-sky-500 focus-within:bg-white transition shadow-2xs">
                <label className="block text-[10px] font-mono text-slate-500 mb-1 flex items-center gap-1">
                  <Activity className="w-3 h-3 text-sky-600" />
                  SYSTOLIC BP
                </label>
                <div className="flex items-baseline gap-1">
                  <input
                    type="number"
                    value={systolicBp}
                    onChange={(e) => setSystolicBp(Number(e.target.value))}
                    className="w-full bg-transparent text-slate-800 text-base font-bold font-mono focus:outline-none tabular-nums"
                  />
                  <span className="text-[10px] font-mono text-slate-400">mmHg</span>
                </div>
              </div>

              {/* Dia BP */}
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 focus-within:border-sky-500 focus-within:bg-white transition shadow-2xs">
                <label className="block text-[10px] font-mono text-slate-500 mb-1 flex items-center gap-1">
                  <Activity className="w-3 h-3 text-sky-600" />
                  DIASTOLIC BP
                </label>
                <div className="flex items-baseline gap-1">
                  <input
                    type="number"
                    value={diastolicBp}
                    onChange={(e) => setDiastolicBp(Number(e.target.value))}
                    className="w-full bg-transparent text-slate-800 text-base font-bold font-mono focus:outline-none tabular-nums"
                  />
                  <span className="text-[10px] font-mono text-slate-400">mmHg</span>
                </div>
              </div>

              {/* RR */}
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 focus-within:border-slate-400 focus-within:bg-white transition shadow-2xs">
                <label className="block text-[10px] font-mono text-slate-500 mb-1 flex items-center gap-1">
                  <Layers className="w-3 h-3 text-slate-500" />
                  RESP RATE
                </label>
                <div className="flex items-baseline gap-1">
                  <input
                    type="number"
                    value={respiratoryRate}
                    onChange={(e) => setRespiratoryRate(Number(e.target.value))}
                    className="w-full bg-transparent text-slate-800 text-base font-bold font-mono focus:outline-none tabular-nums"
                  />
                  <span className="text-[10px] font-mono text-slate-400">bpm</span>
                </div>
              </div>

              {/* SpO2 */}
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 focus-within:border-sky-400 focus-within:bg-white transition shadow-2xs">
                <label className="block text-[10px] font-mono text-slate-500 mb-1 flex items-center gap-1">
                  <Thermometer className="w-3 h-3 text-sky-600" />
                  SPO2 %
                </label>
                <div className="flex items-baseline gap-1">
                  <input
                    type="number"
                    step="0.1"
                    value={spo2}
                    onChange={(e) => setSpo2(Number(e.target.value))}
                    className="w-full bg-transparent text-sky-700 text-base font-bold font-mono focus:outline-none tabular-nums"
                  />
                  <span className="text-[10px] font-mono text-slate-400">%</span>
                </div>
              </div>

              {/* Temp */}
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 focus-within:border-slate-400 focus-within:bg-white transition shadow-2xs">
                <label className="block text-[10px] font-mono text-slate-500 mb-1 flex items-center gap-1">
                  <Thermometer className="w-3 h-3 text-slate-500" />
                  TEMP CORE
                </label>
                <div className="flex items-baseline gap-1">
                  <input
                    type="number"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(Number(e.target.value))}
                    className="w-full bg-transparent text-slate-800 text-base font-bold font-mono focus:outline-none tabular-nums"
                  />
                  <span className="text-[10px] font-mono text-slate-400">°C</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            SUBMIT ACTION CONTROLS
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-3">
          <button
            type="button"
            onClick={handleResetForm}
            className="w-full sm:w-auto px-4 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-mono rounded-xl border border-slate-300 flex items-center justify-center gap-2 transition cursor-pointer shadow-xs"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>RESET FIELDS</span>
          </button>

          <button
            type="submit"
            disabled={isSubmitting}
            className="group relative w-full sm:w-auto px-6 py-3 bg-sky-600 hover:bg-sky-500 text-white font-mono font-bold text-xs rounded-xl transition-all flex items-center justify-between sm:justify-center gap-3 cursor-pointer shadow-sm active:scale-[0.98] disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>ADMITTING TO HOSPITAL RECORD SYSTEM...</span>
              </>
            ) : (
              <>
                <span>ADMIT PATIENT TO RECORD SYSTEM</span>
                <div className="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <FileSpreadsheet className="w-3.5 h-3.5 text-white" />
                </div>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CaseIntakeAdmissionSection;
