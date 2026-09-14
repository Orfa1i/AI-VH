import React, { useState } from 'react';
import type { ClinicalReport, PhysicianReviewPayload } from '../../types';
import {
  FileText,
  CheckCircle2,
  XCircle,
  BookOpen,
  Award,
  Stethoscope,
  TestTube,
  Clock,
  ShieldCheck,
  User,
} from 'lucide-react';

interface PhysicianReviewDashboardProps {
  reports: ClinicalReport[];
  onSubmitReview: (review: PhysicianReviewPayload) => Promise<void>;
  isSubmitting?: boolean;
}

export const PhysicianReviewDashboard: React.FC<PhysicianReviewDashboardProps> = ({
  reports,
  onSubmitReview,
  isSubmitting = false,
}) => {
  const [selectedReportId, setSelectedReportId] = useState<string>(
    reports.length > 0 ? reports[0].id : ''
  );

  // Review Form State
  const [diagnosisGrade, setDiagnosisGrade] = useState('CORRECT');
  const [reasoningGrade, setReasoningGrade] = useState('SOUND');
  const [testsGrade, setTestsGrade] = useState('APPROPRIATE');
  const [treatmentGrade, setTreatmentGrade] = useState('SAFE_AND_OPTIMAL');
  const [overallScore, setOverallScore] = useState<number>(5);
  const [notes, setNotes] = useState('');
  const [correctedDiagnosis, setCorrectedDiagnosis] = useState('');
  const [submittedReviewSuccess, setSubmittedReviewSuccess] = useState(false);

  const activeReport = reports.find((r) => r.id === selectedReportId) || reports[0];

  const handleReviewAction = async (approved: boolean) => {
    if (!activeReport) return;
    try {
      await onSubmitReview({
        report_id: activeReport.id,
        physician_name: 'Dr. Attending Physician, MD',
        diagnosis_grade: diagnosisGrade,
        reasoning_grade: reasoningGrade,
        tests_grade: testsGrade,
        treatment_grade: treatmentGrade,
        overall_score: overallScore,
        approved,
        notes: notes || (approved ? 'Diagnosis and treatment plan approved as presented.' : 'Revision required.'),
        corrected_diagnosis: correctedDiagnosis || undefined,
      });
      setSubmittedReviewSuccess(true);
      setTimeout(() => setSubmittedReviewSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to submit review:', err);
    }
  };

  if (reports.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-slate-400">
        <FileText className="w-12 h-12 text-slate-600 mb-3" />
        <h3 className="text-lg font-bold text-slate-200">No Clinical Reports Yet</h3>
        <p className="text-sm max-w-md text-center mt-1 text-slate-400">
          Run an encounter in the 3D Virtual Hospital simulation to generate autonomous MedGemma clinical reports for review.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-950 text-slate-200">
      {/* Sidebar: Report Queue */}
      <div className="w-80 border-r border-slate-800 bg-slate-900/60 flex flex-col">
        <div className="p-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-sky-400" />
            <h2 className="text-sm font-bold tracking-wider text-slate-100 uppercase">
              Clinical Report Queue
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {reports.length} autonomous report{reports.length > 1 ? 's' : ''} available
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {reports.map((rep) => {
            const isSelected = rep.id === activeReport?.id;
            return (
              <div
                key={rep.id}
                onClick={() => setSelectedReportId(rep.id)}
                className={`p-3 rounded-xl border cursor-pointer transition-all duration-200 ${
                  isSelected
                    ? 'bg-sky-950/40 border-sky-500 shadow-md shadow-sky-500/10 text-white'
                    : 'bg-slate-800/40 border-slate-800 hover:border-slate-700 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-bold text-sky-400 font-mono">{rep.id}</span>
                  <span className="text-[11px] text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(rep.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <div className="font-semibold text-sm truncate">{rep.patient_name}</div>
                <div className="text-xs text-slate-400 truncate mt-0.5">
                  Dx: {rep.primary_diagnosis}
                </div>
                <div className="mt-2 flex items-center justify-between text-[11px]">
                  <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono">
                    {(rep.diagnostic_confidence * 100).toFixed(0)}% Conf
                  </span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" /> Ready
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Panel: Report Detail & Physician Review Form */}
      {activeReport && (
        <div className="flex-1 flex overflow-hidden">
          {/* Left: The Clinical Report View */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 border-r border-slate-800/80 max-w-3xl">
            {/* Header / Demographics Card */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                <div>
                  <span className="text-xs font-mono text-sky-400 font-bold uppercase tracking-wider">
                    Official AI Clinical Encounter Report • {activeReport.id}
                  </span>
                  <h1 className="text-xl font-bold text-slate-100 mt-1">
                    {activeReport.patient_name}
                  </h1>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400 font-mono">
                    Encounter: {activeReport.encounter_id}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {activeReport.patient_age} yrs • {activeReport.patient_sex}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-400 font-semibold block mb-1">Chief Complaint</span>
                  <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60 font-medium text-slate-200">
                    "{activeReport.chief_complaint}"
                  </div>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold block mb-1">Intake Vital Signs</span>
                  <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60 font-mono text-slate-300">
                    BP {activeReport.vital_signs.systolic_bp}/{activeReport.vital_signs.diastolic_bp} mmHg • HR {activeReport.vital_signs.heart_rate} bpm • SpO2 {activeReport.vital_signs.spo2_percent}%
                  </div>
                </div>
              </div>

              <div className="mt-4 text-xs">
                <span className="text-slate-400 font-semibold block mb-1">
                  History of Present Illness (HPI)
                </span>
                <p className="text-slate-300 leading-relaxed bg-slate-800/40 p-3 rounded-lg border border-slate-800">
                  {activeReport.history_of_present_illness}
                </p>
              </div>
            </div>

            {/* Diagnostic Investigations & Laboratory Findings */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
              <div className="flex items-center gap-2 mb-3">
                <TestTube className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Diagnostic Investigations & Results
                </h3>
              </div>
              <div className="space-y-2">
                {activeReport.investigation_results.map((res, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/60 text-xs"
                  >
                    <div className="flex items-center justify-between font-semibold mb-1">
                      <span className="text-indigo-300">{res.test_type}</span>
                      <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 text-[10px]">
                        COMPLETED
                      </span>
                    </div>
                    <p className="text-slate-300 mt-1">{res.interpretation}</p>
                    <div className="mt-2 grid grid-cols-2 gap-1 font-mono text-[11px] text-slate-400">
                      {Object.entries(res.values).map(([k, v]) => (
                        <div key={k} className="truncate">
                          <span className="text-slate-500">{k}:</span> {String(v)}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Assessment & MedGemma Clinical Synthesis */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Award className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                    Assessment & Clinical Reasoning
                  </h3>
                </div>
                <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-mono font-bold">
                  {(activeReport.diagnostic_confidence * 100).toFixed(0)}% Confidence
                </span>
              </div>

              <div className="p-3.5 rounded-lg bg-emerald-950/30 border border-emerald-800/60 mb-4">
                <span className="text-xs text-emerald-400 font-semibold block uppercase">
                  Primary Diagnosis
                </span>
                <span className="text-lg font-bold text-emerald-200 block mt-0.5">
                  {activeReport.primary_diagnosis}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed bg-slate-800/40 p-3 rounded-lg border border-slate-800 mb-4">
                {activeReport.clinical_reasoning}
              </p>

              {/* Differential Diagnosis Table */}
              <div className="mb-4">
                <span className="text-xs font-semibold text-slate-400 block mb-2">
                  Differential Diagnoses Considered
                </span>
                <div className="space-y-1.5">
                  {activeReport.differential_diagnosis.map((d, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2 rounded bg-slate-800/50 border border-slate-700/50 text-xs"
                    >
                      <span className="font-medium text-slate-200">{d.condition}</span>
                      <span className="font-mono text-sky-400">
                        {(d.likelihood * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Medical Knowledge Citations (Harrison's Internal Medicine) */}
              {activeReport.medical_knowledge_citations.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-purple-400 mb-2">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Evidence Retrieved from Harrison's Principles of Internal Medicine</span>
                  </div>
                  <div className="space-y-2">
                    {activeReport.medical_knowledge_citations.map((c, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-purple-950/20 border border-purple-900/40 text-xs"
                      >
                        <div className="font-bold text-purple-300">
                          {c.chapter} • Page {c.page}
                        </div>
                        <p className="text-slate-300 text-[11px] mt-1 italic">
                          "{c.text.slice(0, 220)}..."
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Treatment Plan */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-3">
                Guideline-Directed Treatment Regimen
              </h3>
              <ul className="space-y-2 text-xs">
                {activeReport.treatment_plan.map((item, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2.5 p-2 rounded bg-slate-800/40 border border-slate-800"
                  >
                    <span className="w-5 h-5 rounded-full bg-sky-950 border border-sky-800 text-sky-400 flex items-center justify-center font-mono font-bold text-[10px] shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span className="text-slate-300 leading-normal">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right: Expert Physician Review Form */}
          <div className="w-96 bg-slate-900/90 p-6 overflow-y-auto border-l border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 pb-4 border-b border-slate-800">
                <User className="w-5 h-5 text-emerald-400" />
                <div>
                  <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                    Attending Physician Review
                  </h2>
                  <p className="text-xs text-slate-400">Structured clinical oversight</p>
                </div>
              </div>

              {submittedReviewSuccess && (
                <div className="my-4 p-3 rounded-lg bg-emerald-500/20 border border-emerald-500/50 text-emerald-200 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Review recorded & merged into RL preference dataset!</span>
                </div>
              )}

              {/* Form Controls */}
              <div className="space-y-4 my-4 text-xs">
                {/* 1. Diagnosis Accuracy */}
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Diagnosis Concordance
                  </label>
                  <select
                    value={diagnosisGrade}
                    onChange={(e) => setDiagnosisGrade(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    <option value="CORRECT">Correct (High Concordance)</option>
                    <option value="PARTIALLY_CORRECT">Partially Correct</option>
                    <option value="INCORRECT">Incorrect (Missed Diagnosis)</option>
                  </select>
                </div>

                {/* 2. Reasoning Quality */}
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Clinical Reasoning
                  </label>
                  <select
                    value={reasoningGrade}
                    onChange={(e) => setReasoningGrade(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    <option value="SOUND">Sound & Evidence-based</option>
                    <option value="MISSING_CRITICAL_EVIDENCE">Missing Critical Evidence</option>
                    <option value="FAULTY_LOGIC">Faulty Logical Leap</option>
                    <option value="UNSUPPORTED_CONCLUSION">Unsupported Conclusion</option>
                  </select>
                </div>

                {/* 3. Diagnostic Tests Appropriateness */}
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Workup & Lab Ordering
                  </label>
                  <select
                    value={testsGrade}
                    onChange={(e) => setTestsGrade(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    <option value="APPROPRIATE">Appropriate & Indicated</option>
                    <option value="OVER_ORDERING">Over-ordering / Defensive</option>
                    <option value="MISSING_ESSENTIAL_TEST">Missing Essential Guideline Test</option>
                    <option value="INAPPROPRIATE_TEST">Inappropriate / Unsafe Test</option>
                  </select>
                </div>

                {/* 4. Treatment Safety */}
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Treatment Safety & Efficacy
                  </label>
                  <select
                    value={treatmentGrade}
                    onChange={(e) => setTreatmentGrade(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    <option value="SAFE_AND_OPTIMAL">Safe & Guideline-optimal</option>
                    <option value="SUBOPTIMAL">Suboptimal Intervention</option>
                    <option value="CONTRAINDICATED_OR_HARMFUL">Contraindicated / Harmful</option>
                  </select>
                </div>

                {/* 5. Overall Score */}
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Overall Clinical Score (1–5)
                  </label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((score) => (
                      <button
                        key={score}
                        type="button"
                        onClick={() => setOverallScore(score)}
                        className={`flex-1 py-1.5 rounded font-bold border transition-all ${
                          overallScore === score
                            ? 'bg-sky-500 text-white border-sky-400'
                            : 'bg-slate-800 text-slate-400 border-slate-700 hover:border-slate-600'
                        }`}
                      >
                        {score}★
                      </button>
                    ))}
                  </div>
                </div>

                {/* Optional Corrected Diagnosis */}
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Corrected Diagnosis (if applicable)
                  </label>
                  <input
                    type="text"
                    value={correctedDiagnosis}
                    onChange={(e) => setCorrectedDiagnosis(e.target.value)}
                    placeholder="Enter revised or refined clinical diagnosis..."
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 text-xs"
                  />
                </div>

                {/* 6. Physician Notes */}
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Physician Feedback Notes
                  </label>
                  <textarea
                    rows={3}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Enter clinical critique, rationale, or training guidance..."
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 text-xs"
                  />
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-4 border-t border-slate-800 space-y-2">
              <button
                disabled={isSubmitting}
                onClick={() => handleReviewAction(true)}
                className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/30 transition-all cursor-pointer disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Approve Clinical Report</span>
              </button>
              <button
                disabled={isSubmitting}
                onClick={() => handleReviewAction(false)}
                className="w-full py-2.5 px-4 rounded-xl bg-rose-950/80 hover:bg-rose-900 border border-rose-700/60 text-rose-300 font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50 text-xs"
              >
                <XCircle className="w-4 h-4" />
                <span>Reject & Request Revision</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
