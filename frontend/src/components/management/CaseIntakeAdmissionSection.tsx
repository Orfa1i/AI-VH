import React, { useState } from 'react';
import type { BenchmarkCase, PatientRecord } from '../../types';

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
  const [age, setAge] = useState<number>(55);
  const [sex, setSex] = useState<'Male' | 'Female' | 'Other'>('Male');
  const [triageAcuity, setTriageAcuity] = useState<string>('URGENT');
  const [assignedDepartment, setAssignedDepartment] = useState<string>('EMERGENCY');
  const [bedNumber, setBedNumber] = useState<string>('ED-BAY-03');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [hpi, setHpi] = useState('');
  const [pastMedicalHistory, setPastMedicalHistory] = useState('');
  const [medications, setMedications] = useState('');
  const [allergies, setAllergies] = useState('');

  // Vitals
  const [heartRate, setHeartRate] = useState<number>(98);
  const [systolicBp, setSystolicBp] = useState<number>(134);
  const [diastolicBp, setDiastolicBp] = useState<number>(84);
  const [respiratoryRate, setRespiratoryRate] = useState<number>(18);
  const [spo2, setSpo2] = useState<number>(97.0);
  const [temperature, setTemperature] = useState<number>(37.2);

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [lastAdmitted, setLastAdmitted] = useState<PatientRecord | null>(null);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('');

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
    } else if (caseId === 'CASE-103') {
      setName('Arthur Pendelton');
      setAge(68);
      setSex('Male');
      setTriageAcuity('URGENT');
      setAssignedDepartment('INTERNAL_MEDICINE');
      setBedNumber('MED-103');
      setChiefComplaint('Oliguria, peripheral pitting edema, and generalized fatigue');
      setHpi('Noticed darkening urine and decreased volume over past 5 days following intense NSAID use for back pain.');
      setPastMedicalHistory('Benign Prostatic Hyperplasia, Mild Osteoarthritis');
      setMedications('Ibuprofen 800mg TID, Tamsulosin 0.4mg daily');
      setAllergies('Codeine (Severe Nausea)');
      setHeartRate(82);
      setSystolicBp(156);
      setDiastolicBp(94);
      setRespiratoryRate(16);
      setSpo2(96.0);
      setTemperature(36.8);
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
      setSuccessMessage(`Successfully admitted ${admitted.name} (MRN: ${admitted.mrn}) to ${admitted.assigned_department} [Bed: ${admitted.bed_number}].`);
      onPatientAdmitted(admitted);
    } catch (err: any) {
      console.error('Error admitting patient:', err);
      alert(`Admission Failed: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickEncounter = () => {
    if (selectedPresetId && onAdmitAndSimulate) {
      onAdmitAndSimulate(selectedPresetId);
    }
  };

  return (
    <div className="flex-1 p-6 bg-slate-900/60 overflow-y-auto max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-slate-100">Clinical Case Intake & Admission Portal</span>
            <span className="px-2.5 py-0.5 text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full">
              Live Intake Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Convert incoming clinical cases and triage presentations into persistent hospital patient records with MRNs, bed assignments, and automated EHR baselines.
          </p>
        </div>

        {/* Preset Selector */}
        <div className="flex items-center gap-2 bg-slate-800/80 p-2 rounded-lg border border-slate-700">
          <span className="text-xs text-slate-400 font-medium whitespace-nowrap">Load Preset:</span>
          <select
            value={selectedPresetId}
            onChange={(e) => handleSelectPreset(e.target.value)}
            className="bg-slate-900 text-cyan-300 text-xs rounded px-2.5 py-1.5 border border-slate-700 focus:outline-none focus:border-cyan-500"
          >
            <option value="">-- Choose Benchmark Case --</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id}: {c.name} ({c.acuity})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Success Notification Alert */}
      {successMessage && lastAdmitted && (
        <div className="mb-6 p-4 bg-emerald-950/70 border border-emerald-700/60 rounded-xl flex items-start justify-between gap-4 animate-in fade-in duration-300">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-base flex-shrink-0">
              ✓
            </div>
            <div>
              <h4 className="text-sm font-semibold text-emerald-200">Patient Admitted Successfully</h4>
              <p className="text-xs text-emerald-300/80 mt-0.5">{successMessage}</p>
              <div className="flex items-center gap-4 mt-2 text-[11px] font-mono text-emerald-400/90">
                <span>PATIENT ID: {lastAdmitted.id}</span>
                <span>MRN: {lastAdmitted.mrn}</span>
                <span>ACUITY: {lastAdmitted.triage_acuity}</span>
                <span>BED: {lastAdmitted.bed_number}</span>
              </div>
            </div>
          </div>
          {onAdmitAndSimulate && selectedPresetId && (
            <button
              onClick={handleQuickEncounter}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded shadow transition whitespace-nowrap"
            >
              Start Clinical Encounter →
            </button>
          )}
        </div>
      )}

      {/* Main Intake Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Demographics & Bed Allocation */}
        <div className="bg-slate-800/50 border border-slate-800 rounded-xl p-5 shadow-sm">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            1. Patient Demographics & Hospital Allocation
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1 font-medium">Patient Full Name *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Samuel Jenkins"
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1 font-medium">Age</label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                min={1}
                max={120}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1 font-medium">Biological Sex</label>
              <select
                value={sex}
                onChange={(e) => setSex(e.target.value as any)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1 font-medium">Triage Acuity (ESI)</label>
              <select
                value={triageAcuity}
                onChange={(e) => setTriageAcuity(e.target.value)}
                className={`w-full bg-slate-900 border text-xs rounded-lg px-3 py-2 font-semibold focus:outline-none ${
                  triageAcuity === 'RESUSCITATION'
                    ? 'text-rose-400 border-rose-800'
                    : triageAcuity === 'EMERGENT'
                    ? 'text-amber-400 border-amber-800'
                    : 'text-cyan-400 border-cyan-800'
                }`}
              >
                <option value="RESUSCITATION">Level 1 - RESUSCITATION (Immediate)</option>
                <option value="EMERGENT">Level 2 - EMERGENT (Critical)</option>
                <option value="URGENT">Level 3 - URGENT (Acute)</option>
                <option value="LESS_URGENT">Level 4 - LESS URGENT</option>
                <option value="NON_URGENT">Level 5 - NON URGENT</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1 font-medium">Assigned Department</label>
              <select
                value={assignedDepartment}
                onChange={(e) => setAssignedDepartment(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
              >
                <option value="EMERGENCY">Emergency Department</option>
                <option value="INTERNAL_MEDICINE">Internal Medicine</option>
                <option value="CARDIOLOGY">Cardiology / CCU</option>
                <option value="ICU">Medical Intensive Care (MICU)</option>
                <option value="STEP_DOWN">Inpatient Step-Down Wing</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1 font-medium">Assigned Bed Number</label>
              <input
                type="text"
                value={bedNumber}
                onChange={(e) => setBedNumber(e.target.value)}
                placeholder="e.g., CCU-02 or ED-BAY-03"
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Clinical Presentation & History */}
        <div className="bg-slate-800/50 border border-slate-800 rounded-xl p-5 shadow-sm">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            2. Chief Complaint & Clinical History
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1 font-medium">Chief Complaint (Presenting Problem) *</label>
              <input
                type="text"
                value={chiefComplaint}
                onChange={(e) => setChiefComplaint(e.target.value)}
                placeholder="e.g., Acute substernal crushing chest pain with radiation to jaw"
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-amber-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1 font-medium">History of Present Illness (HPI)</label>
              <textarea
                value={hpi}
                onChange={(e) => setHpi(e.target.value)}
                placeholder="Onset, quality, severity, radiation, aggravating/alleviating factors..."
                rows={2}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-amber-500 focus:outline-none resize-none"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1 font-medium">Past Medical History (Comma-separated)</label>
              <input
                type="text"
                value={pastMedicalHistory}
                onChange={(e) => setPastMedicalHistory(e.target.value)}
                placeholder="Hypertension, Type 2 DM, Prior MI, Hyperlipidemia"
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-amber-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1 font-medium">Active Outpatient Medications (Comma-separated)</label>
              <input
                type="text"
                value={medications}
                onChange={(e) => setMedications(e.target.value)}
                placeholder="Metformin 1000mg BID, Atorvastatin 40mg QHS, Lisinopril 20mg"
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-amber-500 focus:outline-none"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs text-rose-400 mb-1 font-medium flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                Drug Allergies & Adverse Reactions (Crucial for Pharmacist Reconciliation)
              </label>
              <input
                type="text"
                value={allergies}
                onChange={(e) => setAllergies(e.target.value)}
                placeholder="e.g., Penicillin (Anaphylaxis), Sulfa (Rash), or NKDA"
                className="w-full bg-slate-900 border border-rose-900/50 text-rose-200 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-rose-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Section 3: Baseline Intake Vitals */}
        <div className="bg-slate-800/50 border border-slate-800 rounded-xl p-5 shadow-sm">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            3. Baseline Triage Vitals
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Heart Rate (bpm)</label>
              <input
                type="number"
                value={heartRate}
                onChange={(e) => setHeartRate(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Systolic BP (mmHg)</label>
              <input
                type="number"
                value={systolicBp}
                onChange={(e) => setSystolicBp(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Diastolic BP (mmHg)</label>
              <input
                type="number"
                value={diastolicBp}
                onChange={(e) => setDiastolicBp(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Resp Rate (/min)</label>
              <input
                type="number"
                value={respiratoryRate}
                onChange={(e) => setRespiratoryRate(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">SpO2 (%)</label>
              <input
                type="number"
                step="0.1"
                value={spo2}
                onChange={(e) => setSpo2(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Temp (°C)</label>
              <input
                type="number"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Submit Actions */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => {
              setName('');
              setChiefComplaint('');
              setHpi('');
              setPastMedicalHistory('');
              setMedications('');
              setAllergies('');
              setSelectedPresetId('');
            }}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-medium rounded-lg transition"
          >
            Clear Form
          </button>

          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs rounded-lg shadow-md hover:shadow-cyan-500/25 transition disabled:opacity-50 flex items-center gap-2"
          >
            {isSubmitting ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Admitting Patient to Database...</span>
              </>
            ) : (
              <>
                <span>✓ Admit Patient to Hospital</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CaseIntakeAdmissionSection;
