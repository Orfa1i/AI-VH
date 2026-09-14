import React, { useState, useEffect } from 'react';
import type { MedicationSafetyReport, BenchmarkCase } from '../../types';
import {
  Pill,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  Send,
  Loader2,
  X,
  FileText,
  Activity,
  User,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { speakClinicalMessage, stopClinicalSpeech } from '../../utils/speechSynthesis';

interface PharmacistModalProps {
  isOpen: boolean;
  onClose: () => void;
  cases: BenchmarkCase[];
}


const PRESET_ORDERS = [
  {
    title: 'Standard ACS / NSTEMI Protocol',
    patientId: 'CASE-101',
    diagnosis: 'Acute Coronary Syndrome (NSTEMI)',
    prescriptions: [
      'Aspirin 325mg chewable STAT',
      'Ticagrelor 180mg loading dose, then 90mg BID',
      'Sublingual Nitroglycerin 0.4mg q5min PRN',
      'Atorvastatin 80mg oral daily',
      'Unfractionated Heparin continuous infusion',
    ],
  },
  {
    title: 'ACS with Inappropriate NSAID (Safety Test)',
    patientId: 'CASE-101',
    diagnosis: 'Acute Coronary Syndrome (NSTEMI)',
    prescriptions: [
      'Aspirin 325mg chewable STAT',
      'Ibuprofen 800mg PO TID for chest soreness',
      'Atorvastatin 80mg daily',
    ],
  },
  {
    title: 'Infection in Penicillin-Allergic Patient (Allergy Test)',
    patientId: 'CASE-101',
    diagnosis: 'Community-Acquired Pneumonia',
    prescriptions: [
      'Amoxicillin / Clavulanate 875mg PO BID',
      'Azithromycin 500mg IV STAT',
    ],
  },
  {
    title: 'Severe DKA Resuscitation Protocol',
    patientId: 'CASE-102',
    diagnosis: 'Diabetic Ketoacidosis (DKA) with Metabolic Acidosis',
    prescriptions: [
      '0.9% Normal Saline 1000 mL/hr IV bolus',
      'Regular Insulin continuous IV infusion 0.1 units/kg/hr',
      'Potassium Chloride 20 mEq/L IV fluid infusion',
    ],
  },
  {
    title: 'Renal Impairment with Nephrotoxic Order (Renal Risk)',
    patientId: 'CASE-102',
    diagnosis: 'Acute Renal Azotemia / Sepsis',
    prescriptions: [
      'Ketorolac 30mg IV STAT',
      'Enoxaparin 1 mg/kg Q12H subcutaneous',
      'Metformin 1000mg BID',
    ],
  },
];

export const PharmacistModal: React.FC<PharmacistModalProps> = ({
  isOpen,
  onClose,
  cases,
}) => {
  const [selectedPresetIndex, setSelectedPresetIndex] = useState<number>(0);
  const [patientId, setPatientId] = useState<string>(PRESET_ORDERS[0].patientId);
  const [diagnosis, setDiagnosis] = useState<string>(PRESET_ORDERS[0].diagnosis);
  const [prescriptionsText, setPrescriptionsText] = useState<string>(
    PRESET_ORDERS[0].prescriptions.join('\n')
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [report, setReport] = useState<MedicationSafetyReport | null>(null);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) {
      stopClinicalSpeech();
      setIsSpeaking(false);
    }
  }, [isOpen]);

  const handleToggleSpeech = () => {
    if (isSpeaking) {
      stopClinicalSpeech();
      setIsSpeaking(false);
    } else if (report) {
      const summaryText = `Clinical Pharmacist Doctor Elena Rostova. Dispensing review status is: ${
        report.safety_cleared ? 'cleared and approved' : 'hold for physician clarification'
      }. ${
        report.flagged_contraindications.length > 0
          ? 'Alert: ' + report.flagged_contraindications.join('. ')
          : 'All ordered medications cleared against patient profile.'
      }`;
      speakClinicalMessage(
        summaryText,
        'DR_ROSTOVA',
        () => setIsSpeaking(true),
        () => setIsSpeaking(false)
      );
    }
  };

  if (!isOpen) return null;


  const handleSelectPreset = (idx: number) => {
    setSelectedPresetIndex(idx);
    const p = PRESET_ORDERS[idx];
    setPatientId(p.patientId);
    setDiagnosis(p.diagnosis);
    setPrescriptionsText(p.prescriptions.join('\n'));
    setReport(null);
  };

  const handleRunReview = async () => {
    const rxList = prescriptionsText
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (rxList.length === 0) return;

    setIsLoading(true);
    try {
      const res = await fetch('/api/pharmacy/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prescriptions: rxList,
          patient_id: patientId,
          diagnosis: diagnosis,
        }),
      });
      if (!res.ok) throw new Error('Pharmacy review request failed');
      const data: MedicationSafetyReport = await res.json();
      setReport(data);
    } catch (err) {
      console.error('Error running pharmacy review:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-300 shadow-lg shadow-teal-500/10">
              <Pill className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100">
                  Clinical Pharmacy & Medication Safety
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30">
                  Phase 7 Scale
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Dr. Elena Rostova, PharmD, BCPS • Central Core Pharmacy Station
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Preset Buttons */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Clinical Medication Scenarios & Safety Benchmarks:
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              {PRESET_ORDERS.map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectPreset(idx)}
                  className={`p-2.5 rounded-xl text-left border text-xs font-medium transition-all ${
                    selectedPresetIndex === idx
                      ? 'bg-teal-950/60 border-teal-500/70 text-teal-200 shadow-md shadow-teal-900/30'
                      : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  <div className="font-semibold text-slate-200 mb-0.5 truncate">
                    {preset.title}
                  </div>
                  <div className="text-[11px] text-slate-400 truncate">
                    {preset.diagnosis}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Form Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-teal-400" />
                Select Inpatient Patient:
              </label>
              <select
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-teal-500"
              >
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.id}: {c.name} ({c.age}yo {c.sex}) - {c.chief_complaint.slice(0, 40)}...
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-teal-400" />
                Primary Diagnosis:
              </label>
              <input
                type="text"
                value={diagnosis}
                onChange={(e) => setDiagnosis(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-teal-500"
                placeholder="Clinical diagnosis..."
              />
            </div>
          </div>

          {/* Prescriptions Input Area */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-teal-400" />
              Medication Orders for Review (One per line):
            </label>
            <textarea
              rows={4}
              value={prescriptionsText}
              onChange={(e) => setPrescriptionsText(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-teal-500 font-mono leading-relaxed"
              placeholder="e.g. Aspirin 325mg PO STAT..."
            />
          </div>

          {/* Action Button */}
          <div className="flex justify-end">
            <button
              onClick={handleRunReview}
              disabled={isLoading || !prescriptionsText.trim()}
              className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white text-xs font-bold shadow-lg shadow-teal-600/20 border border-teal-400/40 flex items-center gap-2 cursor-pointer transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Pharmacist Reconciling Orders...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Review Orders with Dr. Rostova</span>
                </>
              )}
            </button>
          </div>

          {/* Report Display */}
          {report && (
            <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-4 animate-in fade-in duration-300">
              {/* Status Banner */}
              <div
                className={`p-4 rounded-xl border flex items-center justify-between ${
                  report.safety_cleared
                    ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-300'
                    : 'bg-rose-950/40 border-rose-500/50 text-rose-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  {report.safety_cleared ? (
                    <ShieldCheck className="w-6 h-6 text-emerald-400" />
                  ) : (
                    <ShieldAlert className="w-6 h-6 text-rose-400 animate-pulse" />
                  )}
                  <div>
                    <h3 className="font-bold text-sm">
                      {report.safety_cleared
                        ? 'PHARMACY SAFETY CLEARED — APPROVED FOR DISPENSING'
                        : 'PHARMACY HOLD — CLINICAL CONTRAINDICATIONS FLAGGED'}
                    </h3>
                    <p className="text-xs opacity-80">
                      Report ID: {report.id} • Reviewed by {report.pharmacist_name}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleToggleSpeech}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                      isSpeaking
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : 'bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700'
                    }`}
                  >
                    {isSpeaking ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                    <span>{isSpeaking ? 'Stop Voice' : 'Dr. Rostova Voice'}</span>
                  </button>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-mono font-bold uppercase ${
                      report.safety_cleared
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                    }`}
                  >
                    {report.dispensing_status}
                  </span>
                </div>

              </div>

              {/* Warnings and Interventions */}
              {report.flagged_contraindications.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertOctagon className="w-4 h-4" />
                    Flagged Clinical Contraindications ({report.flagged_contraindications.length}):
                  </h4>
                  <div className="space-y-1.5">
                    {report.flagged_contraindications.map((contra, i) => (
                      <div
                        key={i}
                        className="px-3 py-2 rounded-xl bg-rose-950/30 border border-rose-900/60 text-xs text-rose-200"
                      >
                        {contra}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Allergy Warnings */}
              {report.allergy_warnings.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    Allergy Warnings ({report.allergy_warnings.length}):
                  </h4>
                  <div className="space-y-1.5">
                    {report.allergy_warnings.map((warn, i) => (
                      <div
                        key={i}
                        className="px-3 py-2 rounded-xl bg-amber-950/30 border border-amber-900/60 text-xs text-amber-200"
                      >
                        {warn}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Renal Adjustments */}
              {report.renal_adjustments.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="w-4 h-4" />
                    Renal Dose Adjustments & Nephrotoxicity Warnings:
                  </h4>
                  <div className="space-y-1.5">
                    {report.renal_adjustments.map((adj, i) => (
                      <div
                        key={i}
                        className="px-3 py-2 rounded-xl bg-cyan-950/30 border border-cyan-900/60 text-xs text-cyan-200"
                      >
                        {adj}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Clinical Interventions Required */}
              {report.clinical_interventions.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-teal-400 uppercase tracking-wider">
                    Pharmacist Clinical Recommendations:
                  </h4>
                  <div className="space-y-1.5">
                    {report.clinical_interventions.map((inte, i) => (
                      <div
                        key={i}
                        className="px-3 py-2 rounded-xl bg-teal-950/30 border border-teal-900/60 text-xs text-teal-200 flex items-start gap-2"
                      >
                        <span className="text-teal-400 font-bold">•</span>
                        <span>{inte}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Approved Medications */}
              {report.approved_medications.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Approved Medications Cleared for Dispensing ({report.approved_medications.length}):
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {report.approved_medications.map((med, i) => (
                      <div
                        key={i}
                        className="px-3 py-2 rounded-xl bg-emerald-950/20 border border-emerald-900/40 text-xs text-emerald-200 flex items-center gap-2"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span className="truncate">{med}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
