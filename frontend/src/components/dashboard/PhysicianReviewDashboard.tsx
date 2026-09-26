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
  Activity,
  HeartPulse,
  Thermometer,
  User
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
      setTimeout(() => setSubmittedReviewSuccess(false), 3500);
    } catch (err) {
      console.error('Failed to submit review:', err);
    }
  };

  if (reports.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-slate-400 bg-slate-950 telemetry-grid">
        <div className="relative rounded-2xl p-1 bg-gradient-to-b from-slate-800/80 to-slate-900/60 border border-slate-700/60 shadow-2xl mb-4">
          <div className="w-16 h-16 rounded-[calc(1rem-2px)] bg-slate-950 flex items-center justify-center text-sky-400">
            <FileText className="w-8 h-8" />
          </div>
        </div>
        <h3 className="text-sm font-mono font-bold text-slate-200 uppercase tracking-widest">
          NO CLINICAL REPORTS PENDING REVIEW
        </h3>
        <p className="text-xs max-w-md text-center mt-2 text-slate-400 font-sans leading-relaxed">
          Simulate an encounter pathway to generate autonomous Clinical AI reports grounded with Harrison's 21st Edition evidence.
        </p>
      </div>
    );
  }

  const confidencePct = Math.round((activeReport?.diagnostic_confidence || 0.92) * 100);

  return (
    <div className="flex-1 flex flex-col md:flex-row overflow-hidden bg-slate-950 text-slate-200 telemetry-grid">
      {/* ═══════════════════════════════════════════════════════════════════
          SIDEBAR: CLINICAL REPORT QUEUE
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="w-full md:w-80 border-b md:border-b-0 md:border-r border-slate-800/90 bg-slate-950/90 flex flex-col shrink-0 backdrop-blur-xl">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <Stethoscope className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-xs font-mono font-bold tracking-wider text-slate-100 uppercase">
                CLINICAL QUEUE
              </h2>
              <span className="text-[10px] font-mono text-slate-500">Autonomous Encounters</span>
            </div>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-sky-950/80 text-sky-300 border border-sky-700/60 font-semibold shadow-inner">
            {reports.length} READY
          </span>
        </div>

        {/* Report Cards Scroll Area */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2.5 max-h-60 md:max-h-none">
          {reports.map((rep) => {
            const isSelected = rep.id === activeReport?.id;
            return (
              <div
                key={rep.id}
                onClick={() => setSelectedReportId(rep.id)}
                className={`relative rounded-xl p-0.5 transition-all duration-200 cursor-pointer ${
                  isSelected
                    ? 'bg-gradient-to-r from-sky-500/50 via-sky-400/30 to-emerald-500/40 shadow-lg shadow-sky-500/10'
                    : 'bg-slate-800/40 hover:bg-slate-800/70 border border-slate-800/60'
                }`}
              >
                <div
                  className={`p-3 rounded-[calc(0.75rem-1px)] transition-all ${
                    isSelected
                      ? 'bg-slate-900/95 text-white'
                      : 'bg-slate-950/80 hover:bg-slate-900/50 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="font-bold text-sky-400 font-mono text-[11px] tracking-wide">
                      {rep.id}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {new Date(rep.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  <div className="font-semibold text-xs text-slate-100 flex items-center gap-1.5 truncate">
                    <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">{rep.patient_name}</span>
                  </div>

                  <div className="text-[11px] text-slate-400 truncate mt-1 pl-5">
                    Dx: <span className="text-slate-200 font-medium">{rep.primary_diagnosis}</span>
                  </div>

                  <div className="mt-2.5 pt-2 border-t border-slate-800/70 flex items-center justify-between text-[10px] font-mono">
                    <span className="px-2 py-0.5 rounded-md bg-emerald-950/70 border border-emerald-800/60 text-emerald-400 font-semibold tabular-nums">
                      {Math.round(rep.diagnostic_confidence * 100)}% CONF
                    </span>
                    <span className="text-emerald-400 flex items-center gap-1 text-[10px]">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      VERIFIED
                    </span>
                  </div>
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
          {/* Top Alert Banner: Medication Safety (Machined Double-Bezel) */}
          {!dismissAlert && (
            <div className="relative rounded-xl p-0.5 bg-gradient-to-r from-rose-500/40 via-rose-600/20 to-slate-800/50 shadow-md">
              <div className="p-3.5 rounded-[calc(0.75rem-1px)] bg-slate-950/90 flex flex-col sm:flex-row sm:items-center justify-between gap-3 backdrop-blur-md">
                <div className="flex items-start sm:items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-center shrink-0">
                    <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse" />
                  </div>
                  <div>
                    <div className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wide flex items-center gap-2">
                      <span>MEDICATION SAFETY &amp; CONTRAINDICATION ALERT</span>
                      <span className="px-1.5 py-0.2 bg-rose-950 text-rose-300 rounded text-[9px] border border-rose-800 font-bold">
                        LEVEL 1 CRITICAL
                      </span>
                    </div>
                    <div className="text-xs text-slate-300 mt-0.5 leading-relaxed font-sans">
                      NSAIDs contraindicated for Patient {activeReport.patient_name} due to acute renal baseline fluctuation and active antiplatelet or anticoagulant regimen.
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setDismissAlert(true)}
                  className="self-end sm:self-center px-3 py-1 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 font-mono text-[10px] rounded border border-slate-700/80 transition cursor-pointer shrink-0"
                >
                  Dismiss Alert
                </button>
              </div>
            </div>
          )}

          {/* Success Banner */}
          {submittedReviewSuccess && (
            <div className="p-3.5 rounded-xl bg-emerald-950/80 border border-emerald-600/80 text-emerald-300 text-xs font-mono flex items-center gap-2.5 shadow-lg shadow-emerald-500/10 animate-in fade-in duration-300">
              <div className="w-6 h-6 rounded-full bg-emerald-500/20 border border-emerald-400/40 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <span className="leading-relaxed">
                Attending physician verdict recorded securely to Hospital Telemetry Ledger and RL DPO preference dataset.
              </span>
            </div>
          )}

          {/* Patient Overview Card (Double-Bezel) */}
          <div className="relative rounded-2xl p-0.5 bg-gradient-to-r from-slate-800/80 via-slate-800/40 to-slate-800/80 border border-slate-700/50 shadow-xl">
            <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 font-bold font-mono text-sm">
                  {activeReport.patient_name.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-base font-bold text-slate-100 font-sans tracking-tight">
                      {activeReport.patient_name}
                    </h1>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-900 border border-slate-700 text-slate-300">
                      {activeReport.patient_age}y / {activeReport.patient_sex}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-3 font-mono">
                    <span>ENCOUNTER: <strong className="text-sky-400">{activeReport.encounter_id}</strong></span>
                    <span>PATIENT ID: <strong className="text-slate-300">{activeReport.patient_id}</strong></span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-lg text-xs font-mono bg-sky-950/80 text-sky-300 border border-sky-800/70 font-medium">
                  CHIEF COMPLAINT: {activeReport.chief_complaint}
                </span>
                <span className="px-2.5 py-1 rounded-lg text-xs font-mono bg-emerald-950/80 text-emerald-300 border border-emerald-800/70 font-medium">
                  DISPOSITION: {activeReport.recommended_disposition || 'CARDIOLOGY ADMISSION'}
                </span>
              </div>
            </div>
          </div>

          {/* Main Asymmetrical Bento Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* ═══════════════════════════════════════════════════════════════
                LEFT COLUMN: DIAGNOSIS & CLINICAL GUIDELINES (7 COLS)
                ═══════════════════════════════════════════════════════════════ */}
            <div className="lg:col-span-7 space-y-4">
              {/* Primary Diagnosis Card (Double-Bezel Hero) */}
              <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-sky-500/30 via-slate-800/40 to-slate-900/60 border border-sky-500/40 shadow-2xl">
                <div className="p-5 rounded-[calc(1rem-2px)] bg-slate-950/95 backdrop-blur-md">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 rounded-md bg-sky-500/20 flex items-center justify-center text-sky-400">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-[11px] font-mono text-sky-400 uppercase font-bold tracking-wider">
                        PRIMARY CLINICAL DIAGNOSIS
                      </span>
                    </div>
                    <span className="px-2 py-0.5 bg-emerald-950 text-emerald-400 border border-emerald-800/80 rounded-md font-mono text-[10px] font-bold">
                      ICD-10: I21.4
                    </span>
                  </div>

                  <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-4">
                    <div className="flex-1">
                      <h2 className="text-xl font-bold text-slate-100 font-sans tracking-tight">
                        {activeReport.primary_diagnosis}
                      </h2>
                      <p className="text-xs text-slate-300 mt-2 leading-relaxed font-sans">
                        {activeReport.clinical_reasoning || "Evaluated via serial biomarker surveillance, hemodynamic stability metrics, and Harrison's Principles of Internal Medicine criteria."}
                      </p>
                    </div>
                    <div className="sm:text-right shrink-0 bg-slate-900/60 p-3 rounded-xl border border-slate-800/80">
                      <div className="text-2xl font-bold font-mono text-emerald-400 tabular-nums">
                        {confidencePct}%
                      </div>
                      <div className="text-[9px] font-mono text-slate-400 uppercase tracking-wider">
                        DIAGNOSTIC CONFIDENCE
                      </div>
                    </div>
                  </div>

                  {/* Key Clinical Biomarker Tiles */}
                  <div className="pt-4 mt-4 border-t border-slate-800/80 grid grid-cols-3 gap-2.5 text-center">
                    <div className="bg-slate-900/70 p-2.5 rounded-xl border border-slate-800/80">
                      <div className="text-[9px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-center gap-1">
                        <HeartPulse className="w-3 h-3 text-emerald-400" />
                        HEART RATE
                      </div>
                      <div className="text-sm font-bold font-mono text-emerald-400 mt-1 tabular-nums">
                        {activeReport.vital_signs.heart_rate} BPM
                      </div>
                    </div>
                    <div className="bg-slate-900/70 p-2.5 rounded-xl border border-slate-800/80">
                      <div className="text-[9px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-center gap-1">
                        <Activity className="w-3 h-3 text-sky-400" />
                        BLOOD PRESSURE
                      </div>
                      <div className="text-sm font-bold font-mono text-sky-400 mt-1 tabular-nums">
                        {activeReport.vital_signs.systolic_bp}/{activeReport.vital_signs.diastolic_bp}
                      </div>
                    </div>
                    <div className="bg-slate-900/70 p-2.5 rounded-xl border border-slate-800/80">
                      <div className="text-[9px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-center gap-1">
                        <Thermometer className="w-3 h-3 text-slate-300" />
                        O2 SATURATION
                      </div>
                      <div className="text-sm font-bold font-mono text-slate-200 mt-1 tabular-nums">
                        {activeReport.vital_signs.spo2_percent}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Differential Diagnosis Ranking (Double-Bezel) */}
              <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-slate-800/60 to-slate-900/40 border border-slate-700/50 shadow-xl">
                <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Activity className="w-4 h-4 text-amber-400" />
                      <span className="text-[10px] font-mono font-bold text-slate-200 uppercase tracking-wider">
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
                            <span className="font-medium text-slate-300 flex items-center gap-1.5">
                              <span className="w-4 h-4 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-400 flex items-center justify-center">
                                {idx + 1}
                              </span>
                              {d.condition}
                            </span>
                            <span className="text-sky-400 font-bold tabular-nums">{pct}%</span>
                          </div>
                          <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                            <div
                              className={`h-full rounded-full transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] ${
                                idx === 0
                                  ? 'bg-gradient-to-r from-sky-500 to-sky-400'
                                  : idx === 1
                                  ? 'bg-gradient-to-r from-amber-500 to-amber-400'
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
              </div>

              {/* Guideline-Directed Treatment Plan Checklist (Double-Bezel) */}
              <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-slate-800/60 to-slate-900/40 border border-slate-700/50 shadow-xl">
                <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span className="text-[10px] font-mono font-bold text-slate-200 uppercase tracking-wider">
                        GUIDELINE-DIRECTED TREATMENT REGIMEN
                      </span>
                    </div>
                    <span className="px-2 py-0.5 bg-emerald-950 text-emerald-400 rounded-md font-mono text-[9px] border border-emerald-800 font-semibold">
                      AHA/ACC 2023 COMPLIANT
                    </span>
                  </div>

                  <div className="space-y-2 text-xs">
                    {activeReport.treatment_plan.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-start justify-between p-3 bg-slate-900/60 rounded-xl border border-slate-800/80 gap-3 hover:border-slate-700 transition"
                      >
                        <div className="flex items-start gap-2.5">
                          <span className="w-5 h-5 rounded-lg bg-sky-950 text-sky-400 border border-sky-800 font-mono text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                            {idx + 1}
                          </span>
                          <div className="text-slate-200 font-medium leading-relaxed font-sans">
                            {item}
                          </div>
                        </div>
                        <span className="px-2 py-0.5 bg-emerald-950/80 text-emerald-400 rounded font-mono text-[9px] border border-emerald-800/80 shrink-0 font-semibold">
                          {idx === 0 ? 'ADMINISTERED' : 'ORDERED'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Diagnostic Investigations Findings (Double-Bezel) */}
              {activeReport.investigation_results.length > 0 && (
                <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-slate-800/60 to-slate-900/40 border border-slate-700/50 shadow-xl">
                  <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
                    <div className="flex items-center gap-2 mb-3">
                      <TestTube className="w-4 h-4 text-indigo-400" />
                      <span className="text-[10px] font-mono font-bold text-slate-200 uppercase tracking-wider">
                        DIAGNOSTIC INVESTIGATIONS &amp; LAB BIOMARKERS
                      </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                      {activeReport.investigation_results.map((res, i) => (
                        <div key={i} className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 text-xs">
                          <div className="flex items-center justify-between font-semibold mb-1.5">
                            <span className="text-sky-300 font-mono text-[11px]">{res.test_type}</span>
                            <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-1.5 py-0.5 rounded border border-emerald-800 font-semibold">
                              COMPLETED
                            </span>
                          </div>
                          <p className="text-slate-300 text-[11px] leading-relaxed font-sans">{res.interpretation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* ═══════════════════════════════════════════════════════════════
                RIGHT COLUMN: HARRISON'S CITATIONS & RL DPO ALIGNMENT (5 COLS)
                ═══════════════════════════════════════════════════════════════ */}
            <div className="lg:col-span-5 space-y-4">
              {/* Harrison's 21st Edition Evidence Citation Cards (Double-Bezel) */}
              <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-slate-800/60 to-slate-900/40 border border-slate-700/50 shadow-xl">
                <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-sky-400" />
                      <span className="text-[10px] font-mono font-bold text-slate-200 uppercase tracking-wider">
                        HARRISON'S 21ST EDITION EVIDENCE
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-500">47,806 RAG STORE</span>
                  </div>

                  <div className="space-y-3">
                    {activeReport.medical_knowledge_citations.length > 0 ? (
                      activeReport.medical_knowledge_citations.map((c, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-900/70 p-3.5 rounded-xl border-l-2 border-sky-400 border border-slate-800 space-y-2"
                        >
                          <div className="flex items-center justify-between text-[11px] font-mono text-sky-400">
                            <span className="font-bold truncate max-w-[200px]">{c.chapter}</span>
                            <span className="text-slate-500">Page {c.page}</span>
                          </div>
                          <p className="text-xs text-slate-300 italic leading-relaxed font-sans">
                            "{c.text.slice(0, 240)}..."
                          </p>
                          <div className="flex gap-2 pt-1">
                            <span className="px-2 py-0.5 bg-slate-950 text-slate-400 rounded-md text-[9px] font-mono border border-slate-800">
                              Class I Recommendation
                            </span>
                            <span className="px-2 py-0.5 bg-slate-950 text-emerald-400 rounded-md text-[9px] font-mono border border-slate-800">
                              Level A Evidence
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="bg-slate-900/70 p-3.5 rounded-xl border-l-2 border-sky-400 border border-slate-800 space-y-2">
                        <div className="flex items-center justify-between text-[11px] font-mono text-sky-400">
                          <span className="font-bold">CHAPTER 266: ST-Segment Elevation MI</span>
                          <span className="text-slate-500">Page 2041</span>
                        </div>
                        <p className="text-xs text-slate-300 italic leading-relaxed font-sans">
                          "Early invasive strategy with coronary angiography and revascularization is indicated for high-risk clinical features with ongoing biomarker elevation."
                        </p>
                        <div className="flex gap-2 pt-1">
                          <span className="px-2 py-0.5 bg-slate-950 text-slate-400 rounded-md text-[9px] font-mono border border-slate-800">
                            Class I Recommendation
                          </span>
                          <span className="px-2 py-0.5 bg-slate-950 text-emerald-400 rounded-md text-[9px] font-mono border border-slate-800">
                            Level A Evidence
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Physician Reinforcement Learning Alignment (RL DPO) (Double-Bezel Console) */}
              <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-emerald-500/30 via-slate-800/40 to-slate-900/60 border border-emerald-500/40 shadow-2xl">
                <div className="p-5 rounded-[calc(1rem-2px)] bg-slate-950/95 backdrop-blur-md">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 rounded-md bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                        <Sparkles className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-[11px] font-mono font-bold text-slate-200 uppercase tracking-wider">
                        PHYSICIAN RL DPO ALIGNMENT
                      </span>
                    </div>
                    <span className="px-2 py-0.5 bg-emerald-950 text-emerald-400 rounded-md font-mono text-[9px] border border-emerald-800 font-bold">
                      MODEL VER. 4.2
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed mb-4 font-sans">
                    Score decision accuracy to continuously reinforce Dr. Vance's clinical judgment via Direct Preference Optimization (DPO).
                  </p>

                  {/* Interactive Star Reward Scoring (1-5) */}
                  <div className="bg-slate-900/70 p-3.5 rounded-xl border border-slate-800/80 mb-3.5">
                    <div className="text-[9px] font-mono text-slate-400 uppercase tracking-wider">
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
                                  ? 'fill-amber-400 text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]'
                                  : 'text-slate-700 hover:text-slate-500'
                              }`}
                            />
                          </button>
                        ))}
                      </div>
                      <span className="font-mono text-xs text-slate-200 font-bold">
                        {getScoreDescription(overallScore)}
                      </span>
                    </div>
                  </div>

                  {/* Rubric Selectors */}
                  <div className="space-y-3 mb-4 text-xs">
                    <div>
                      <label className="block text-[10px] font-mono text-slate-400 mb-1">
                        DIAGNOSIS ACCURACY
                      </label>
                      <select
                        value={diagnosisGrade}
                        onChange={(e) => setDiagnosisGrade(e.target.value)}
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500 transition"
                      >
                        <option value="CORRECT">Correct (High Concordance)</option>
                        <option value="PARTIALLY_CORRECT">Partially Correct</option>
                        <option value="INCORRECT">Incorrect (Missed Diagnosis)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[10px] font-mono text-slate-400 mb-1">
                        CLINICAL REASONING
                      </label>
                      <select
                        value={reasoningGrade}
                        onChange={(e) => setReasoningGrade(e.target.value)}
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500 transition"
                      >
                        <option value="SOUND">Sound and Evidence-based</option>
                        <option value="MISSING_CRITICAL_EVIDENCE">Missing Critical Evidence</option>
                        <option value="FAULTY_LOGIC">Faulty Logical Leap</option>
                        <option value="UNSUPPORTED_CONCLUSION">Unsupported Conclusion</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[10px] font-mono text-slate-400 mb-1">
                        WORKUP &amp; LAB ORDERING
                      </label>
                      <select
                        value={testsGrade}
                        onChange={(e) => setTestsGrade(e.target.value)}
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500 transition"
                      >
                        <option value="APPROPRIATE">Appropriate and Indicated</option>
                        <option value="OVER_ORDERING">Over-ordering / Defensive</option>
                        <option value="MISSING_ESSENTIAL_TEST">Missing Essential Guideline Test</option>
                        <option value="INAPPROPRIATE_TEST">Inappropriate / Unsafe Test</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[10px] font-mono text-slate-400 mb-1">
                        TREATMENT SAFETY
                      </label>
                      <select
                        value={treatmentGrade}
                        onChange={(e) => setTreatmentGrade(e.target.value)}
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500 transition"
                      >
                        <option value="SAFE_AND_OPTIMAL">Safe and Guideline-Optimal</option>
                        <option value="SUBOPTIMAL">Suboptimal Intervention</option>
                        <option value="CONTRAINDICATED_OR_HARMFUL">Contraindicated / Harmful</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[10px] font-mono text-slate-400 mb-1">
                        CORRECTED DIAGNOSIS (IF REVISED)
                      </label>
                      <input
                        type="text"
                        value={correctedDiagnosis}
                        onChange={(e) => setCorrectedDiagnosis(e.target.value)}
                        placeholder="Refined clinical diagnosis (optional)..."
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-mono text-slate-400 mb-1">
                        ATTENDING CLINICAL CRITIQUE / NOTES
                      </label>
                      <textarea
                        rows={2}
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Attending feedback or training preference..."
                        className="w-full bg-slate-900/90 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500 resize-none font-sans"
                      />
                    </div>
                  </div>

                  {/* Verdict Buttons (Button-in-Button Nested Architecture) */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <button
                      disabled={isSubmitting}
                      onClick={() => handleReviewAction(true)}
                      className="group relative bg-emerald-500 hover:bg-emerald-400 text-slate-950 py-3 px-4 rounded-xl font-mono text-xs font-bold tracking-wider active:scale-[0.98] transition-all flex items-center justify-between cursor-pointer shadow-lg shadow-emerald-500/20 disabled:opacity-50"
                    >
                      <span>APPROVE VERDICT</span>
                      <div className="w-6 h-6 rounded-lg bg-slate-950/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <ThumbsUp className="w-3.5 h-3.5 text-slate-950" />
                      </div>
                    </button>

                    <button
                      disabled={isSubmitting}
                      onClick={() => handleReviewAction(false)}
                      className="group relative bg-slate-900 hover:bg-rose-950/80 text-slate-300 hover:text-rose-200 border border-slate-800 hover:border-rose-800/80 py-3 px-4 rounded-xl font-mono text-xs font-bold tracking-wider active:scale-[0.98] transition-all flex items-center justify-between cursor-pointer disabled:opacity-50"
                    >
                      <span>REJECT / FLAG</span>
                      <div className="w-6 h-6 rounded-lg bg-slate-800/80 group-hover:bg-rose-900/60 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <ThumbsDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-rose-200" />
                      </div>
                    </button>
                  </div>

                  <div className="text-center pt-3">
                    <span className="text-[10px] text-slate-500 font-mono">
                      DPO preference pair logged securely to hospital telemetry ledger.
                    </span>
                  </div>
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
