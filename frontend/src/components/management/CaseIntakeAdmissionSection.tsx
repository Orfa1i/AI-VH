import React, { useState } from 'react';
import type { BenchmarkCase, PatientRecord } from '../../types';
import {
  UserPlus,
  CheckCircle2,
  Sparkles,
  RotateCcw,
  ArrowRight,
  ShieldAlert
} from 'lucide-react';

interface CaseIntakeAdmissionSectionProps {
  cases: BenchmarkCase[];
  onPatientAdmitted: (patient: PatientRecord) => void;
  onAdmitAndSimulate?: (caseId: string) => void;
}

export const CaseIntakeAdmissionSection: React.FC<CaseIntakeAdmissionSectionProps> = ({
  cases,
  onPatientAdmitted,
  onAdmitAndSimulate,
}) => {
  // Form fields
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
  const [selectedPresetId, setSelectedPresetId] = useState<string>('');

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
    setSelectedPresetId('');
    setSuccessMessage(null);
  };

  // Pre-fill form from selected clinical preset
  const handleSelectPreset = (caseId: string) => {
    setSelectedPresetId(caseId);
    if (!caseId) return;

    if (caseId === 'CASE-101') {
      setName('Robert Miller');
      setAge(62);
      setSex('Male');
      setTriageAcuity('RESUSCITATION');
      setAssignedDepartment('CARDIOLOGY');
      setBedNumber('CCU-01');
      setChiefComplaint('Substernal crushing chest pressure radiating to left arm');
      setHpi('Acute onset 2 hours ago while climbing stairs. Associated with nausea, diaphoresis, and lightheadedness.');
      setPastMedicalHistory('Essential Hypertension, Hyperlipidemia, 30 pack-year smoking history');
      setMedications('Aspirin 81mg daily, Atorvastatin 40mg daily, Amlodipine 5mg daily');
      setAllergies('Penicillin (Anaphylaxis/Hives)');
      setHeartRate(102);
      setSystolicBp(148);
      setDiastolicBp(92);
      setRespiratoryRate(22);
      setSpo2(95.0);
      setTemperature(36.9);
    } else if (caseId === 'CASE-102') {
      setName('Elena Rostova');
      setAge(24);
      setSex('Female');
      setTriageAcuity('EMERGENT');
      setAssignedDepartment('ICU');
      setBedNumber('ICU-BED-02');
      setChiefComplaint('Nausea, vomiting, progressive lethargy, and deep rapid Kussmaul breathing');
      setHpi('Felt unwell for 3 days with polyuria, polydipsia, and anorexia following viral gastroenteritis.');
      setPastMedicalHistory('Type 1 Diabetes Mellitus (diagnosed age 12)');
      setMedications('Insulin glargine 22 units QHS, Insulin lispro 6 units with meals');
      setAllergies('NKDA (No Known Drug Allergies)');
      setHeartRate(118);
      setSystolicBp(98);
      setDiastolicBp(62);
      setRespiratoryRate(28);
      setSpo2(98.0);
      setTemperature(37.4);
    } else if (caseId === 'CASE-104') {
      setName('Clara Vance');
      setAge(52);
      setSex('Female');
      setTriageAcuity('EMERGENT');
      setAssignedDepartment('STEP_DOWN');
      setBedNumber('STEP-104');
      setChiefComplaint('Sudden onset pleuritic chest pain and dyspnea');
      setHpi('Pain began abruptly 4 hours ago. Recently returned from a 14-hour transcontinental flight.');
      setPastMedicalHistory('Mild Asthma, Mild Varicose Veins');
      setMedications('Oral contraceptive pill, Albuterol inhaler PRN');
      setAllergies('Latex (Contact Dermatitis)');
      setHeartRate(112);
      setSystolicBp(124);
      setDiastolicBp(78);
      setRespiratoryRate(24);
      setSpo2(92.0);
      setTemperature(37.1);
    }
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
      age: Number(age),
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
      case_id: selectedPresetId || undefined,
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

      const admitted: PatientRecord = await res.json();
      setLastAdmitted(admitted);
      setSuccessMessage(`Admitted ${admitted.name} (MRN: ${admitted.mrn}) to ${admitted.assigned_department} [Bed: ${admitted.bed_number}].`);
      onPatientAdmitted(admitted);
    } catch (err: any) {
      console.error('Error admitting patient:', err);
      alert(`Admission Failed: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickEncounter = () => {
    if (lastAdmitted && onAdmitAndSimulate) {
      onAdmitAndSimulate(lastAdmitted.id);
    }
  };

  return (
    <div className="flex-1 p-4 md:p-6 bg-slate-950 overflow-y-auto max-w-7xl mx-auto w-full telemetry-grid">
      {/* ═══════════════════════════════════════════════════════════════════
          TOP HEADER & ADMISSION BADGE
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <UserPlus className="w-4 h-4" />
            </div>
            <h2 className="text-base font-bold text-slate-100 tracking-wide font-headline-sm uppercase">
              Clinical Case Intake &amp; Admission Portal
            </h2>
            <span className="px-2 py-0.5 text-[10px] font-mono font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800 rounded">
              EHR INTAKE ENGINE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Generate authenticated patient records with unique MRNs, ESI acuity classifications, bed allocations, and baseline vitals.
          </p>
        </div>

        {/* Clinical Scenario Preset Quick-Loader */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1.5 rounded">
          <span className="text-[11px] font-mono text-slate-400 px-2 flex items-center gap-1.5">
            <Sparkles className="w-3 h-3 text-sky-400" />
            <span>QUICK PRESET:</span>
          </span>
          <select
            value={selectedPresetId}
            onChange={(e) => handleSelectPreset(e.target.value)}
            className="bg-slate-950 text-sky-400 text-xs rounded px-2.5 py-1.5 border border-slate-700/80 font-mono focus:outline-none focus:border-sky-500"
          >
            <option value="">-- Manual Case Entry --</option>
            {cases.length > 0 ? (
              cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id}: {c.name} ({c.acuity})
                </option>
              ))
            ) : (
              <>
                <option value="CASE-101">CASE-101: Robert Miller (NSTEMI / CCU)</option>
                <option value="CASE-102">CASE-102: Elena Rostova (DKA / ICU)</option>
                <option value="CASE-104">CASE-104: Clara Vance (Submassive PE)</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          SUCCESS NOTIFICATION CARD
          ═══════════════════════════════════════════════════════════════════ */}
      {successMessage && lastAdmitted && (
        <div className="mb-6 p-4 bg-emerald-950/60 border border-emerald-700/80 rounded hud-bracket flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-in fade-in duration-200">
          <div className="flex items-start gap-3">
            <div className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-mono font-bold text-emerald-300 uppercase tracking-wider">
                PATIENT ADMITTED SUCCESSFULLY
              </div>
              <p className="text-xs text-slate-300 mt-0.5">{successMessage}</p>
              <div className="flex flex-wrap items-center gap-3 mt-1.5 text-[10px] font-mono text-emerald-400">
                <span>MRN: <strong className="text-slate-100">{lastAdmitted.mrn}</strong></span>
                <span>•</span>
                <span>ACUITY: <strong className="text-slate-100">{lastAdmitted.triage_acuity}</strong></span>
                <span>•</span>
                <span>BED: <strong className="text-slate-100">{lastAdmitted.bed_number}</strong></span>
              </div>
            </div>
          </div>

          {onAdmitAndSimulate && (
            <button
              onClick={handleQuickEncounter}
              className="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-mono font-bold rounded shadow transition flex items-center gap-1.5 shrink-0 cursor-pointer"
            >
              <span>DISPATCH TO PATHWAY</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          MAIN INTAKE FORM
          ═══════════════════════════════════════════════════════════════════ */}
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Section 1: Demographics & Emergency Severity Index (ESI) */}
        <div className="bg-slate-900/80 border border-slate-800 rounded hud-bracket p-4 shadow-sm backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3.5">
            <h3 className="text-xs font-mono font-bold text-sky-400 uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-sky-400" />
              1. PATIENT DEMOGRAPHICS &amp; BED ALLOCATION
            </h3>
            <span className="font-mono text-[10px] text-slate-500">MANDATORY FIELDS (*)</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5">
            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">PATIENT FULL NAME *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Samuel Jenkins"
                className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded px-3 py-2 font-medium focus:ring-1 focus:ring-sky-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">AGE *</label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                min={1}
                max={120}
                className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded px-3 py-2 font-mono focus:ring-1 focus:ring-sky-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">BIOLOGICAL SEX</label>
              <select
                value={sex}
                onChange={(e) => setSex(e.target.value as any)}
                className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded px-3 py-2 focus:ring-1 focus:ring-sky-500 focus:outline-none font-mono"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">ASSIGNED DEPARTMENT</label>
              <select
                value={assignedDepartment}
                onChange={(e) => setAssignedDepartment(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded px-3 py-2 focus:ring-1 focus:ring-sky-500 focus:outline-none font-mono"
              >
                <option value="EMERGENCY">Emergency Department</option>
                <option value="CARDIOLOGY">Cardiology / CCU</option>
                <option value="ICU">Medical ICU (MICU)</option>
                <option value="INTERNAL_MEDICINE">Internal Medicine</option>
                <option value="STEP_DOWN">Inpatient Step-Down Wing</option>
              </select>
            </div>
          </div>

          {/* Triage Acuity (ESI 1-5 Selectable Cards) */}
          <div className="mt-4 pt-3.5 border-t border-slate-800">
            <label className="block text-[11px] font-mono text-slate-400 mb-2">
              EMERGENCY SEVERITY INDEX (ESI) TRIAGE RATING
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
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
                    className={`p-2 rounded border cursor-pointer transition text-left ${
                      isSelected
                        ? lvl.color === 'rose'
                          ? 'bg-rose-950/60 border-rose-500 shadow-sm shadow-rose-500/20'
                          : lvl.color === 'amber'
                          ? 'bg-amber-950/60 border-amber-500 shadow-sm shadow-amber-500/20'
                          : lvl.color === 'yellow'
                          ? 'bg-yellow-950/60 border-yellow-500 shadow-sm shadow-yellow-500/20'
                          : lvl.color === 'sky'
                          ? 'bg-sky-950/60 border-sky-500 shadow-sm shadow-sky-500/20'
                          : 'bg-emerald-950/60 border-emerald-500 shadow-sm shadow-emerald-500/20'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-[10px] font-mono font-bold ${
                        isSelected ? 'text-white' : 'text-slate-400'
                      }`}>
                        {lvl.label}
                      </span>
                      {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />}
                    </div>
                    <div className="text-xs font-semibold text-slate-100 mt-0.5">{lvl.title}</div>
                    <div className="text-[9px] text-slate-400 font-mono mt-0.5 truncate">{lvl.desc}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Section 2: Clinical Presentation & History */}
        <div className="bg-slate-900/80 border border-slate-800 rounded hud-bracket p-4 shadow-sm backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3.5">
            <h3 className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              2. CLINICAL PRESENTATION &amp; MEDICAL HISTORY
            </h3>
            <span className="font-mono text-[10px] text-slate-500">DIAGNOSTIC EVIDENCE</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            <div className="md:col-span-2">
              <label className="block text-[11px] font-mono text-slate-400 mb-1">
                CHIEF COMPLAINT (PRESENTING PROBLEM) *
              </label>
              <input
                type="text"
                value={chiefComplaint}
                onChange={(e) => setChiefComplaint(e.target.value)}
                placeholder="e.g., Acute substernal crushing chest pressure radiating to jaw and left arm"
                className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded px-3 py-2 font-medium focus:ring-1 focus:ring-amber-500 focus:outline-none"
                required
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-[11px] font-mono text-slate-400 mb-1">
                HISTORY OF PRESENT ILLNESS (HPI)
              </label>
              <textarea
                value={hpi}
                onChange={(e) => setHpi(e.target.value)}
                placeholder="Onset, character, severity, radiation, aggravating/alleviating factors, associated symptoms..."
                rows={2}
                className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded px-3 py-2 focus:ring-1 focus:ring-amber-500 focus:outline-none resize-none leading-relaxed"
              />
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">
                PAST MEDICAL HISTORY (COMMA-SEPARATED)
              </label>
              <input
                type="text"
                value={pastMedicalHistory}
                onChange={(e) => setPastMedicalHistory(e.target.value)}
                placeholder="Hypertension, Type 2 DM, Prior MI, Hyperlipidemia"
                className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded px-3 py-2 focus:ring-1 focus:ring-amber-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 mb-1">
                ACTIVE OUTPATIENT MEDICATIONS
              </label>
              <input
                type="text"
                value={medications}
                onChange={(e) => setMedications(e.target.value)}
                placeholder="Metformin 1000mg BID, Atorvastatin 40mg QHS, Lisinopril 20mg"
                className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded px-3 py-2 focus:ring-1 focus:ring-amber-500 focus:outline-none"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-[11px] font-mono text-rose-400 mb-1 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>DRUG ALLERGIES &amp; ADVERSE REACTIONS (CRITICAL CLINICAL SAFETY PROFILE)</span>
              </label>
              <input
                type="text"
                value={allergies}
                onChange={(e) => setAllergies(e.target.value)}
                placeholder="e.g., Penicillin (Anaphylaxis), Sulfa (Rash), or NKDA"
                className="w-full bg-slate-950 border border-rose-900/60 text-rose-200 text-xs rounded px-3 py-2 focus:ring-1 focus:ring-rose-500 focus:outline-none font-medium"
              />
            </div>
          </div>
        </div>

        {/* Section 3: Baseline Intake Vitals */}
        <div className="bg-slate-900/80 border border-slate-800 rounded hud-bracket p-4 shadow-sm backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3.5">
            <h3 className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              3. BASELINE TRIAGE VITALS (TELEMETRY SEED)
            </h3>
            <span className="font-mono text-[10px] text-emerald-400/90 font-semibold">LEAD II SYNCHRONIZED</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5">
            {/* HR */}
            <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
              <label className="block text-[10px] font-mono text-slate-400 mb-1">HEART RATE</label>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  value={heartRate}
                  onChange={(e) => setHeartRate(Number(e.target.value))}
                  className="w-full bg-transparent text-emerald-400 text-base font-bold font-mono focus:outline-none"
                />
                <span className="text-[10px] font-mono text-slate-500">BPM</span>
              </div>
            </div>

            {/* Sys BP */}
            <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
              <label className="block text-[10px] font-mono text-slate-400 mb-1">SYSTOLIC BP</label>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  value={systolicBp}
                  onChange={(e) => setSystolicBp(Number(e.target.value))}
                  className="w-full bg-transparent text-slate-200 text-base font-bold font-mono focus:outline-none"
                />
                <span className="text-[10px] font-mono text-slate-500">mmHg</span>
              </div>
            </div>

            {/* Dia BP */}
            <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
              <label className="block text-[10px] font-mono text-slate-400 mb-1">DIASTOLIC BP</label>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  value={diastolicBp}
                  onChange={(e) => setDiastolicBp(Number(e.target.value))}
                  className="w-full bg-transparent text-slate-200 text-base font-bold font-mono focus:outline-none"
                />
                <span className="text-[10px] font-mono text-slate-500">mmHg</span>
              </div>
            </div>

            {/* RR */}
            <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
              <label className="block text-[10px] font-mono text-slate-400 mb-1">RESP RATE</label>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  value={respiratoryRate}
                  onChange={(e) => setRespiratoryRate(Number(e.target.value))}
                  className="w-full bg-transparent text-slate-200 text-base font-bold font-mono focus:outline-none"
                />
                <span className="text-[10px] font-mono text-slate-500">bpm</span>
              </div>
            </div>

            {/* SpO2 */}
            <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
              <label className="block text-[10px] font-mono text-slate-400 mb-1">SPO2 %</label>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  step="0.1"
                  value={spo2}
                  onChange={(e) => setSpo2(Number(e.target.value))}
                  className="w-full bg-transparent text-sky-400 text-base font-bold font-mono focus:outline-none"
                />
                <span className="text-[10px] font-mono text-slate-500">%</span>
              </div>
            </div>

            {/* Temp */}
            <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
              <label className="block text-[10px] font-mono text-slate-400 mb-1">TEMP CORE</label>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className="w-full bg-transparent text-slate-200 text-base font-bold font-mono focus:outline-none"
                />
                <span className="text-[10px] font-mono text-slate-500">°C</span>
              </div>
            </div>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            SUBMIT ACTION CONTROLS
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={handleResetForm}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono rounded border border-slate-800 flex items-center gap-1.5 transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>RESET FIELDS</span>
          </button>

          <button
            type="submit"
            disabled={isSubmitting}
            className="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-mono font-bold text-xs rounded transition flex items-center gap-2 cursor-pointer shadow-sm active:scale-95 disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-slate-950/30 border-t-slate-950 rounded-full animate-spin" />
                <span>ADMITTING TO HOSPITAL EHR...</span>
              </>
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                <span>ADMIT PATIENT TO RECORD SYSTEM</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CaseIntakeAdmissionSection;
