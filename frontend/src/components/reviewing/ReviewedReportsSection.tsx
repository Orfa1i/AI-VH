import React, { useState, useEffect, useCallback } from 'react';
import {
  FileCheck2,
  CheckCircle2,
  XCircle,
  Star,
  Search,
  Stethoscope,
  RefreshCw,
  Cpu,
  Play,
  BookOpen,
} from 'lucide-react';

import type { ClinicalReport } from '../../types';
import {
  Button,
  Badge,
  Card,
  CardHead,
  CardTitle,
  Dialog,
  TextField,
  Checkbox,
  Stat,
  EmptyState,
  Alert,
  Chip,
} from '../ui';
import { AppPage } from '../layout/Templates';

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

const CANONICAL_DEMO_REVIEWED: ReviewedReportItem[] = [
  {
    id: 'rev-demo-001',
    report_id: 'rep-demo-arthur',
    encounter_id: 'enc-demo-002',
    physician_name: 'Dr. Marcus Vance, MD (Chief of Cardiology)',
    reviewed_at: new Date(Date.now() - 3600000 * 3).toISOString(),
    diagnosis_grade: 'CORRECT',
    reasoning_grade: 'SOUND',
    tests_grade: 'APPROPRIATE',
    treatment_grade: 'SAFE_AND_OPTIMAL',
    overall_score: 5,
    approved: true,
    notes: 'Exemplary clinical reasoning. NSTEMI promptly identified with serial hs-cTnT and dynamic ECG correlation. Guideline-directed antiplatelet therapy and statin initiation strictly align with 2024 ESC/ACC NSTE-ACS guidelines.',
    report: {
      id: 'rep-demo-arthur',
      encounter_id: 'enc-demo-002',
      patient_id: 'pat-demo-002',
      patient_name: 'Arthur Pendelton',
      patient_age: 68,
      patient_sex: 'Male',
      created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
      chief_complaint: 'Substernal chest pressure radiating to left mandible, diaphoresis, dyspnea on exertion.',
      history_of_present_illness: '68-year-old male with hypertension and hyperlipidemia presenting with acute onset retrosternal crushing chest pressure radiating to left jaw and shoulder for 45 minutes, associated with cold diaphoresis.',
      past_medical_history: ['Hypertension (10 yrs)', 'Hyperlipidemia', 'Ex-smoker (20 pack-years)'],
      medications: ['Amlodipine 5mg daily', 'Atorvastatin 20mg daily'],
      allergies: ['NKDA'],
      vital_signs: {
        timestamp: new Date().toISOString(),
        heart_rate: 94,
        systolic_bp: 154,
        diastolic_bp: 92,
        respiratory_rate: 20,
        temperature_c: 36.7,
        spo2_percent: 96,
        pain_score: 8,
      },
      physical_exam_findings: {
        Cardiovascular: 'S4 gallop present, no murmurs, normal peripheral pulses.',
        Pulmonary: 'Bibasilar end-inspiratory crackles.',
      },
      investigations_ordered: ['Serial 12-lead ECG', 'High-sensitivity Troponin T (0h, 1h)', 'CBC, CMP, Lipid panel'],
      investigation_results: [
        {
          test_type: 'High-Sensitivity Troponin T',
          values: { '0h': '68 ng/L', '1h': '142 ng/L' },
          abnormal_flags: { '0h': true, '1h': true },
          interpretation: 'Marked delta elevation (>5 ng/L rise at 1 hour) confirming acute myocardial injury.',
        },
      ],
      differential_diagnosis: [
        {
          condition: 'Non-ST-Elevation Myocardial Infarction (NSTEMI)',
          likelihood: 0.94,
          supporting_points: ['Significant delta troponin elevation', 'ST-depression in leads V4-V6', 'Classic anginal presentation'],
          opposing_points: ['No persistent ST-elevation on initial ECG'],
        },
      ],
      primary_diagnosis: 'Acute Coronary Syndrome: Non-ST-Elevation Myocardial Infarction (NSTEMI, TIMI Risk Score 5)',
      diagnostic_confidence: 0.96,
      clinical_reasoning: 'Positive biomarker delta with ischemic symptoms meets universal definition of acute myocardial infarction. Early invasive coronary angiography indicated within 24 hours.',
      treatment_plan: [
        'Aspirin 324mg chewed stat, Ticagrelor 180mg loading dose.',
        'Enoxaparin 1mg/kg SQ q12h.',
        'Atorvastatin 80mg oral stat.',
        'Urgent cardiology consultation for cardiac catheterization.',
      ],
      recommended_disposition: 'ADMIT_CARDIAC_ICU',
      medical_knowledge_citations: [
        {
          book: "Braunwald's Heart Disease (12th Edition)",
          chapter: 'Chapter 38: Acute Coronary Syndromes',
          topic: 'High-Sensitivity Troponin Rapid Diagnostic Algorithms',
          source: "Braunwald's, 12e, Ch 38",
          excerpt: 'A 0h/1h or 0h/2h hs-cTn algorithm allows rapid rule-in and rule-out of NSTEMI with high negative and positive predictive values.',
          relevance_score: 0.97,
        },
      ],
    },
  },
  {
    id: 'rev-demo-002',
    report_id: 'rep-demo-diana',
    encounter_id: 'enc-demo-004',
    physician_name: 'Dr. Sarah Chen, MD (Stroke Neurology)',
    reviewed_at: new Date(Date.now() - 3600000 * 8).toISOString(),
    diagnosis_grade: 'CORRECT',
    reasoning_grade: 'SOUND',
    tests_grade: 'APPROPRIATE',
    treatment_grade: 'SAFE_AND_OPTIMAL',
    overall_score: 5,
    approved: true,
    notes: 'Flawless acute stroke protocol activation. NIHSS calculated accurately at 7. Non-contrast head CT ruled out hemorrhage within 25 minutes of door arrival.',
    report: {
      id: 'rep-demo-diana',
      encounter_id: 'enc-demo-004',
      patient_id: 'pat-demo-004',
      patient_name: 'Diana Reyes',
      patient_age: 35,
      patient_sex: 'Female',
      created_at: new Date(Date.now() - 3600000 * 9).toISOString(),
      chief_complaint: 'Acute onset left-sided facial droop and right upper extremity pronator drift.',
      history_of_present_illness: '35-year-old female presenting with sudden-onset focal neurological deficits that began 75 minutes prior to arrival while at work.',
      past_medical_history: ['Migraine with aura', 'Oral contraceptive use'],
      medications: ['Combined oral contraceptive pill daily'],
      allergies: ['NKDA'],
      vital_signs: {
        timestamp: new Date().toISOString(),
        heart_rate: 76,
        systolic_bp: 138,
        diastolic_bp: 82,
        respiratory_rate: 16,
        temperature_c: 36.6,
        spo2_percent: 99,
        pain_score: 2,
      },
      physical_exam_findings: {
        Neurological: 'Alert and oriented x4. Left lower facial weakness, mild dysarthria, right pronator drift, NIHSS score: 7.',
      },
      investigations_ordered: ['Non-contrast Head CT', 'CTA Head and Neck', 'Point-of-care blood glucose', 'Coagulation studies'],
      investigation_results: [
        {
          test_type: 'Non-contrast Head CT',
          values: { Intracranial_Hemorrhage: 'Negative', ASPECTS: '10/10' },
          abnormal_flags: { Intracranial_Hemorrhage: false },
          interpretation: 'No acute intracranial hemorrhage or territorial infarction identified.',
        },
      ],
      differential_diagnosis: [
        {
          condition: 'Acute Ischemic Stroke (LVO vs. Small Vessel)',
          likelihood: 0.88,
          supporting_points: ['Sudden focal neurological deficit', 'Clear onset time within 4.5 hour thrombolysis window'],
          opposing_points: ['Young patient without traditional cardiovascular risk factors'],
        },
      ],
      primary_diagnosis: 'Acute Ischemic Cerebrovascular Event (Candidate for IV Tenecteplase / Thrombolysis)',
      diagnostic_confidence: 0.91,
      clinical_reasoning: 'Deficit onset < 4.5 hours with CT negative for hemorrhage. Rapid thrombolytic assessment initiated per AHA/ASA Guidelines.',
      treatment_plan: [
        'Confirm IV access, maintain BP < 185/110 mmHg.',
        'Administer Tenecteplase (TNK-tPA) 0.25 mg/kg IV bolus over 5 seconds.',
        'Continuous neuro-checks and NIHSS monitoring q15m.',
        'Admit to Comprehensive Stroke Unit / Neuro-ICU.',
      ],
      recommended_disposition: 'ADMIT_NEURO_ICU',
      medical_knowledge_citations: [
        {
          book: "Adams and Victor's Principles of Neurology (12th Edition)",
          chapter: 'Chapter 33: Cerebrovascular Diseases',
          topic: 'Intravenous Thrombolysis Indications and Safety Criteria',
          source: "Adams & Victor's, 12e, Ch 33",
          excerpt: 'Intravenous thrombolysis with tenecteplase or alteplase within 4.5 hours of ischemic stroke onset significantly improves functional outcomes at 90 days.',
          relevance_score: 0.96,
        },
      ],
    },
  },
];

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
        const items = Array.isArray(data) && data.length > 0 ? data : CANONICAL_DEMO_REVIEWED;
        setReviewedItems(items);
        setSelectedId((prev) => prev || (items[0]?.id ?? null));
      } else {
        setReviewedItems(CANONICAL_DEMO_REVIEWED);
        setSelectedId((prev) => prev || CANONICAL_DEMO_REVIEWED[0].id);
      }
    } catch {
      setReviewedItems(CANONICAL_DEMO_REVIEWED);
      setSelectedId((prev) => prev || CANONICAL_DEMO_REVIEWED[0].id);
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
        if (res.status === 422) {
          const detail = errorData.detail || {};
          const failedGates = detail.validation?.failed_gates || [];
          const blockers = detail.blockers || [];
          throw new Error(
            `Training Blocked: ${failedGates.length} pre-training validation gates failed (${failedGates.join(', ')}). ${blockers.slice(0, 1).join(' ')}`
          );
        }
        throw new Error(typeof errorData.detail === 'string' ? errorData.detail : 'Fine-tuning execution failed.');
      }

      const result = await res.json();
      setTrainingResult(result);
      setTrainingStatus(`Model fine-tuning completed successfully. Adapter saved to ${result.adapter_path || 'models/medgemma-dpo-lora'}`);
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

    if (approvalFilter === 'APPROVED' && !item.approved) return false;
    if (approvalFilter === 'REJECTED' && item.approved) return false;

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
    <AppPage
      title="Reviewing Archive & Doctor Evaluations"
      description="Central archive of all clinical reports evaluated and signed by attending physicians. Ground truth for MedGemma RL fine-tuning."
      breadcrumbs={[
        { label: 'Clinical Ops', href: '#' },
        { label: 'Reviewing Archive', isCurrent: true },
      ]}
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Button
            variant="primary"
            size="md"
            onClick={() => setIsTrainingModalOpen(true)}
            leadingIcon={<Cpu className="w-3.5 h-3.5" />}
          >
            Start manual training
          </Button>

          <Button
            variant="secondary"
            size="md"
            onClick={fetchReviewedReports}
            disabled={loading}
            leadingIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Refresh reports
          </Button>
        </div>
      }
    >
      {/* SUMMARY KPI CARDS */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <Stat label="Total Evaluated" value={totalReviewed} delta="Doctor reviews" />
        <Stat label="Approval Rate" value={`${approvalRate}%`} delta={`${approvedCount} of ${totalReviewed} approved`} />
        <Stat label="Avg Physician Score" value={`${avgScore} / 5`} delta="Guideline concordant" />
        <Stat label="Training Policy" value="Manual" delta="Triggered explicitly" />
      </div>

      {/* MASTER-DETAIL VIEW */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(280px, 340px) 1fr',
          gap: 'var(--space-6)',
          alignItems: 'start',
        }}
      >
        {/* LEFT COLUMN: FILTERS & MASTER LIST */}
        <Card style={{ padding: 0, overflow: 'hidden' }}>
          <div
            style={{
              padding: 'var(--space-3)',
              borderBottom: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-app)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
            }}
          >
            <TextField
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search patient, diagnosis, doctor..."
              leadingIcon={<Search className="w-3.5 h-3.5" style={{ color: 'var(--text-tertiary)' }} />}
            />

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {(['ALL', 'APPROVED', 'REJECTED'] as const).map((filter) => (
                <Chip
                  key={filter}
                  isSelected={approvalFilter === filter}
                  onClick={() => setApprovalFilter(filter)}
                >
                  {filter === 'ALL' ? 'All' : filter === 'APPROVED' ? 'Approved' : 'Rejected'}
                </Chip>
              ))}
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {(['ALL', '5', '4', '3_OR_LESS'] as const).map((sc) => (
                <Chip
                  key={sc}
                  isSelected={scoreFilter === sc}
                  onClick={() => setScoreFilter(sc)}
                >
                  {sc === 'ALL' ? 'All scores' : sc === '3_OR_LESS' ? '≤ 3 stars' : `${sc} stars`}
                </Chip>
              ))}
            </div>
          </div>

          {/* LIST */}
          <div
            style={{
              maxHeight: 'calc(100vh - 360px)',
              overflowY: 'auto',
              padding: 'var(--space-2)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
            }}
          >
            {filteredItems.length === 0 ? (
              <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
                <p className="caption" style={{ color: 'var(--text-tertiary)', margin: 0 }}>
                  No reviewed cases found.
                </p>
              </div>
            ) : (
              filteredItems.map((item) => {
                const isSelected = activeItem?.id === item.id;
                return (
                  <div
                    key={item.id}
                    onClick={() => setSelectedId(item.id)}
                    style={{
                      padding: 'var(--space-3)',
                      borderRadius: 'var(--radius-md)',
                      border: isSelected
                        ? '2px solid var(--color-primary)'
                        : '1px solid var(--border-subtle)',
                      backgroundColor: isSelected ? 'var(--color-primary-tint)' : 'var(--bg-surface)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                      <span className="heading-3" style={{ fontSize: '0.875rem', margin: 0 }}>
                        {item.report.patient_name || 'Patient'}
                      </span>
                      <Badge variant={item.approved ? 'success' : 'danger'}>
                        {item.approved ? 'Approved' : 'Revision Req.'}
                      </Badge>
                    </div>

                    <p
                      className="body-sm"
                      style={{
                        margin: '2px 0 6px',
                        color: 'var(--text-secondary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      Dx: <strong style={{ color: 'var(--text-primary)' }}>{item.report.primary_diagnosis}</strong>
                    </p>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        paddingTop: 'var(--space-2)',
                        borderTop: '1px solid var(--border-subtle)',
                        fontSize: '0.75rem',
                      }}
                    >
                      <span className="caption" style={{ color: 'var(--text-tertiary)' }}>
                        {item.physician_name || 'Attending Physician'}
                      </span>
                      <span className="ak-num" style={{ fontWeight: 700, color: 'var(--ak-color-warning)' }}>
                        {item.overall_score}/5 stars
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </Card>

        {/* RIGHT COLUMN: DETAIL VIEW */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {activeItem ? (
            <>
              {/* Doctor Review Card */}
              <Card>
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 'var(--space-3)',
                    paddingBottom: 'var(--space-4)',
                    borderBottom: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                    {activeItem.approved ? (
                      <CheckCircle2 className="w-6 h-6" style={{ color: 'var(--color-success)' }} />
                    ) : (
                      <XCircle className="w-6 h-6" style={{ color: 'var(--color-danger)' }} />
                    )}
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <h2 className="heading-3" style={{ margin: 0 }}>
                          Attending Physician Evaluation Report
                        </h2>
                        <Badge variant={activeItem.approved ? 'success' : 'danger'}>
                          {activeItem.approved ? 'CLINICALLY APPROVED' : 'REVISION REQUIRED'}
                        </Badge>
                      </div>
                      <p className="caption ak-num" style={{ color: 'var(--text-secondary)', margin: '2px 0 0' }}>
                        Reviewed by {activeItem.physician_name} • {new Date(activeItem.reviewed_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <Badge variant="warning">
                    <Star className="w-3.5 h-3.5" style={{ marginRight: 4, fill: 'var(--ak-color-warning)', display: 'inline-block' }} />
                    {activeItem.overall_score}.0 / 5.0 Rating
                  </Badge>
                </div>

                {/* 4 Rubric Grades */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: 'var(--space-3)',
                    paddingTop: 'var(--space-4)',
                    paddingBottom: 'var(--space-4)',
                    borderBottom: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                    <span className="caption" style={{ color: 'var(--text-tertiary)', display: 'block' }}>Diagnosis Grade</span>
                    <strong className="body-sm ak-num" style={{ marginTop: 2, display: 'block' }}>{activeItem.diagnosis_grade}</strong>
                  </div>

                  <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                    <span className="caption" style={{ color: 'var(--text-tertiary)', display: 'block' }}>Reasoning Grade</span>
                    <strong className="body-sm ak-num" style={{ marginTop: 2, display: 'block' }}>{activeItem.reasoning_grade}</strong>
                  </div>

                  <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                    <span className="caption" style={{ color: 'var(--text-tertiary)', display: 'block' }}>Workup & Tests</span>
                    <strong className="body-sm ak-num" style={{ marginTop: 2, display: 'block' }}>{activeItem.tests_grade}</strong>
                  </div>

                  <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                    <span className="caption" style={{ color: 'var(--text-tertiary)', display: 'block' }}>Treatment Safety</span>
                    <strong className="body-sm ak-num" style={{ marginTop: 2, display: 'block' }}>{activeItem.treatment_grade}</strong>
                  </div>
                </div>

                {/* Doctor Notes */}
                <div style={{ paddingTop: 'var(--space-4)' }}>
                  <span className="ak-label" style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
                    <Stethoscope className="w-3.5 h-3.5" style={{ color: 'var(--color-primary)' }} />
                    Attending Physician Clinical Notes
                  </span>
                  <div
                    style={{
                      backgroundColor: 'var(--bg-app)',
                      padding: 'var(--space-3)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <p className="body-sm" style={{ margin: 0 }}>
                      {activeItem.notes || 'No specific clinical annotations provided.'}
                    </p>
                  </div>
                </div>

                {activeItem.corrected_diagnosis && (
                  <div style={{ marginTop: 'var(--space-3)' }}>
                    <Alert variant="warning" title="Physician Corrected Diagnosis">
                      <strong>{activeItem.corrected_diagnosis}</strong>
                    </Alert>
                  </div>
                )}
              </Card>

              {/* Underlying Report Card */}
              <Card>
                <CardHead>
                  <CardTitle>Evaluated Clinical Assessment Report</CardTitle>
                  <span className="caption ak-num" style={{ color: 'var(--text-tertiary)' }}>
                    Report ID: {activeItem.report.id}
                  </span>
                </CardHead>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                    gap: 'var(--space-3)',
                    marginBottom: 'var(--space-4)',
                  }}
                >
                  <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                    <span className="caption" style={{ color: 'var(--text-tertiary)', display: 'block' }}>Patient</span>
                    <span className="body-sm" style={{ fontWeight: 600 }}>
                      {activeItem.report.patient_name} ({activeItem.report.patient_age}y {activeItem.report.patient_sex})
                    </span>
                  </div>

                  <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                    <span className="caption" style={{ color: 'var(--text-tertiary)', display: 'block' }}>Primary Diagnosis</span>
                    <span className="body-sm" style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                      {activeItem.report.primary_diagnosis}
                    </span>
                  </div>

                  <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                    <span className="caption" style={{ color: 'var(--text-tertiary)', display: 'block' }}>Confidence</span>
                    <span className="body-sm ak-num" style={{ fontWeight: 600 }}>
                      {Math.round((activeItem.report.diagnostic_confidence || 0.9) * 100)}%
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                  <div>
                    <span className="ak-label" style={{ display: 'block', marginBottom: 2 }}>Chief Complaint</span>
                    <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                      <p className="body-sm" style={{ margin: 0 }}>{activeItem.report.chief_complaint}</p>
                    </div>
                  </div>

                  <div>
                    <span className="ak-label" style={{ display: 'block', marginBottom: 2 }}>Clinical Reasoning & Pathophysiology</span>
                    <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                      <p className="body-sm" style={{ margin: 0, whiteSpace: 'pre-line' }}>{activeItem.report.clinical_reasoning}</p>
                    </div>
                  </div>

                  {activeItem.report.treatment_plan && activeItem.report.treatment_plan.length > 0 && (
                    <div>
                      <span className="ak-label" style={{ display: 'block', marginBottom: 2 }}>Prescribed Treatment Regimen</span>
                      <ul style={{ margin: 0, paddingLeft: 20, backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                        {activeItem.report.treatment_plan.map((tx, idx) => (
                          <li key={idx} className="body-sm">{tx}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {activeItem.report.medical_knowledge_citations && activeItem.report.medical_knowledge_citations.length > 0 && (() => {
                    const citList = activeItem.report.medical_knowledge_citations;
                    const primeBook = citList.find(c => c.book)?.book || citList[0]?.source || 'Specialty Medical Literature';
                    return (
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                          <BookOpen className="w-3.5 h-3.5" style={{ color: 'var(--color-primary)' }} />
                          <span className="ak-label" style={{ margin: 0 }}>{primeBook} Evidence Grounding</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                          {citList.map((c, idx) => (
                            <div
                              key={idx}
                              style={{
                                backgroundColor: 'var(--bg-app)',
                                padding: 'var(--space-3)',
                                borderRadius: 'var(--radius-sm)',
                                border: '1px solid var(--border-subtle)',
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4, flexWrap: 'wrap', gap: 4 }}>
                                <span className="caption" style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                                  {c.book || primeBook} · {c.chapter || c.topic || 'Clinical Reference'} {c.page ? `(p. ${c.page})` : ''}
                                </span>
                                {c.relevance != null && (
                                  <Badge variant="success" className="ak-num">
                                    {Math.round(c.relevance <= 1.0 ? c.relevance * 100 : Math.min(100, c.relevance * 10))}% Relevance
                                  </Badge>
                                )}
                              </div>
                              {(c.text || c.excerpt) && (
                                <p className="body-sm" style={{ margin: 0, fontStyle: 'italic', color: 'var(--text-secondary)' }}>
                                  "{c.text || c.excerpt}"
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              </Card>
            </>
          ) : (
            <EmptyState
              icon={<FileCheck2 className="w-8 h-8" />}
              title="No report selected"
              description="Select an evaluated report from the left panel to inspect doctor grades, clinical notes, and treatment details."
            />
          )}
        </div>
      </div>

      {/* MANUAL FINE-TUNING MODAL DIALOG */}
      {isTrainingModalOpen && (
        <Dialog
          isOpen={isTrainingModalOpen}
          onClose={() => setIsTrainingModalOpen(false)}
          title="Manual Model Fine-Tuning Console"
          description="Direct Preference Optimization (DPO) • MedGemma 4-Bit LoRA"
          actions={
            <>
              <Button variant="secondary" onClick={() => setIsTrainingModalOpen(false)}>
                Close
              </Button>
              <Button
                variant="primary"
                onClick={handleManualTrain}
                disabled={isTraining}
                isLoading={isTraining}
                leadingIcon={<Play className="w-3.5 h-3.5" />}
              >
                {isTraining ? 'Training in Progress...' : 'SEND DATA FOR MODEL TRAINING'}
              </Button>
            </>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <Alert variant="info" title="Strict Manual Policy Gate">
              Automatic fine-tuning is disabled. Model weight optimization only runs when explicitly triggered by you. Preference pairs synthesized from verified physician evaluations will be passed into the DPO pipeline.
            </Alert>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
              <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                <span className="caption" style={{ color: 'var(--text-tertiary)', display: 'block' }}>Evaluated Cases Available</span>
                <span className="heading-3 ak-num" style={{ marginTop: 2, display: 'block' }}>{totalReviewed} Cases</span>
              </div>
              <div style={{ backgroundColor: 'var(--bg-app)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                <span className="caption" style={{ color: 'var(--text-tertiary)', display: 'block' }}>Target Foundation Model</span>
                <span className="heading-3" style={{ fontSize: '0.875rem', marginTop: 2, display: 'block' }}>MedGemma 4B (NF4)</span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
              <TextField
                label="Epochs"
                type="number"
                min={1}
                max={20}
                value={epochs}
                onChange={(e) => setEpochs(Number(e.target.value))}
              />

              <TextField
                label="Learning Rate"
                type="number"
                step="0.00005"
                value={learningRate}
                onChange={(e) => setLearningRate(Number(e.target.value))}
              />
            </div>

            <Checkbox
              label="Dry-Run Mode"
              helpText="Verify data pipeline without consuming GPU VRAM"
              checked={useDryRun}
              onChange={(e) => setUseDryRun(e.target.checked)}
            />

            {trainingStatus && (
              <Alert variant="success" title="Training Status">
                {trainingStatus}
              </Alert>
            )}

            {trainingResult && (
              <Alert variant="info" title="Training Metrics Summary">
                <div className="ak-num">Status: {trainingResult.status}</div>
                <div className="ak-num">Pairs trained: {trainingResult.pairs_trained || 0}</div>
                {trainingResult.final_loss !== undefined && (
                  <div className="ak-num">Convergence Loss: {trainingResult.final_loss}</div>
                )}
              </Alert>
            )}

            {trainingError && (
              <div data-testid="train-blocked-503">
                <Alert variant="danger" title="Training Notice">
                  {trainingError}
                </Alert>
              </div>
            )}
          </div>
        </Dialog>
      )}
    </AppPage>
  );
};

export default ReviewedReportsSection;
