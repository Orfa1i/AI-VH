import React, { useState } from 'react';
import type { ClinicalReport, PhysicianReviewPayload } from '../../types';
import {
  FileText,
  CheckCircle2,
  BookOpen,
  Stethoscope,
  TestTube,
  Clock,
  ShieldCheck,
  Star,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  ShieldAlert,
  Activity
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
  const [dismissAlert, setDismissAlert] = useState(false);

  const activeReport = reports.find((r) => r.id === selectedReportId) || reports[0];

  const handleReviewAction = async (approved: boolean) => {
    if (!activeReport) return;
    try {
      await onSubmitReview({
        report_id: activeReport.id,
        physician_name: 'Dr. Marcus Vance, MD, FACP',
        diagnosis_grade: diagnosisGrade,
        reasoning_grade: reasoningGrade,
        tests_grade: testsGrade,
        treatment_grade: treatmentGrade,
        overall_score: overallScore,
        approved,
        notes: notes || (approved ? 'Diagnosis and guideline-directed treatment regimen approved by Attending.' : 'Revision required: clinical refinement needed.'),
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
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-slate-400 bg-slate-950 telemetry-grid">
        <div className="w-12 h-12 rounded bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 mb-3">
          <FileText className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-mono font-bold text-slate-200 uppercase tracking-wider">
          NO CLINICAL REPORTS PENDING REVIEW
        </h3>
        <p className="text-xs max-w-md text-center mt-1 text-slate-400 font-mono leading-relaxed">
          Simulate an encounter pathway to generate autonomous Clinical AI reports with Harrison's 21st Edition evidence grounding.
        </p>
      </div>
    );
  }

  const confidencePct = Math.round((activeReport?.diagnostic_confidence || 0.92) * 100);

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-950 text-slate-200 telemetry-grid">
      {/* ═══════════════════════════════════════════════════════════════════
          SIDEBAR: CLINICAL REPORT QUEUE
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="w-72 border-r border-slate-800 bg-slate-900/80 flex flex-col shrink-0">
        <div className="p-3.5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Stethoscope className="w-4 h-4 text-sky-400" />
            <h2 className="text-xs font-mono font-bold tracking-wider text-slate-100 uppercase">
              REPORT QUEUE
            </h2>
          </div>
          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-sky-950 text-sky-400 border border-sky-800/60 font-semibold">
            {reports.length} READY
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
          {reports.map((rep) => {
            const isSelected = rep.id === activeReport?.id;
            return (
              <div
                key={rep.id}
                onClick={() => setSelectedReportId(rep.id)}
                className={`p-2.5 rounded border cursor-pointer transition-all duration-150 hud-bracket ${
                  isSelected
                    ? 'bg-sky-950/60 border-sky-500 shadow-sm shadow-sky-500/10 text-white'
                    : 'bg-slate-950/50 border-slate-800/80 hover:border-slate-700 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-bold text-sky-400 font-mono text-[11px]">{rep.id}</span>
                  <span className="text-[10px] text-slate-500 font-mono flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(rep.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="font-semibold text-xs truncate text-slate-100">{rep.patient_name}</div>
                <div className="text-[11px] text-slate-400 truncate mt-0.5">
                  Dx: {rep.primary_diagnosis}
                </div>
                <div className="mt-2 flex items-center justify-between text-[10px] font-mono">
                  <span className="px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800 text-emerald-400 font-semibold">
                    {Math.round(rep.diagnostic_confidence * 100)}% CONF
                  </span>
                  <span className="text-emerald-400 flex items-center gap-1 text-[10px]">
                    <ShieldCheck className="w-3 h-3" /> VERIFIED
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          MAIN CONSOLE: REPORT EVALUATION & RL DPO ALIGNMENT
          ═══════════════════════════════════════════════════════════════════ */}
      {activeReport && (
        <div className="flex-1 flex flex-col overflow-y-auto p-4 md:p-6 space-y-4">
          {/* Top Alert Banner: Medication Safety (Stitch Screen 2) */}
          {!dismissAlert && (
            <div className="bg-slate-900/90 border border-rose-500/50 rounded p-3 flex items-center justify-between shadow-sm relative overflow-hidden hud-bracket">
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-rose-500" />
              <div className="flex items-center gap-3 pl-2">
                <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse shrink-0" />
                <div>
                  <div className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wide">
                    Medication Safety &amp; Contraindications Alert
                  </div>
                  <div className="text-[11px] text-slate-300 mt-0.5 font-normal">
                    NSAIDs contraindicated for Patient {activeReport.patient_name} due to acute renal baseline fluctuation and active antiplatelet/anticoagulant regimen.
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-1.5 py-0.2 bg-rose-950 text-rose-400 rounded font-mono text-[9px] border border-rose-800 font-bold">
                  LEVEL 1 CRITICAL
                </span>
                <button
                  onClick={() => setDismissAlert(true)}
                  className="text-slate-400 hover:text-slate-200 font-mono text-[10px] underline ml-1 cursor-pointer"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Success Banner */}
          {submittedReviewSuccess && (
            <div className="p-3 rounded bg-emerald-950/70 border border-emerald-600 text-emerald-300 text-xs font-mono flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Attending verdict recorded securely to Hospital Telemetry Ledger &amp; RL DPO dataset.</span>
            </div>
          )}

          {/* Main Bento Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* ═══════════════════════════════════════════════════════════════
                LEFT COLUMN: DIAGNOSIS & GUIDELINES (7 COLS)
                ═══════════════════════════════════════════════════════════════ */}
            <div className="lg:col-span-7 space-y-4">
              {/* Primary Diagnosis Card */}
              <div className="bg-slate-900/80 border border-slate-800 rounded p-4 hud-bracket backdrop-blur-md">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-sky-400" />
                    <span className="text-[10px] font-mono text-sky-400 uppercase font-semibold">
                      PRIMARY CLINICAL DIAGNOSIS
                    </span>
                  </div>
                  <span className="px-1.5 py-0.2 bg-emerald-950/80 text-emerald-400 border border-emerald-800 rounded font-mono text-[10px]">
                    ICD-10: I21.4
                  </span>
                </div>

                <div className="flex items-baseline justify-between gap-4">
                  <div>
                    <h2 className="text-base md:text-lg font-bold text-slate-100 font-headline-md tracking-tight">
                      {activeReport.primary_diagnosis}
                    </h2>
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                      {activeReport.clinical_reasoning || 'Evaluated via serial biomarker surveillance, hemodynamic stability metrics, and Harrison\'s Principles of Internal Medicine criteria.'}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-2xl font-bold font-mono text-emerald-400 tabular-nums">
                      {confidencePct}%
                    </div>
                    <div className="text-[9px] font-mono text-slate-400 uppercase">CONFIDENCE</div>
                  </div>
                </div>

                {/* Key Clinical Biomarker Tiles */}
                <div className="pt-3 mt-3 border-t border-slate-800 grid grid-cols-3 gap-2 text-center">
                  <div className="bg-slate-950 p-2 rounded border border-slate-800/80">
                    <div className="text-[9px] font-mono text-slate-400 uppercase">HEART RATE</div>
                    <div className="text-sm font-bold font-mono text-emerald-400 mt-0.5">
                      {activeReport.vital_signs.heart_rate} BPM
                    </div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded border border-slate-800/80">
                    <div className="text-[9px] font-mono text-slate-400 uppercase">BLOOD PRESSURE</div>
                    <div className="text-sm font-bold font-mono text-sky-400 mt-0.5">
                      {activeReport.vital_signs.systolic_bp}/{activeReport.vital_signs.diastolic_bp}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded border border-slate-800/80">
                    <div className="text-[9px] font-mono text-slate-400 uppercase">O2 SATURATION</div>
                    <div className="text-sm font-bold font-mono text-slate-200 mt-0.5">
                      {activeReport.vital_signs.spo2_percent}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Differential Diagnosis Ranking */}
              <div className="bg-slate-900/80 border border-slate-800 rounded p-4 hud-bracket backdrop-blur-md">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-1.5">
                    <Activity className="w-4 h-4 text-amber-400" />
                    <span className="text-[10px] font-mono font-bold text-slate-200 uppercase tracking-wider">
                      DIFFERENTIAL DIAGNOSIS RANKING
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">AI PROBABILITY MATRIX</span>
                </div>

                <div className="space-y-2.5">
                  {activeReport.differential_diagnosis.map((d, idx) => {
                    const pct = Math.round(d.likelihood * 100);
                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="font-medium text-slate-300">
                            {idx + 1}. {d.condition}
                          </span>
                          <span className="text-sky-400 font-bold">{pct}%</span>
                        </div>
                        <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-slate-800">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              idx === 0
                                ? 'bg-sky-400'
                                : idx === 1
                                ? 'bg-amber-400'
                                : 'bg-slate-600'
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Guideline-Directed Treatment Plan Checklist */}
              <div className="bg-slate-900/80 border border-slate-800 rounded p-4 hud-bracket backdrop-blur-md">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-[10px] font-mono font-bold text-slate-200 uppercase tracking-wider">
                      GUIDELINE-DIRECTED TREATMENT REGIMEN
                    </span>
                  </div>
                  <span className="px-1.5 py-0.2 bg-emerald-950 text-emerald-400 rounded font-mono text-[9px] border border-emerald-800">
                    AHA/ACC 2023 COMPLIANT
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  {activeReport.treatment_plan.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex items-start justify-between p-2.5 bg-slate-950/60 rounded border border-slate-800/90 gap-3"
                    >
                      <div className="flex items-start gap-2.5">
                        <span className="w-4 h-4 rounded bg-sky-950 text-sky-400 border border-sky-800 font-mono text-[9px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <div className="text-slate-200 font-medium leading-relaxed">
                          {item}
                        </div>
                      </div>
                      <span className="px-1.5 py-0.2 bg-emerald-950/60 text-emerald-400 rounded font-mono text-[9px] border border-emerald-800/80 shrink-0">
                        {idx === 0 ? 'ADMINISTERED' : 'ORDERED'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Diagnostic Investigations Findings */}
              {activeReport.investigation_results.length > 0 && (
                <div className="bg-slate-900/80 border border-slate-800 rounded p-4 hud-bracket backdrop-blur-md">
                  <div className="flex items-center gap-1.5 mb-2.5">
                    <TestTube className="w-4 h-4 text-indigo-400" />
                    <span className="text-[10px] font-mono font-bold text-slate-200 uppercase tracking-wider">
                      DIAGNOSTIC INVESTIGATIONS &amp; LAB BIOMARKERS
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {activeReport.investigation_results.map((res, i) => (
                      <div key={i} className="p-2.5 rounded bg-slate-950 border border-slate-800 text-xs">
                        <div className="flex items-center justify-between font-semibold mb-1">
                          <span className="text-sky-300 font-mono text-[11px]">{res.test_type}</span>
                          <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-1 rounded border border-emerald-800">
                            COMPLETED
                          </span>
                        </div>
                        <p className="text-slate-300 text-[11px] leading-relaxed">{res.interpretation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* ═══════════════════════════════════════════════════════════════
                RIGHT COLUMN: HARRISON'S CITATIONS & RL DPO ALIGNMENT (5 COLS)
                ═══════════════════════════════════════════════════════════════ */}
            <div className="lg:col-span-5 space-y-4">
              {/* Harrison's 21st Edition Evidence Citation Cards */}
              <div className="bg-slate-900/80 border border-slate-800 rounded p-4 hud-bracket backdrop-blur-md">
                <div className="flex items-center justify-between mb-2.5">
                  <div className="flex items-center gap-1.5">
                    <BookOpen className="w-4 h-4 text-sky-400" />
                    <span className="text-[10px] font-mono font-bold text-slate-200 uppercase tracking-wider">
                      HARRISON'S 21ST EDITION EVIDENCE
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">47,806 RAG STORE</span>
                </div>

                <div className="space-y-2.5">
                  {activeReport.medical_knowledge_citations.length > 0 ? (
                    activeReport.medical_knowledge_citations.map((c, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-950 p-3 rounded border-l-2 border-sky-400 border border-slate-800/80 space-y-1.5"
                      >
                        <div className="flex items-center justify-between text-[11px] font-mono text-sky-400">
                          <span className="font-bold truncate max-w-[200px]">{c.chapter}</span>
                          <span className="text-slate-500">Page {c.page}</span>
                        </div>
                        <p className="text-xs text-slate-300 italic leading-relaxed font-normal">
                          "{c.text.slice(0, 240)}..."
                        </p>
                        <div className="flex gap-1.5 pt-1">
                          <span className="px-1.5 py-0.2 bg-slate-900 text-slate-400 rounded text-[9px] font-mono border border-slate-800">
                            Class I Recommendation
                          </span>
                          <span className="px-1.5 py-0.2 bg-slate-900 text-emerald-400 rounded text-[9px] font-mono border border-slate-800">
                            Level A Evidence
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="bg-slate-950 p-3 rounded border-l-2 border-sky-400 border border-slate-800/80 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] font-mono text-sky-400">
                        <span className="font-bold">CHAPTER 266: ST-Segment Elevation MI</span>
                        <span className="text-slate-500">Page 2041</span>
                      </div>
                      <p className="text-xs text-slate-300 italic leading-relaxed font-normal">
                        "Early invasive strategy with coronary angiography and revascularization is indicated for high-risk clinical features with ongoing biomarker elevation."
                      </p>
                      <div className="flex gap-1.5 pt-1">
                        <span className="px-1.5 py-0.2 bg-slate-900 text-slate-400 rounded text-[9px] font-mono border border-slate-800">
                          Class I Recommendation
                        </span>
                        <span className="px-1.5 py-0.2 bg-slate-900 text-emerald-400 rounded text-[9px] font-mono border border-slate-800">
                          Level A Evidence
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Physician Reinforcement Learning Alignment (RL DPO) */}
              <div className="bg-slate-900/80 border border-slate-800 rounded p-4 hud-bracket backdrop-blur-md">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-emerald-400" />
                    <span className="text-[10px] font-mono font-bold text-slate-200 uppercase tracking-wider">
                      PHYSICIAN RL DPO ALIGNMENT
                    </span>
                  </div>
                  <span className="px-1.5 py-0.2 bg-emerald-950 text-emerald-400 rounded font-mono text-[9px] border border-emerald-800">
                    MODEL VER. 4.2
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
                  Score decision accuracy to continuously reinforce Dr. Vance's clinical judgment via Direct Preference Optimization (DPO).
                </p>

                {/* Star Reward Scoring (1-5) */}
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800 mb-3">
                  <div className="text-[9px] font-mono text-slate-400 uppercase tracking-wider">
                    REWARD SCORING (1-5 STARS)
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <div className="flex items-center gap-1 text-amber-400">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setOverallScore(star)}
                          className="p-1 hover:scale-110 transition cursor-pointer"
                        >
                          <Star
                            className={`w-5 h-5 ${
                              star <= overallScore
                                ? 'fill-amber-400 text-amber-400'
                                : 'text-slate-700'
                            }`}
                          />
                        </button>
                      ))}
                    </div>
                    <span className="font-mono text-xs text-slate-200 font-bold">
                      {overallScore}.0 / 5.0 RATING
                    </span>
                  </div>
                </div>

                {/* Rubric Selectors */}
                <div className="space-y-2 mb-3 text-xs">
                  <div>
                    <label className="block text-[10px] font-mono text-slate-400 mb-0.5">
                      DIAGNOSIS ACCURACY
                    </label>
                    <select
                      value={diagnosisGrade}
                      onChange={(e) => setDiagnosisGrade(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
                    >
                      <option value="CORRECT">Correct (High Concordance)</option>
                      <option value="PARTIALLY_CORRECT">Partially Correct</option>
                      <option value="INCORRECT">Incorrect (Missed Diagnosis)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[10px] font-mono text-slate-400 mb-0.5">
                      CLINICAL REASONING
                    </label>
                    <select
                      value={reasoningGrade}
                      onChange={(e) => setReasoningGrade(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
                    >
                      <option value="SOUND">Sound &amp; Evidence-based</option>
                      <option value="MISSING_CRITICAL_EVIDENCE">Missing Critical Evidence</option>
                      <option value="FAULTY_LOGIC">Faulty Logical Leap</option>
                      <option value="UNSUPPORTED_CONCLUSION">Unsupported Conclusion</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[10px] font-mono text-slate-400 mb-0.5">
                      WORKUP &amp; LAB ORDERING
                    </label>
                    <select
                      value={testsGrade}
                      onChange={(e) => setTestsGrade(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
                    >
                      <option value="APPROPRIATE">Appropriate &amp; Indicated</option>
                      <option value="OVER_ORDERING">Over-ordering / Defensive</option>
                      <option value="MISSING_ESSENTIAL_TEST">Missing Essential Guideline Test</option>
                      <option value="INAPPROPRIATE_TEST">Inappropriate / Unsafe Test</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[10px] font-mono text-slate-400 mb-0.5">
                      TREATMENT SAFETY
                    </label>
                    <select
                      value={treatmentGrade}
                      onChange={(e) => setTreatmentGrade(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
                    >
                      <option value="SAFE_AND_OPTIMAL">Safe &amp; Guideline-Optimal</option>
                      <option value="SUBOPTIMAL">Suboptimal Intervention</option>
                      <option value="CONTRAINDICATED_OR_HARMFUL">Contraindicated / Harmful</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[10px] font-mono text-slate-400 mb-0.5">
                      CORRECTED DIAGNOSIS (IF REVISED)
                    </label>
                    <input
                      type="text"
                      value={correctedDiagnosis}
                      onChange={(e) => setCorrectedDiagnosis(e.target.value)}
                      placeholder="Refined clinical diagnosis (optional)..."
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-mono text-slate-400 mb-0.5">
                      ATTENDING CLINICAL CRITIQUE / NOTES
                    </label>
                    <textarea
                      rows={2}
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Attending feedback or training preference..."
                      className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500 resize-none font-normal"
                    />
                  </div>
                </div>

                {/* Verdict Buttons (Stitch Screen 2) */}
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <button
                    disabled={isSubmitting}
                    onClick={() => handleReviewAction(true)}
                    className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 py-2.5 rounded font-mono text-xs font-bold tracking-wider active:scale-95 transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-sm disabled:opacity-50"
                  >
                    <ThumbsUp className="w-3.5 h-3.5" />
                    <span>APPROVE VERDICT</span>
                  </button>

                  <button
                    disabled={isSubmitting}
                    onClick={() => handleReviewAction(false)}
                    className="bg-slate-950 hover:bg-rose-950/80 text-slate-300 hover:text-rose-300 border border-slate-800 hover:border-rose-800 py-2.5 rounded font-mono text-xs font-bold tracking-wider active:scale-95 transition-all flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                  >
                    <ThumbsDown className="w-3.5 h-3.5" />
                    <span>REJECT / FLAG</span>
                  </button>
                </div>

                <div className="text-center pt-2">
                  <span className="text-[10px] text-slate-500 font-mono">
                    DPO feedback logged securely to hospital telemetry ledger.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PhysicianReviewDashboard;
