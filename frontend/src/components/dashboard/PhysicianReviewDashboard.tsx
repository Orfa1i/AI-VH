import React, { useState } from 'react';
import type { ClinicalReport, PhysicianReviewPayload, ReviewAssessment, ReviewErrorTaxonomy } from '../../types';
import { REVIEW_ASSESSMENTS, STRUCTURED_ERROR_TAXONOMY } from '../review/taxonomy';
import {
  FileText,
  CheckCircle2,
  BookOpen,
  Stethoscope,
  TestTube,
  Star,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  Activity,
  HeartPulse,
  Thermometer,
  RotateCcw,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Database,
} from 'lucide-react';

interface PhysicianReviewDashboardProps {
  reports: ClinicalReport[];
  onSubmitReview: (review: PhysicianReviewPayload) => Promise<void>;
  isSubmitting?: boolean;
  onResetData?: () => void;
}

export const PhysicianReviewDashboard: React.FC<PhysicianReviewDashboardProps> = ({
  reports,
  onSubmitReview,
  isSubmitting = false,
  onResetData,
}) => {
  const [selectedReportId, setSelectedReportId] = useState<string>(
    reports.length > 0 ? reports[0].id : ''
  );

  const handleResetReports = async () => {
    if (!window.confirm('Reset all test reports, reviews, and pending queue back to zero for a fresh start?')) {
      return;
    }
    try {
      const res = await fetch('/api/database/purge-mock-data', { method: 'POST' });
      if (res.ok && onResetData) {
        onResetData();
      }
    } catch (err) {
      console.error('Failed to reset reports:', err);
    }
  };


  // Structured Review Form State
  const [assessment, setAssessment] = useState<ReviewAssessment>('CORRECT');
  const [identifiedErrors, setIdentifiedErrors] = useState<ReviewErrorTaxonomy[]>([]);
  const [diagnosisGrade, setDiagnosisGrade] = useState('CORRECT');
  const [reasoningGrade, setReasoningGrade] = useState('SOUND');
  const [testsGrade, setTestsGrade] = useState('APPROPRIATE');
  const [treatmentGrade, setTreatmentGrade] = useState('SAFE_AND_OPTIMAL');
  const [overallScore, setOverallScore] = useState<number>(5);
  const [notes, setNotes] = useState('');
  const [correctedDiagnosis, setCorrectedDiagnosis] = useState('');
  const [correctedReasoning, setCorrectedReasoning] = useState('');
  const [correctedRecommendations, setCorrectedRecommendations] = useState('');
  const [reviewerRole, setReviewerRole] = useState('ATTENDING_PHYSICIAN');
  const [submittedReviewSuccess, setSubmittedReviewSuccess] = useState(false);
  const [evaluatingReport, setEvaluatingReport] = useState(false);

  const toggleErrorTag = (tag: ReviewErrorTaxonomy) => {
    setIdentifiedErrors((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleTriggerEvaluation = async (reportId: string) => {
    setEvaluatingReport(true);
    try {
      const res = await fetch(`/api/reports/${reportId}/evaluate`, { method: 'POST' });
      if (res.ok) {
        const evalData = await res.json();
        const target = reports.find((r) => r.id === reportId);
        if (target) {
          target.automated_evaluation = evalData;
          setSelectedReportId(reportId);
        }
      }
    } catch (err) {
      console.error('Failed to run on-demand evaluation:', err);
    } finally {
      setEvaluatingReport(false);
    }
  };

  const activeReport = reports.find((r) => r.id === selectedReportId) || reports[0];

  const getScoreDescription = (score: number): string => {
    switch (score) {
      case 5:
        return '5.0 / 5.0 : Gold Standard Guideline Alignment';
      case 4:
        return '4.0 / 5.0 : Sound Clinical Judgment with Minor Variations';
      case 3:
        return '3.0 / 5.0 : Borderline Acceptable : Additional Testing Indicated';
      case 2:
        return '2.0 / 5.0 : Suboptimal Decision Making : Guideline Divergence';
      case 1:
        return '1.0 / 5.0 : Critical Discrepancy : Unsafe Clinical Pathway';
      default:
        return `${score}.0 / 5.0 Rating`;
    }
  };

  const handleReviewAction = async (approved: boolean) => {
    if (!activeReport) return;
    try {
      await onSubmitReview({
        report_id: activeReport.id,
        physician_name: 'Dr. Marcus Vance, MD, FACP',
        reviewer_role: reviewerRole,
        specialty: (activeReport as any).specialty || 'INTERNAL_MEDICINE',
        assessment,
        identified_errors: identifiedErrors,
        diagnosis_grade: diagnosisGrade,
        reasoning_grade: reasoningGrade,
        tests_grade: testsGrade,
        treatment_grade: treatmentGrade,
        overall_score: overallScore,
        approved,
        notes: notes || (approved ? 'Diagnosis and guideline-directed treatment regimen approved by Attending.' : 'Revision required: clinical refinement needed.'),
        corrected_diagnosis: correctedDiagnosis.trim() || undefined,
        corrected_reasoning: correctedReasoning.trim() || undefined,
        corrected_recommendations: correctedRecommendations.trim()
          ? correctedRecommendations.split('\n').map((s) => s.trim()).filter(Boolean)
          : undefined,
      });
      setSubmittedReviewSuccess(true);
      setTimeout(() => setSubmittedReviewSuccess(false), 3500);
    } catch (err) {
      console.error('Failed to submit review:', err);
    }
  };

  if (reports.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-slate-600 bg-[#f8fafc] telemetry-grid">
        <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-xs mb-4">
          <div className="w-14 h-14 rounded-xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600">
            <FileText className="w-7 h-7" />
          </div>
        </div>
        <h3 className="text-sm font-mono font-bold text-slate-900 uppercase tracking-widest">
          NO CLINICAL REPORTS PENDING REVIEW
        </h3>
        <p className="text-xs max-w-md text-center mt-2 text-slate-500 font-sans leading-relaxed">
          Simulate an encounter or admit a patient to generate autonomous Clinical AI reports grounded with Harrison's 21st Edition evidence.
        </p>
        <button
          onClick={handleResetReports}
          className="mt-4 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-mono font-semibold flex items-center gap-1.5 border border-slate-300 transition cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
          <span>Reset All Records to Zero</span>
        </button>
      </div>
    );
  }

  const confidencePct = Math.round((activeReport?.diagnostic_confidence || 0.92) * 100);

  return (
    <div className="flex-1 flex flex-col md:flex-row overflow-hidden bg-[#f8fafc] text-slate-900 telemetry-grid">
      {/* ═══════════════════════════════════════════════════════════════════
          SIDEBAR: CLINICAL REPORT QUEUE
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="w-full md:w-80 border-b md:border-b-0 md:border-r border-slate-200 bg-white flex flex-col shrink-0">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 shadow-2xs">
              <Stethoscope className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-xs font-mono font-bold tracking-wider text-slate-900 uppercase">
                CLINICAL QUEUE
              </h2>
              <span className="text-[10px] font-mono text-slate-500">Autonomous Encounters</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleResetReports}
              title="Reset all reports and pending reviews to zero"
              className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-sky-50 text-sky-700 border border-sky-300 font-semibold shadow-2xs">
              {reports.length} READY
            </span>
          </div>
        </div>

        {/* Report Cards Scroll Area */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2.5 max-h-60 md:max-h-none">
          {reports.map((rep) => {
            const isSelected = rep.id === activeReport?.id;
            return (
              <div
                key={rep.id}
                onClick={() => setSelectedReportId(rep.id)}
                className={`p-3 rounded-xl transition-all cursor-pointer border ${
                  isSelected
                    ? 'bg-sky-50 border-sky-300 shadow-xs'
                    : 'bg-slate-50 hover:bg-slate-100 border-slate-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold text-sky-700">
                    {rep.id}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {new Date(rep.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="text-xs font-bold text-slate-900 mt-1 font-sans">
                  {rep.patient_name}
                </div>
                <div className="text-[11px] text-slate-600 truncate mt-0.5 font-sans">
                  {rep.primary_diagnosis}
                </div>
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-200 text-[10px] font-mono">
                  <span className="text-slate-500">CONFIDENCE:</span>
                  <span className="font-bold text-emerald-700 tabular-nums">
                    {Math.round((rep.diagnostic_confidence || 0.9) * 100)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          MAIN DETAIL HORIZON: CLINICAL REPORT & ATTENDING VERDICT
          ═══════════════════════════════════════════════════════════════════ */}
      {activeReport && (
        <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-[#f8fafc]">
          <div className="max-w-4xl mx-auto space-y-5">
            {/* Success Toast */}
            {submittedReviewSuccess && (
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono flex items-center justify-between shadow-xs animate-in fade-in">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Physician review verdict successfully committed to hospital ledger and DPO dataset.</span>
                </div>
              </div>
            )}

            {/* Top Report Header Card */}
            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-sky-50 text-sky-700 border border-sky-200 font-bold">
                      {activeReport.id}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      ENCOUNTER: {activeReport.encounter_id}
                    </span>
                  </div>
                  <h1 className="text-base font-bold text-slate-900 mt-1 font-sans">
                    {activeReport.patient_name}
                  </h1>
                  <p className="text-xs text-slate-500 font-sans mt-0.5">
                    {activeReport.patient_id} • Admitted to Clinical Care Pathway
                  </p>
                </div>

                <div className="sm:text-right shrink-0 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <div className="text-2xl font-bold font-mono text-emerald-700 tabular-nums">
                    {confidencePct}%
                  </div>
                  <div className="text-[9px] font-mono text-slate-500 uppercase tracking-wider">
                    DIAGNOSTIC CONFIDENCE
                  </div>
                </div>
              </div>

              {/* Biomarkers */}
              <div className="pt-4 grid grid-cols-3 gap-2.5 text-center">
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                  <div className="text-[9px] font-mono text-slate-500 uppercase tracking-wider flex items-center justify-center gap-1">
                    <HeartPulse className="w-3 h-3 text-emerald-600" />
                    HEART RATE
                  </div>
                  <div className="text-sm font-bold font-mono text-emerald-700 mt-1 tabular-nums">
                    {activeReport.vital_signs.heart_rate} BPM
                  </div>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                  <div className="text-[9px] font-mono text-slate-500 uppercase tracking-wider flex items-center justify-center gap-1">
                    <Activity className="w-3 h-3 text-sky-600" />
                    BLOOD PRESSURE
                  </div>
                  <div className="text-sm font-bold font-mono text-sky-700 mt-1 tabular-nums">
                    {activeReport.vital_signs.systolic_bp}/{activeReport.vital_signs.diastolic_bp}
                  </div>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                  <div className="text-[9px] font-mono text-slate-500 uppercase tracking-wider flex items-center justify-center gap-1">
                    <Thermometer className="w-3 h-3 text-slate-500" />
                    O2 SATURATION
                  </div>
                  <div className="text-sm font-bold font-mono text-slate-800 mt-1 tabular-nums">
                    {activeReport.vital_signs.spo2_percent}%
                  </div>
                </div>
              </div>
            </div>

            {/* Automated Independent Multi-Stage Evaluation Card */}
            {activeReport.automated_evaluation ? (
              <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    {activeReport.automated_evaluation.passed ? (
                      <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
                        <ShieldCheck className="w-5 h-5" />
                      </div>
                    ) : (
                      <div className="w-8 h-8 rounded-lg bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-700">
                        <ShieldAlert className="w-5 h-5" />
                      </div>
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-mono font-bold text-slate-900 uppercase tracking-wider">
                          INDEPENDENT AUTOMATED EVALUATION
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                            activeReport.automated_evaluation.final_status === 'PASSED'
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : activeReport.automated_evaluation.final_status === 'FLAGGED'
                              ? 'bg-amber-50 text-amber-800 border-amber-200'
                              : 'bg-rose-50 text-rose-800 border-rose-200'
                          }`}
                        >
                          {activeReport.automated_evaluation.final_status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 font-sans mt-0.5">
                        Multi-Stage Audit (6 Focused Dimensions) • Pre-Review Verification
                      </p>
                    </div>
                  </div>

                  <div className="sm:text-right shrink-0">
                    <div className="text-xl font-bold font-mono text-slate-900 tabular-nums">
                      {Math.round(activeReport.automated_evaluation.overall_score * 100)}%
                    </div>
                    <div className="text-[9px] font-mono text-slate-500 uppercase tracking-wider">
                      OVERALL AUDIT SCORE
                    </div>
                  </div>
                </div>

                {/* 6 Dimension Score Matrix */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {Object.entries(activeReport.automated_evaluation.dimensions).map(([key, dim]) => (
                    <div
                      key={key}
                      className={`p-2.5 rounded-lg border text-xs ${
                        dim.passed
                          ? 'bg-slate-50/70 border-slate-200'
                          : 'bg-rose-50/50 border-rose-200'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-mono font-semibold text-slate-700 truncate pr-1">
                          {dim.display_name}
                        </span>
                        <span
                          className={`font-mono text-[10px] font-bold ${
                            dim.passed ? 'text-emerald-700' : 'text-rose-700'
                          }`}
                        >
                          {Math.round(dim.score * 100)}%
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-500 line-clamp-2 leading-tight">
                        {dim.explanation}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Detected Issues Alert if any */}
                {activeReport.automated_evaluation.failed_checks.length > 0 && (
                  <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-amber-800 font-mono font-bold text-[10px]">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                      <span>FLAGGED CLINICAL ITEMS FOR PHYSICIAN ATTENTION:</span>
                    </div>
                    <ul className="list-disc list-inside text-slate-700 text-[11px] space-y-0.5">
                      {activeReport.automated_evaluation.fail_reasons.map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-xs text-slate-600 font-sans">
                  <ShieldAlert className="w-4 h-4 text-slate-400" />
                  <span>Independent multi-stage audit pending for this report.</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleTriggerEvaluation(activeReport.id)}
                  disabled={evaluatingReport}
                  className="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-mono font-semibold transition-colors disabled:opacity-50"
                >
                  {evaluatingReport ? 'Evaluating...' : 'Run Automated Audit'}
                </button>
              </div>
            )}

            {/* Differential Diagnosis Ranking */}
            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2.5">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-amber-600" />
                  <span className="text-[10px] font-mono font-bold text-slate-900 uppercase tracking-wider">
                    DIFFERENTIAL DIAGNOSIS RANKING
                  </span>
                </div>
                <span className="text-[10px] font-mono text-slate-500">AI PROBABILITY MATRIX</span>
              </div>

              <div className="space-y-3">
                {activeReport.differential_diagnosis.map((d, idx) => {
                  const pct = Math.round(d.likelihood * 100);
                  return (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="font-medium text-slate-800 flex items-center gap-1.5">
                          <span className="w-4 h-4 rounded bg-slate-100 border border-slate-200 text-[10px] text-slate-600 flex items-center justify-center font-bold">
                            {idx + 1}
                          </span>
                          {d.condition}
                        </span>
                        <span className="text-sky-700 font-bold tabular-nums">{pct}%</span>
                      </div>
                      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${
                            idx === 0
                              ? 'bg-sky-600'
                              : idx === 1
                              ? 'bg-amber-500'
                              : 'bg-slate-400'
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Guideline-Directed Treatment Plan */}
            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2.5">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span className="text-[10px] font-mono font-bold text-slate-900 uppercase tracking-wider">
                    GUIDELINE-DIRECTED TREATMENT REGIMEN
                  </span>
                </div>
                <span className="px-2 py-0.5 bg-emerald-50 text-emerald-800 rounded-md font-mono text-[9px] border border-emerald-200 font-semibold">
                  AHA/ACC 2023 COMPLIANT
                </span>
              </div>

              <div className="space-y-2 text-xs">
                {activeReport.treatment_plan.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-start justify-between p-3 bg-slate-50 rounded-xl border border-slate-200 gap-3"
                  >
                    <div className="flex items-start gap-2.5">
                      <span className="w-5 h-5 rounded-lg bg-sky-50 text-sky-700 border border-sky-200 font-mono text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <div className="text-slate-800 font-medium leading-relaxed font-sans">
                        {item}
                      </div>
                    </div>
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded font-mono text-[9px] border border-emerald-200 shrink-0 font-semibold">
                      {idx === 0 ? 'ADMINISTERED' : 'ORDERED'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Diagnostic Investigations Findings */}
            {activeReport.investigation_results.length > 0 && (
              <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs">
                <div className="flex items-center gap-2 mb-3 border-b border-slate-100 pb-2.5">
                  <TestTube className="w-4 h-4 text-indigo-600" />
                  <span className="text-[10px] font-mono font-bold text-slate-900 uppercase tracking-wider">
                    DIAGNOSTIC INVESTIGATIONS &amp; LAB BIOMARKERS
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {activeReport.investigation_results.map((res, i) => (
                    <div key={i} className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                      <div className="flex items-center justify-between font-semibold mb-1.5">
                        <span className="text-sky-800 font-mono text-[11px]">{res.test_type}</span>
                        <span className="text-[9px] font-mono text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 font-semibold">
                          COMPLETED
                        </span>
                      </div>
                      <p className="text-slate-700 text-[11px] leading-relaxed font-sans">{res.interpretation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Evidence RAG Citations */}
            {((activeReport.medical_knowledge_citations && activeReport.medical_knowledge_citations.length > 0) ||
              ((activeReport as any).harrison_citations && (activeReport as any).harrison_citations.length > 0)) && (
              <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs">
                <div className="flex items-center gap-2 mb-3 border-b border-slate-100 pb-2.5">
                  <BookOpen className="w-4 h-4 text-sky-600" />
                  <span className="text-[10px] font-mono font-bold text-slate-900 uppercase tracking-wider">
                    HARRISON'S 21ST EDITION VECTOR RAG EVIDENCE
                  </span>
                </div>
                <div className="space-y-2">
                  {(activeReport.medical_knowledge_citations || (activeReport as any).harrison_citations || []).map((c: any, i: number) => (
                    <div key={i} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                      <span className="font-mono text-[11px] text-sky-800 font-bold block mb-1">
                        {c.chapter || c.topic || 'Medical Grounding'}
                      </span>
                      <p className="text-slate-700 leading-relaxed font-sans italic">"{c.text || c.excerpt}"</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Physician Reinforcement Learning Alignment (RL DPO) Console */}
            <div className="p-5 rounded-xl bg-white border border-emerald-200 shadow-xs">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded-md bg-emerald-50 flex items-center justify-center text-emerald-600">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-[11px] font-mono font-bold text-slate-900 uppercase tracking-wider">
                    PHYSICIAN RL DPO ALIGNMENT
                  </span>
                </div>
                <span className="px-2 py-0.5 bg-emerald-50 text-emerald-800 rounded-md font-mono text-[9px] border border-emerald-200 font-bold">
                  MODEL VER. 4.2
                </span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed mb-4 font-sans">
                Score decision accuracy to continuously reinforce Dr. Vance's clinical judgment via Direct Preference Optimization (DPO).
              </p>

              {/* Interactive Star Reward Scoring (1-5) */}
              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 mb-3.5">
                <div className="text-[9px] font-mono text-slate-500 uppercase tracking-wider">
                  REWARD SCORING (1 TO 5 STARS)
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mt-2">
                  <div className="flex items-center gap-1.5">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setOverallScore(star)}
                        className="p-1 hover:scale-125 transition-transform duration-200 cursor-pointer focus:outline-none"
                        title={`Rate ${star} Stars`}
                      >
                        <Star
                          className={`w-6 h-6 transition-colors duration-200 ${
                            star <= overallScore
                              ? 'fill-amber-400 text-amber-500 drop-shadow-xs'
                              : 'text-slate-300 hover:text-slate-400'
                          }`}
                        />
                      </button>
                    ))}
                  </div>
                  <span className="font-mono text-xs text-slate-800 font-bold">
                    {getScoreDescription(overallScore)}
                  </span>
                </div>
              </div>

              {/* Overall Assessment Selectors */}
              <div className="mb-4">
                <label className="block text-[10px] font-mono text-slate-600 mb-1.5 uppercase tracking-wider">
                  OVERALL CLINICAL ASSESSMENT
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {REVIEW_ASSESSMENTS.map((item) => {
                    const isSelected = assessment === item.value;
                    const colorStyles =
                      item.value === 'CORRECT'
                        ? isSelected
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'bg-emerald-50/50 text-emerald-800 border-emerald-200 hover:bg-emerald-100/60'
                        : item.value === 'PARTIALLY_CORRECT'
                        ? isSelected
                          ? 'bg-amber-600 text-white border-amber-600'
                          : 'bg-amber-50/50 text-amber-800 border-amber-200 hover:bg-amber-100/60'
                        : isSelected
                        ? 'bg-rose-600 text-white border-rose-600'
                        : 'bg-rose-50/50 text-rose-800 border-rose-200 hover:bg-rose-100/60';

                    return (
                      <button
                        key={item.value}
                        type="button"
                        onClick={() => setAssessment(item.value)}
                        className={`py-2 px-3 rounded-xl border text-xs font-mono font-bold transition-all text-center cursor-pointer ${colorStyles}`}
                      >
                        {item.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Identified Clinical Error Categories (Taxonomy) */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-[10px] font-mono text-slate-600 uppercase tracking-wider">
                    IDENTIFIED CLINICAL DEFECTS &amp; ERRORS (OPTIONAL)
                  </label>
                  <span className="text-[10px] font-mono text-slate-400">
                    {identifiedErrors.length} selected
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {STRUCTURED_ERROR_TAXONOMY.map((err) => {
                    const isSelected = identifiedErrors.includes(err.code);
                    return (
                      <button
                        key={err.code}
                        type="button"
                        onClick={() => toggleErrorTag(err.code)}
                        title={err.description}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-mono transition-all border cursor-pointer ${
                          isSelected
                            ? 'bg-rose-100 text-rose-800 border-rose-300 font-bold shadow-xs'
                            : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        {isSelected ? '✓ ' : '+ '}
                        {err.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Reviewer Role & Specialty Selection */}
              <div className="grid grid-cols-2 gap-2.5 mb-4">
                <div>
                  <label className="block text-[10px] font-mono text-slate-600 mb-1">
                    REVIEWER ROLE
                  </label>
                  <select
                    value={reviewerRole}
                    onChange={(e) => setReviewerRole(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-2.5 py-1.5 text-xs text-slate-900 font-mono focus:bg-white focus:outline-none focus:border-sky-500 transition cursor-pointer"
                  >
                    <option value="ATTENDING_PHYSICIAN">Attending Physician (MD/DO)</option>
                    <option value="CLINICAL_RESIDENT">Clinical Resident</option>
                    <option value="MEDICAL_STUDENT">Medical Student</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-mono text-slate-600 mb-1">
                    DIAGNOSIS ACCURACY
                  </label>
                  <select
                    value={diagnosisGrade}
                    onChange={(e) => setDiagnosisGrade(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-2.5 py-1.5 text-xs text-slate-900 font-mono focus:bg-white focus:outline-none focus:border-sky-500 transition cursor-pointer"
                  >
                    <option value="CORRECT">Correct (High Concordance)</option>
                    <option value="PARTIALLY_CORRECT">Partially Correct</option>
                    <option value="INCORRECT">Incorrect (Missed Diagnosis)</option>
                  </select>
                </div>
              </div>

              {/* Rubric Selectors */}
              <div className="space-y-3 mb-4 text-xs">
                <div>
                  <label className="block text-[10px] font-mono text-slate-600 mb-1">
                    CLINICAL REASONING
                  </label>
                  <select
                    value={reasoningGrade}
                    onChange={(e) => setReasoningGrade(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-900 font-mono focus:bg-white focus:outline-none focus:border-sky-500 transition cursor-pointer"
                  >
                    <option value="SOUND">Sound and Evidence-based</option>
                    <option value="MISSING_CRITICAL_EVIDENCE">Missing Critical Evidence</option>
                    <option value="FAULTY_LOGIC">Faulty Logical Leap</option>
                    <option value="UNSUPPORTED_CONCLUSION">Unsupported Conclusion</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-slate-600 mb-1">
                    WORKUP &amp; LAB ORDERING
                  </label>
                  <select
                    value={testsGrade}
                    onChange={(e) => setTestsGrade(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-900 font-mono focus:bg-white focus:outline-none focus:border-sky-500 transition cursor-pointer"
                  >
                    <option value="APPROPRIATE">Appropriate and Indicated</option>
                    <option value="OVER_ORDERING">Over-ordering / Defensive</option>
                    <option value="MISSING_ESSENTIAL_TEST">Missing Essential Guideline Test</option>
                    <option value="INAPPROPRIATE_TEST">Inappropriate / Unsafe Test</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-slate-600 mb-1">
                    TREATMENT SAFETY
                  </label>
                  <select
                    value={treatmentGrade}
                    onChange={(e) => setTreatmentGrade(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-900 font-mono focus:bg-white focus:outline-none focus:border-sky-500 transition cursor-pointer"
                  >
                    <option value="SAFE_AND_OPTIMAL">Safe and Guideline-Optimal</option>
                    <option value="SUBOPTIMAL">Suboptimal Intervention</option>
                    <option value="CONTRAINDICATED_OR_HARMFUL">Contraindicated / Harmful</option>
                  </select>
                </div>

                {/* Structured Corrections Section */}
                <div className="p-3.5 bg-sky-50/50 rounded-xl border border-sky-100 space-y-2.5">
                  <div className="text-[10px] font-mono font-bold text-sky-900 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-sky-600" />
                    <span>STRUCTURED CLINICAL CORRECTIONS (OPTIONAL)</span>
                  </div>

                  <div>
                    <label className="block text-[10px] font-mono text-slate-600 mb-1">
                      CORRECTED PRIMARY DIAGNOSIS
                    </label>
                    <input
                      type="text"
                      value={correctedDiagnosis}
                      onChange={(e) => setCorrectedDiagnosis(e.target.value)}
                      placeholder="e.g. Acute Non-ST-Elevation Myocardial Infarction"
                      className="w-full bg-white border border-slate-300 rounded-xl px-3 py-1.5 text-xs text-slate-900 font-mono focus:outline-none focus:border-sky-500 transition"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-mono text-slate-600 mb-1">
                      CORRECTED CLINICAL REASONING
                    </label>
                    <textarea
                      rows={2}
                      value={correctedReasoning}
                      onChange={(e) => setCorrectedReasoning(e.target.value)}
                      placeholder="Sound physiological reasoning that supports the diagnosis..."
                      className="w-full bg-white border border-slate-300 rounded-xl p-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-sky-500 resize-none font-sans"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-mono text-slate-600 mb-1">
                      CORRECTED RECOMMENDATIONS &amp; TREATMENT (ONE PER LINE)
                    </label>
                    <textarea
                      rows={2}
                      value={correctedRecommendations}
                      onChange={(e) => setCorrectedRecommendations(e.target.value)}
                      placeholder="Aspirin 325 mg PO chewable immediately&#10;Ticagrelor 180 mg PO loading dose"
                      className="w-full bg-white border border-slate-300 rounded-xl p-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-sky-500 resize-none font-sans"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-slate-600 mb-1">
                    ATTENDING CLINICAL CRITIQUE / NOTES
                  </label>
                  <textarea
                    rows={2}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Attending feedback or training preference..."
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-sky-500 resize-none font-sans"
                  />
                </div>

                {/* Training Dataset Eligibility Live Status */}
                <div className={`p-2.5 rounded-xl border flex items-center justify-between text-xs font-mono ${
                  assessment === 'CORRECT' || correctedDiagnosis.trim() || correctedReasoning.trim() || correctedRecommendations.trim() || notes.trim().length >= 15
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-amber-50 border-amber-200 text-amber-800'
                }`}>
                  <div className="flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5" />
                    <span className="font-bold text-[10px]">
                      DATASET STATUS: {
                        assessment === 'CORRECT' || correctedDiagnosis.trim() || correctedReasoning.trim() || correctedRecommendations.trim() || notes.trim().length >= 15
                          ? 'ELIGIBLE FOR TRAINING RECORD'
                          : 'INCOMPLETE (CORRECTION NEEDED)'
                      }
                    </span>
                  </div>
                  <span className="text-[9px] opacity-80">
                    {assessment === 'CORRECT' ? 'Approved Gold Standard' : 'Requires correction to enter dataset'}
                  </span>
                </div>
              </div>

              {/* Verdict Buttons */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <button
                  disabled={isSubmitting}
                  onClick={() => handleReviewAction(true)}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white py-3 px-4 rounded-xl font-mono text-xs font-bold tracking-wider active:scale-[0.98] transition-all flex items-center justify-between cursor-pointer shadow-xs disabled:opacity-50"
                >
                  <span>APPROVE VERDICT</span>
                  <div className="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center">
                    <ThumbsUp className="w-3.5 h-3.5 text-white" />
                  </div>
                </button>

                <button
                  disabled={isSubmitting}
                  onClick={() => handleReviewAction(false)}
                  className="bg-slate-100 hover:bg-rose-50 text-slate-700 hover:text-rose-700 border border-slate-300 hover:border-rose-300 py-3 px-4 rounded-xl font-mono text-xs font-bold tracking-wider active:scale-[0.98] transition-all flex items-center justify-between cursor-pointer disabled:opacity-50"
                >
                  <span>REJECT / FLAG</span>
                  <div className="w-6 h-6 rounded-lg bg-slate-200 flex items-center justify-center">
                    <ThumbsDown className="w-3.5 h-3.5 text-slate-600" />
                  </div>
                </button>
              </div>

              <div className="text-center pt-3">
                <span className="text-[10px] text-slate-400 font-mono">
                  DPO preference pair logged securely to hospital telemetry ledger.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PhysicianReviewDashboard;
