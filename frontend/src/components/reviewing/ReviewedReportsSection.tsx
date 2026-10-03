import React, { useState, useEffect, useCallback } from 'react';
import {
  FileCheck2,
  CheckCircle2,
  XCircle,
  Star,
  Search,
  User,
  Stethoscope,
  RefreshCw,
  Cpu,
  Play,
  AlertTriangle,
  FileText,
} from 'lucide-react';
import type { ClinicalReport } from '../../types';

export interface ReviewedReportItem {
  id: string;
  report_id: string;
  encounter_id: string;
  physician_name: string;
  reviewed_at: string;
  diagnosis_grade: string;
  reasoning_grade: string;
  tests_grade: string;
  treatment_grade: string;
  overall_score: number;
  approved: boolean;
  notes: string;
  corrected_diagnosis?: string;
  corrected_treatment?: string[];
  report: ClinicalReport;
}

interface ReviewedReportsSectionProps {
  onTriggerTrainingSuccess?: () => void;
}

export const ReviewedReportsSection: React.FC<ReviewedReportsSectionProps> = ({
  onTriggerTrainingSuccess,
}) => {
  const [reviewedItems, setReviewedItems] = useState<ReviewedReportItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [approvalFilter, setApprovalFilter] = useState<'ALL' | 'APPROVED' | 'REJECTED'>('ALL');
  const [scoreFilter, setScoreFilter] = useState<'ALL' | '5' | '4' | '3_OR_LESS'>('ALL');

  // Manual Training Modal / State
  const [isTrainingModalOpen, setIsTrainingModalOpen] = useState<boolean>(false);
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [trainingStatus, setTrainingStatus] = useState<string | null>(null);
  const [trainingResult, setTrainingResult] = useState<any>(null);
  const [trainingError, setTrainingError] = useState<string | null>(null);
  const [epochs, setEpochs] = useState<number>(4);
  const [learningRate, setLearningRate] = useState<number>(0.0002);
  const [useDryRun, setUseDryRun] = useState<boolean>(false);

  const fetchReviewedReports = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/reports/reviewed');
      if (res.ok) {
        const data = await res.json();
        setReviewedItems(data || []);
        if (data && data.length > 0) {
          setSelectedId((prev) => prev || (data[0]?.id ?? null));
        }
      }
    } catch (err) {
      console.error('Failed to load reviewed reports:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReviewedReports();
  }, [fetchReviewedReports]);

  const handleManualTrain = async () => {
    setIsTraining(true);
    setTrainingStatus('Compiling verified doctor feedback and DPO pairs...');
    setTrainingError(null);
    setTrainingResult(null);

    try {
      const res = await fetch('/api/rl/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          epochs,
          learning_rate: learningRate,
          dry_run: useDryRun,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Training failed' }));
        if (res.status === 503) {
          throw new Error(
            'Training temporarily disabled until Phase 5 data hygiene is complete (HTTP 503). Your reviews are saved — nothing is lost.'
          );
        }
        throw new Error(errorData.detail || 'Fine-tuning execution failed.');
      }

      const result = await res.json();
      setTrainingResult(result);
      setTrainingStatus(`Model fine-tuning completed successfully! Adapter saved to ${result.adapter_path || 'models/medgemma-dpo-lora'}`);
      if (onTriggerTrainingSuccess) {
        onTriggerTrainingSuccess();
      }
    } catch (err: any) {
      console.error('Manual fine-tuning error:', err);
      setTrainingError(err.message || 'Fine-tuning process encountered an error.');
      setTrainingStatus(null);
    } finally {
      setIsTraining(false);
    }
  };

  const filteredItems = reviewedItems.filter((item) => {
    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const patientMatch = item.report.patient_name?.toLowerCase().includes(q);
      const diagnosisMatch = item.report.primary_diagnosis?.toLowerCase().includes(q);
      const docMatch = item.physician_name?.toLowerCase().includes(q);
      const idMatch = item.report_id?.toLowerCase().includes(q) || item.id?.toLowerCase().includes(q);
      if (!patientMatch && !diagnosisMatch && !docMatch && !idMatch) {
        return false;
      }
    }

    // Approval filter
    if (approvalFilter === 'APPROVED' && !item.approved) return false;
    if (approvalFilter === 'REJECTED' && item.approved) return false;

    // Score filter
    if (scoreFilter === '5' && item.overall_score !== 5) return false;
    if (scoreFilter === '4' && item.overall_score !== 4) return false;
    if (scoreFilter === '3_OR_LESS' && item.overall_score > 3) return false;

    return true;
  });

  const activeItem = reviewedItems.find((item) => item.id === selectedId) || filteredItems[0] || null;

  // Aggregate stats
  const totalReviewed = reviewedItems.length;
  const approvedCount = reviewedItems.filter((i) => i.approved).length;
  const approvalRate = totalReviewed > 0 ? Math.round((approvedCount / totalReviewed) * 100) : 0;
  const avgScore =
    totalReviewed > 0
      ? (reviewedItems.reduce((acc, i) => acc + (i.overall_score || 0), 0) / totalReviewed).toFixed(1)
      : '0.0';

  return (
    <div className="flex-1 flex flex-col bg-[#f8fafc] overflow-hidden text-slate-800 telemetry-grid">
      {/* Top Header Bar */}
      <div className="px-6 py-4 border-b border-slate-200 bg-white/90 backdrop-blur-md flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0 shadow-xs">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 shadow-xs">
              <FileCheck2 className="w-4 h-4 text-emerald-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-slate-900 font-sans uppercase tracking-wide">
                  Reviewing Archive &amp; Doctor Evaluations
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {totalReviewed} EVALUATED CASES
                </span>
              </div>
              <p className="text-xs text-slate-500 font-sans mt-0.5">
                Central archive of all clinical reports evaluated and signed by attending physicians. Ground truth for MedGemma RL fine-tuning.
              </p>
            </div>
          </div>
        </div>

        {/* Header Action: Manual Fine-Tuning Trigger */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsTrainingModalOpen(true)}
            className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-mono font-bold shadow-sm shadow-purple-500/20 flex items-center gap-2 transition cursor-pointer active:scale-[0.98]"
            title="Open Manual Fine-Tuning Console"
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>MANUAL MODEL TRAINING</span>
          </button>

          <button
            onClick={fetchReviewedReports}
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-200 transition cursor-pointer"
            title="Refresh Reviewed Cases"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Summary KPI Cards Bar */}
      <div className="px-6 py-3 bg-white border-b border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 shrink-0">
        <div className="px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-3 shadow-2xs">
          <div className="w-8 h-8 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center font-bold font-mono">
            {totalReviewed}
          </div>
          <div>
            <p className="text-[10px] font-mono text-slate-500 uppercase font-bold">Total Evaluated</p>
            <p className="text-xs font-bold text-slate-800">Doctor Reviews</p>
          </div>
        </div>

        <div className="px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-3 shadow-2xs">
          <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold font-mono">
            {approvalRate}%
          </div>
          <div>
            <p className="text-[10px] font-mono text-slate-500 uppercase font-bold">Approval Rate</p>
            <p className="text-xs font-bold text-slate-800">{approvedCount} of {totalReviewed} Approved</p>
          </div>
        </div>

        <div className="px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-3 shadow-2xs">
          <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center font-bold font-mono">
            {avgScore}
          </div>
          <div>
            <p className="text-[10px] font-mono text-slate-500 uppercase font-bold">Avg Physician Score</p>
            <div className="flex items-center text-amber-500">
              {[1, 2, 3, 4, 5].map((s) => (
                <Star
                  key={s}
                  className={`w-2.5 h-2.5 ${
                    s <= Math.round(Number(avgScore)) ? 'fill-amber-400 text-amber-400' : 'text-slate-300'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="px-4 py-2.5 rounded-xl bg-purple-50/70 border border-purple-200 flex items-center gap-3 shadow-2xs">
          <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center">
            <Cpu className="w-4 h-4 text-purple-700" />
          </div>
          <div>
            <p className="text-[10px] font-mono text-purple-700 uppercase font-bold">Training Policy</p>
            <p className="text-xs font-bold text-slate-800">Strictly Manual Only</p>
          </div>
        </div>
      </div>

      {/* Main Content: Filter Bar & Master-Detail View */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Left Column: Filter & Case List (Master) */}
        <div className="w-full md:w-96 border-r border-slate-200 bg-white flex flex-col shrink-0 overflow-hidden">
          {/* Search & Filters */}
          <div className="p-3 border-b border-slate-200 space-y-2 bg-slate-50/60">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search patient, diagnosis, doctor..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-sans placeholder-slate-400 focus:outline-none focus:border-sky-400"
              />
            </div>

            <div className="flex flex-col gap-1.5 text-[11px] font-mono">
              <div className="flex items-center gap-1.5">
                <span className="text-slate-400 text-[10px] uppercase font-bold w-12">Status:</span>
                {(['ALL', 'APPROVED', 'REJECTED'] as const).map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setApprovalFilter(filter)}
                    className={`px-2 py-0.5 rounded text-[10px] font-medium transition cursor-pointer ${
                      approvalFilter === filter
                        ? 'bg-sky-600 text-white font-bold'
                        : 'bg-slate-200/70 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {filter}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-1.5">
                <span className="text-slate-400 text-[10px] uppercase font-bold w-12">Score:</span>
                {(['ALL', '5', '4', '3_OR_LESS'] as const).map((sc) => (
                  <button
                    key={sc}
                    onClick={() => setScoreFilter(sc)}
                    className={`px-1.5 py-0.5 rounded text-[10px] font-medium transition cursor-pointer ${
                      scoreFilter === sc
                        ? 'bg-amber-500 text-white font-bold'
                        : 'bg-slate-200/70 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {sc === 'ALL' ? 'All' : sc === '3_OR_LESS' ? '≤3★' : `${sc}★`}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* List of Reviewed Cases */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {filteredItems.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                <FileText className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <p className="text-xs font-mono font-medium">No reviewed cases found</p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Reports reviewed by attending physicians will appear here automatically.
                </p>
              </div>
            ) : (
              filteredItems.map((item) => {
                const isSelected = activeItem?.id === item.id;
                return (
                  <div
                    key={item.id}
                    onClick={() => setSelectedId(item.id)}
                    className={`p-3.5 cursor-pointer transition flex flex-col gap-1.5 border-l-3 ${
                      isSelected
                        ? 'bg-sky-50/70 border-sky-600'
                        : 'hover:bg-slate-50 border-transparent'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 font-sans truncate">
                        {item.report.patient_name || 'Patient'}
                      </span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-bold uppercase ${
                          item.approved
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {item.approved ? 'Approved' : 'Revision Req.'}
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-600 truncate font-sans">
                      Dx: <span className="font-medium text-slate-800">{item.report.primary_diagnosis}</span>
                    </p>

                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-0.5">
                      <span className="flex items-center gap-1 text-slate-500">
                        <User className="w-3 h-3 text-slate-400" />
                        {item.physician_name || 'Attending Physician'}
                      </span>
                      <div className="flex items-center gap-1 text-amber-600 font-bold">
                        <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                        <span>{item.overall_score}/5</span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Case Evaluation Detail (Detail) */}
        <div className="flex-1 overflow-y-auto p-5 md:p-6 space-y-5 bg-[#f8fafc]">
          {activeItem ? (
            <>
              {/* Doctor Review Card */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-emerald-50/40 via-white to-sky-50/30 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                      activeItem.approved ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                    }`}>
                      {activeItem.approved ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-sm font-bold text-slate-900 font-sans">
                          Attending Physician Evaluation Report
                        </h2>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                          activeItem.approved ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}>
                          {activeItem.approved ? 'CLINICALLY APPROVED' : 'REVISION REQUIRED'}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                        Reviewed by {activeItem.physician_name} • {new Date(activeItem.reviewed_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1 bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200 text-amber-800 font-mono font-bold text-xs">
                    <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                    <span>{activeItem.overall_score}.0 / 5.0 Rating</span>
                  </div>
                </div>

                {/* 4-Axis Clinical Rubric Grades */}
                <div className="p-5 border-b border-slate-100 grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <p className="text-[10px] font-mono text-slate-500 uppercase font-bold">Diagnosis Grade</p>
                    <p className="text-xs font-bold text-slate-900 font-mono mt-0.5">{activeItem.diagnosis_grade}</p>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <p className="text-[10px] font-mono text-slate-500 uppercase font-bold">Reasoning Grade</p>
                    <p className="text-xs font-bold text-slate-900 font-mono mt-0.5">{activeItem.reasoning_grade}</p>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <p className="text-[10px] font-mono text-slate-500 uppercase font-bold">Workup &amp; Tests</p>
                    <p className="text-xs font-bold text-slate-900 font-mono mt-0.5">{activeItem.tests_grade}</p>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <p className="text-[10px] font-mono text-slate-500 uppercase font-bold">Treatment Safety</p>
                    <p className="text-xs font-bold text-slate-900 font-mono mt-0.5">{activeItem.treatment_grade}</p>
                  </div>
                </div>

                {/* Doctor Clinical Feedback Notes */}
                <div className="p-5 bg-slate-50/50 space-y-3">
                  <div>
                    <h4 className="text-[11px] font-mono font-bold text-slate-700 uppercase tracking-wide flex items-center gap-1.5 mb-1">
                      <Stethoscope className="w-3.5 h-3.5 text-sky-600" />
                      Attending Physician Clinical Notes
                    </h4>
                    <p className="text-xs text-slate-800 font-sans leading-relaxed p-3 bg-white border border-slate-200 rounded-xl shadow-2xs">
                      {activeItem.notes || 'No specific clinical annotations provided.'}
                    </p>
                  </div>

                  {activeItem.corrected_diagnosis && (
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl">
                      <span className="text-[10px] font-mono font-bold text-amber-800 uppercase block mb-0.5">
                        Physician Corrected Diagnosis
                      </span>
                      <p className="text-xs font-bold text-slate-900">{activeItem.corrected_diagnosis}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Underlying Clinical Report Card */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
                <div className="px-5 py-3.5 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                  <h3 className="text-xs font-mono font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5 text-sky-600" />
                    Evaluated Clinical Assessment Report
                  </h3>
                  <span className="text-[10px] font-mono text-slate-400">REPORT ID: {activeItem.report.id}</span>
                </div>

                <div className="p-5 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <span className="text-[10px] font-mono text-slate-500 uppercase block">Patient</span>
                      <span className="text-xs font-bold text-slate-900 font-sans">
                        {activeItem.report.patient_name} ({activeItem.report.patient_age}y {activeItem.report.patient_sex})
                      </span>
                    </div>

                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <span className="text-[10px] font-mono text-slate-500 uppercase block">Primary Diagnosis</span>
                      <span className="text-xs font-bold text-sky-800 font-sans">
                        {activeItem.report.primary_diagnosis}
                      </span>
                    </div>

                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <span className="text-[10px] font-mono text-slate-500 uppercase block">Confidence</span>
                      <span className="text-xs font-bold text-slate-900 font-mono">
                        {Math.round((activeItem.report.diagnostic_confidence || 0.9) * 100)}%
                      </span>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-[11px] font-mono font-bold text-slate-700 uppercase tracking-wide mb-1">
                      Chief Complaint
                    </h4>
                    <p className="text-xs text-slate-800 bg-slate-50 p-3 rounded-xl border border-slate-200 font-sans">
                      {activeItem.report.chief_complaint}
                    </p>
                  </div>

                  <div>
                    <h4 className="text-[11px] font-mono font-bold text-slate-700 uppercase tracking-wide mb-1">
                      Clinical Reasoning &amp; Pathophysiology
                    </h4>
                    <p className="text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200 font-sans leading-relaxed whitespace-pre-line">
                      {activeItem.report.clinical_reasoning}
                    </p>
                  </div>

                  {activeItem.report.treatment_plan && activeItem.report.treatment_plan.length > 0 && (
                    <div>
                      <h4 className="text-[11px] font-mono font-bold text-slate-700 uppercase tracking-wide mb-1">
                        Prescribed Treatment Regimen
                      </h4>
                      <ul className="list-disc list-inside space-y-1 text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200">
                        {activeItem.report.treatment_plan.map((tx, idx) => (
                          <li key={idx} className="font-sans">{tx}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-12 text-slate-400">
              <FileCheck2 className="w-12 h-12 mb-3 text-slate-300" />
              <h3 className="text-sm font-mono font-bold text-slate-700 uppercase">NO REPORT SELECTED</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm">
                Select an evaluated report from the left panel to inspect doctor grades, clinical notes, and treatment details.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Manual Fine-Tuning Modal */}
      {isTrainingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-purple-50 via-white to-indigo-50 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 font-sans uppercase">
                    Manual Model Fine-Tuning Console
                  </h3>
                  <p className="text-[11px] text-slate-500 font-mono">
                    Direct Preference Optimization (DPO) • MedGemma 4-Bit LoRA
                  </p>
                </div>
              </div>

              <button
                onClick={() => setIsTrainingModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 transition cursor-pointer text-xs font-mono"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4 font-sans text-xs">
              <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-xl text-purple-900">
                <p className="font-bold font-mono text-[11px] uppercase mb-0.5">Strict Manual Policy Gate</p>
                <p className="text-[11px] text-purple-800 leading-relaxed">
                  Automatic fine-tuning is disabled. Model weight optimization only runs when explicitly triggered by you. Preference pairs synthesized from verified physician evaluations will be passed into the DPO pipeline.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[10px] text-slate-500 uppercase block font-bold">Evaluated Cases Available</span>
                  <span className="text-base font-black text-slate-900">{totalReviewed} Cases</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[10px] text-slate-500 uppercase block font-bold">Target Foundation Model</span>
                  <span className="text-xs font-bold text-slate-800">MedGemma 4B (NF4)</span>
                </div>
              </div>

              {/* Training Parameters Form */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <label className="font-mono text-[11px] font-bold text-slate-700">Epochs:</label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={epochs}
                    onChange={(e) => setEpochs(Number(e.target.value))}
                    className="w-20 px-2 py-1 border border-slate-300 rounded font-mono text-center focus:outline-none focus:border-purple-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <label className="font-mono text-[11px] font-bold text-slate-700">Learning Rate:</label>
                  <input
                    type="number"
                    step="0.00005"
                    value={learningRate}
                    onChange={(e) => setLearningRate(Number(e.target.value))}
                    className="w-28 px-2 py-1 border border-slate-300 rounded font-mono text-center focus:outline-none focus:border-purple-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-mono text-[11px] font-bold text-slate-700 block">Dry-Run Mode:</label>
                    <span className="text-[10px] text-slate-400">Verify data pipeline without consuming GPU VRAM</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={useDryRun}
                    onChange={(e) => setUseDryRun(e.target.checked)}
                    className="w-4 h-4 rounded text-purple-600 focus:ring-purple-500 cursor-pointer"
                  />
                </div>
              </div>

              {/* Status or Result Message */}
              {trainingStatus && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-[11px] font-mono flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>{trainingStatus}</span>
                </div>
              )}

              {trainingResult && (
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-xl text-purple-900 text-[11px] font-mono space-y-1">
                  <p className="font-bold uppercase tracking-wider text-purple-800">Training Metrics Summary:</p>
                  <p>Status: <span className="font-bold text-emerald-700">{trainingResult.status}</span></p>
                  <p>Verified Pairs Trained: <span className="font-bold">{trainingResult.pairs_trained || 0}</span></p>
                  {trainingResult.final_loss !== undefined && (
                    <p>Convergence Loss: <span className="font-bold">{trainingResult.final_loss}</span></p>
                  )}
                  {trainingResult.adapter_path && (
                    <p className="text-[10px] text-purple-700 truncate">Saved Path: {trainingResult.adapter_path}</p>
                  )}
                </div>
              )}

              {trainingError && (
                <div data-testid="train-blocked-503" className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-[11px] font-mono flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>{trainingError}</span>
                </div>
              )}
            </div>

            <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setIsTrainingModalOpen(false)}
                className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-mono font-semibold rounded-xl transition cursor-pointer"
              >
                CLOSE
              </button>

              <button
                type="button"
                onClick={handleManualTrain}
                disabled={isTraining}
                className="px-5 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-mono font-bold rounded-xl shadow-md shadow-purple-500/20 flex items-center gap-2 transition cursor-pointer active:scale-[0.98] disabled:opacity-50"
              >
                {isTraining ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>TRAINING IN PROGRESS...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>SEND DATA FOR MODEL TRAINING</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewedReportsSection;
