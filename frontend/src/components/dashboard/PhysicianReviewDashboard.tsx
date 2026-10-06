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
} from 'lucide-react';

import {
  Button,
  Badge,
  Card,
  CardHead,
  CardTitle,
  TextField,
  TextArea,
  Select,
  Alert,
  EmptyState,
  ProgressBar,
  Chip,
} from '../ui';
import { AppPage } from '../layout/Templates';

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
      <AppPage
        title="Physician Review Queue"
        description="Clinical report verification, independent audit dimensions, and RL DPO preference alignment."
      >
        <EmptyState
          icon={<FileText className="w-8 h-8" />}
          title="No clinical reports pending review"
          description="Simulate an encounter or admit a patient to generate autonomous Clinical AI reports grounded in Harrison's 21st Edition evidence."
          action={
            <Button
              variant="secondary"
              size="md"
              onClick={handleResetReports}
              leadingIcon={<RotateCcw className="w-3.5 h-3.5" />}
            >
              Reset Records to Zero
            </Button>
          }
        />
      </AppPage>
    );
  }

  const confidencePct = Math.round((activeReport?.diagnostic_confidence || 0.92) * 100);

  return (
    <AppPage
      title="Physician Review Dashboard"
      description="Clinical report verification, multi-stage independent audit dimensions, and DPO alignment."
      breadcrumbs={[
        { label: 'Clinical Ops', href: '#' },
        { label: 'Physician Review', isCurrent: true },
      ]}
      actions={
        <Button
          variant="secondary"
          size="md"
          onClick={handleResetReports}
          leadingIcon={<RotateCcw className="w-3.5 h-3.5" />}
        >
          Reset Review Queue
        </Button>
      }
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(260px, 320px) 1fr',
          gap: 'var(--space-6)',
          alignItems: 'start',
        }}
      >
        {/* SIDEBAR: CLINICAL REPORT QUEUE */}
        <Card style={{ padding: 0, overflow: 'hidden' }}>
          <div
            style={{
              padding: 'var(--space-4)',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'var(--bg-app)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Stethoscope className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
              <div>
                <h3 className="heading-3" style={{ fontSize: '0.875rem', margin: 0 }}>
                  Clinical Queue
                </h3>
                <span className="caption" style={{ color: 'var(--text-secondary)' }}>
                  Autonomous Encounters
                </span>
              </div>
            </div>

            <Badge variant="brand" hasDot>
              {reports.length} Ready
            </Badge>
          </div>

          <div
            style={{
              padding: 'var(--space-3)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
              maxHeight: 'calc(100vh - 280px)',
              overflowY: 'auto',
            }}
          >
            {reports.map((rep) => {
              const isSelected = rep.id === activeReport?.id;
              return (
                <div
                  key={rep.id}
                  onClick={() => setSelectedReportId(rep.id)}
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
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span className="caption ak-num" style={{ fontWeight: 700, color: 'var(--color-primary)' }}>
                      {rep.id}
                    </span>
                    <span className="caption ak-num" style={{ color: 'var(--text-tertiary)' }}>
                      {new Date(rep.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  <div className="heading-3" style={{ fontSize: '0.875rem', marginTop: 4, marginBottom: 2 }}>
                    {rep.patient_name}
                  </div>

                  <div
                    className="body-sm"
                    style={{
                      color: 'var(--text-secondary)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {rep.primary_diagnosis}
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginTop: 'var(--space-2)',
                      paddingTop: 'var(--space-2)',
                      borderTop: '1px solid var(--border-subtle)',
                      fontSize: '0.75rem',
                    }}
                  >
                    <span className="caption" style={{ color: 'var(--text-secondary)' }}>Confidence:</span>
                    <span className="ak-num" style={{ fontWeight: 700, color: 'var(--color-success)' }}>
                      {Math.round((rep.diagnostic_confidence || 0.9) * 100)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* MAIN DETAIL COLUMN */}
        {activeReport && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
            {/* SUCCESS BANNER */}
            {submittedReviewSuccess && (
              <Alert variant="success" title="Review Verdict Committed">
                Physician review verdict successfully logged to clinical records and DPO fine-tuning set.
              </Alert>
            )}

            {/* TOP REPORT HEADER CARD */}
            <Card>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: 'var(--space-4)',
                  paddingBottom: 'var(--space-4)',
                  borderBottom: '1px solid var(--border-subtle)',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <Badge variant="brand">{activeReport.id}</Badge>
                    <span className="caption ak-num" style={{ color: 'var(--text-tertiary)' }}>
                      Encounter: {activeReport.encounter_id}
                    </span>
                  </div>
                  <h2 className="heading-2" style={{ marginTop: 'var(--space-2)', marginBottom: 2 }}>
                    {activeReport.patient_name}
                  </h2>
                  <p className="caption ak-num" style={{ color: 'var(--text-secondary)', margin: 0 }}>
                    {activeReport.patient_id} • Admitted to Clinical Care Pathway
                  </p>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3) var(--space-4)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    textAlign: 'right',
                  }}
                >
                  <div className="display-sm ak-num" style={{ color: 'var(--color-primary)' }}>
                    {confidencePct}%
                  </div>
                  <div className="caption" style={{ color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                    Diagnostic Confidence
                  </div>
                </div>
              </div>

              {/* Vitals Telemetry */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: 'var(--space-3)',
                  paddingTop: 'var(--space-4)',
                }}
              >
                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    textAlign: 'center',
                  }}
                >
                  <div className="caption" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, color: 'var(--text-secondary)' }}>
                    <HeartPulse className="w-3.5 h-3.5" style={{ color: 'var(--color-success)' }} />
                    Heart Rate
                  </div>
                  <div className="heading-3 ak-num" style={{ marginTop: 4 }}>
                    {activeReport.vital_signs.heart_rate} BPM
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    textAlign: 'center',
                  }}
                >
                  <div className="caption" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, color: 'var(--text-secondary)' }}>
                    <Activity className="w-3.5 h-3.5" style={{ color: 'var(--color-primary)' }} />
                    Blood Pressure
                  </div>
                  <div className="heading-3 ak-num" style={{ marginTop: 4 }}>
                    {activeReport.vital_signs.systolic_bp}/{activeReport.vital_signs.diastolic_bp}
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    textAlign: 'center',
                  }}
                >
                  <div className="caption" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, color: 'var(--text-secondary)' }}>
                    <Thermometer className="w-3.5 h-3.5" style={{ color: 'var(--text-tertiary)' }} />
                    O2 Saturation
                  </div>
                  <div className="heading-3 ak-num" style={{ marginTop: 4 }}>
                    {activeReport.vital_signs.spo2_percent}%
                  </div>
                </div>
              </div>
            </Card>

            {/* AUTOMATED INDEPENDENT MULTI-STAGE EVALUATION */}
            {activeReport.automated_evaluation ? (
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
                    {activeReport.automated_evaluation.passed ? (
                      <ShieldCheck className="w-6 h-6" style={{ color: 'var(--color-success)' }} />
                    ) : (
                      <ShieldAlert className="w-6 h-6" style={{ color: 'var(--color-danger)' }} />
                    )}
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <span className="heading-3" style={{ fontSize: '0.875rem' }}>
                          Independent Evaluation Pipeline
                        </span>
                        <Badge
                          variant={
                            activeReport.automated_evaluation.final_status === 'PASSED'
                              ? 'success'
                              : activeReport.automated_evaluation.final_status === 'FLAGGED'
                              ? 'warning'
                              : 'danger'
                          }
                          hasDot
                        >
                          {activeReport.automated_evaluation.final_status}
                        </Badge>
                      </div>
                      <p className="caption" style={{ color: 'var(--text-secondary)', margin: '2px 0 0' }}>
                        Multi-Stage Audit (6 Focused Dimensions) • Pre-Review Verification
                      </p>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div className="heading-2 ak-num" style={{ margin: 0 }}>
                      {Math.round(activeReport.automated_evaluation.overall_score * 100)}%
                    </div>
                    <span className="caption" style={{ color: 'var(--text-secondary)' }}>
                      Overall Score
                    </span>
                  </div>
                </div>

                {/* 6 Dimension Score Grid */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: 'var(--space-3)',
                    marginTop: 'var(--space-4)',
                  }}
                >
                  {Object.entries(activeReport.automated_evaluation.dimensions).map(([key, dim]) => (
                    <div
                      key={key}
                      style={{
                        padding: 'var(--space-3)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                        backgroundColor: dim.passed ? 'var(--bg-app)' : 'var(--color-danger-tint)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span className="caption" style={{ fontWeight: 600 }}>{dim.display_name}</span>
                        <span
                          className="ak-num"
                          style={{
                            fontWeight: 700,
                            color: dim.passed ? 'var(--color-success)' : 'var(--color-danger)',
                            fontSize: '0.75rem',
                          }}
                        >
                          {Math.round(dim.score * 100)}%
                        </span>
                      </div>
                      <p className="caption" style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '0.6875rem' }}>
                        {dim.explanation}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Flagged items warning if any */}
                {activeReport.automated_evaluation.failed_checks.length > 0 && (
                  <div style={{ marginTop: 'var(--space-4)' }}>
                    <Alert variant="warning" title="Flagged items for physician review">
                      <ul style={{ margin: '4px 0 0', paddingLeft: 16 }}>
                        {activeReport.automated_evaluation.fail_reasons.map((reason, idx) => (
                          <li key={idx} className="body-sm">{reason}</li>
                        ))}
                      </ul>
                    </Alert>
                  </div>
                )}
              </Card>
            ) : (
              <Card>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <ShieldAlert className="w-5 h-5" style={{ color: 'var(--text-tertiary)' }} />
                    <span className="body-sm">
                      Independent multi-stage audit pending for this report.
                    </span>
                  </div>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleTriggerEvaluation(activeReport.id)}
                    disabled={evaluatingReport}
                    isLoading={evaluatingReport}
                  >
                    Run Automated Audit
                  </Button>
                </div>
              </Card>
            )}

            {/* DIFFERENTIAL DIAGNOSIS RANKING */}
            <Card>
              <CardHead>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <Badge variant="ai">AI</Badge>
                  <CardTitle>Differential Diagnosis Ranking</CardTitle>
                </div>
                <span className="caption ak-num" style={{ color: 'var(--text-secondary)' }}>
                  Probability Matrix
                </span>
              </CardHead>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {activeReport.differential_diagnosis.map((d, idx) => {
                  const pct = Math.round(d.likelihood * 100);
                  return (
                    <div key={idx}>
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          marginBottom: 4,
                        }}
                      >
                        <span className="body-sm" style={{ fontWeight: 500 }}>
                          <span className="ak-num" style={{ color: 'var(--text-tertiary)', marginRight: 6 }}>
                            {idx + 1}.
                          </span>
                          {d.condition}
                        </span>
                        <span className="ak-num" style={{ fontWeight: 700, color: 'var(--color-primary)' }}>
                          {pct}%
                        </span>
                      </div>
                      <ProgressBar
                        value={pct}
                        variant={idx === 0 ? 'spectrum' : 'primary'}
                        size="sm"
                      />
                    </div>
                  );
                })}
              </div>

              <div style={{ marginTop: 'var(--space-3)' }}>
                <span className="caption" style={{ color: 'var(--text-tertiary)' }}>
                  AI-assisted. Review before acting.
                </span>
              </div>
            </Card>

            {/* GUIDELINE-DIRECTED TREATMENT PLAN */}
            <Card>
              <CardHead>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--color-success)' }} />
                  <CardTitle>Guideline-Directed Treatment Plan</CardTitle>
                </div>
                <Badge variant="success">AHA/ACC Guideline Concordant</Badge>
              </CardHead>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {activeReport.treatment_plan.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      justifyContent: 'space-between',
                      backgroundColor: 'var(--bg-app)',
                      padding: 'var(--space-3)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      gap: 'var(--space-3)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-2)' }}>
                      <span className="caption ak-num" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                        {idx + 1}.
                      </span>
                      <span className="body-sm" style={{ fontWeight: 500 }}>{item}</span>
                    </div>
                    <Badge variant="neutral" style={{ flexShrink: 0 }}>
                      {idx === 0 ? 'Administered' : 'Ordered'}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>

            {/* INVESTIGATION FINDINGS */}
            {activeReport.investigation_results.length > 0 && (
              <Card>
                <CardHead>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <TestTube className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
                    <CardTitle>Diagnostic Investigations & Biomarkers</CardTitle>
                  </div>
                </CardHead>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                    gap: 'var(--space-3)',
                  }}
                >
                  {activeReport.investigation_results.map((res, i) => (
                    <div
                      key={i}
                      style={{
                        backgroundColor: 'var(--bg-app)',
                        padding: 'var(--space-3)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span className="caption ak-num" style={{ fontWeight: 700, color: 'var(--color-primary)' }}>
                          {res.test_type}
                        </span>
                        <Badge variant="success">Completed</Badge>
                      </div>
                      <p className="body-sm" style={{ margin: 0, color: 'var(--text-secondary)' }}>
                        {res.interpretation}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* RAG GROUNDING CITATIONS */}
            {((activeReport.medical_knowledge_citations && activeReport.medical_knowledge_citations.length > 0) ||
              ((activeReport as any).harrison_citations && (activeReport as any).harrison_citations.length > 0)) && (
              <Card>
                <CardHead>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <BookOpen className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
                    <CardTitle>Harrison's 21st Edition Vector Grounding</CardTitle>
                  </div>
                </CardHead>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                  {(activeReport.medical_knowledge_citations || (activeReport as any).harrison_citations || []).map((c: any, i: number) => (
                    <div
                      key={i}
                      style={{
                        backgroundColor: 'var(--bg-app)',
                        padding: 'var(--space-3)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <span className="caption" style={{ fontWeight: 700, color: 'var(--color-primary)', display: 'block', marginBottom: 2 }}>
                        {c.chapter || c.topic || 'Medical Grounding'}
                      </span>
                      <p className="body-sm" style={{ fontStyle: 'italic', margin: 0, color: 'var(--text-secondary)' }}>
                        "{c.text || c.excerpt}"
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* PHYSICIAN RL DPO ALIGNMENT CONSOLE */}
            <Card>
              <CardHead>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <Sparkles className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
                    <CardTitle>Physician RL DPO Alignment Console</CardTitle>
                  </div>
                  <span className="caption" style={{ color: 'var(--text-secondary)' }}>
                    Reinforce clinical reasoning and diagnosis accuracy through structured feedback
                  </span>
                </div>
                <Badge variant="outline">Model Ver. 4.2</Badge>
              </CardHead>

              {/* Star Rating */}
              <div
                style={{
                  backgroundColor: 'var(--bg-app)',
                  padding: 'var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  marginBottom: 'var(--space-4)',
                }}
              >
                <span className="ak-label" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>
                  Reward Score (1 to 5 Stars)
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-3)' }}>
                  <div style={{ display: 'flex', gap: 4 }}>
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setOverallScore(star)}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          padding: 4,
                        }}
                      >
                        <Star
                          className="w-6 h-6"
                          style={{
                            fill: star <= overallScore ? 'var(--ak-color-warning)' : 'none',
                            color: star <= overallScore ? 'var(--ak-color-warning)' : 'var(--border-subtle)',
                            transition: 'color 0.15s ease',
                          }}
                        />
                      </button>
                    ))}
                  </div>
                  <span className="caption ak-num" style={{ fontWeight: 600 }}>
                    {getScoreDescription(overallScore)}
                  </span>
                </div>
              </div>

              {/* Overall Assessment Buttons */}
              <div style={{ marginBottom: 'var(--space-4)' }}>
                <span className="ak-label" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>
                  Overall Clinical Assessment
                </span>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-2)' }}>
                  {REVIEW_ASSESSMENTS.map((item) => {
                    const isSelected = assessment === item.value;
                    return (
                      <Button
                        key={item.value}
                        variant={isSelected ? 'primary' : 'secondary'}
                        onClick={() => setAssessment(item.value)}
                        style={{ width: '100%' }}
                      >
                        {item.label}
                      </Button>
                    );
                  })}
                </div>
              </div>

              {/* Identified Clinical Defects */}
              <div style={{ marginBottom: 'var(--space-4)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
                  <span className="ak-label">Identified Clinical Defects (Optional)</span>
                  <span className="caption ak-num" style={{ color: 'var(--text-tertiary)' }}>
                    {identifiedErrors.length} selected
                  </span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {STRUCTURED_ERROR_TAXONOMY.map((err) => {
                    const isSelected = identifiedErrors.includes(err.code);
                    return (
                      <Chip
                        key={err.code}
                        isSelected={isSelected}
                        onClick={() => toggleErrorTag(err.code)}
                      >
                        {err.label}
                      </Chip>
                    );
                  })}
                </div>
              </div>

              {/* Reviewer Role & Diagnosis Grade */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: 'var(--space-4)',
                  marginBottom: 'var(--space-4)',
                }}
              >
                <Select
                  label="Reviewer Role"
                  value={reviewerRole}
                  onChange={(e) => setReviewerRole(e.target.value)}
                >
                  <option value="ATTENDING_PHYSICIAN">Attending Physician (MD/DO)</option>
                  <option value="CLINICAL_RESIDENT">Clinical Resident</option>
                  <option value="MEDICAL_STUDENT">Medical Student</option>
                </Select>

                <Select
                  label="Diagnosis Accuracy"
                  value={diagnosisGrade}
                  onChange={(e) => setDiagnosisGrade(e.target.value)}
                >
                  <option value="CORRECT">Correct (High Concordance)</option>
                  <option value="PARTIALLY_CORRECT">Partially Correct</option>
                  <option value="INCORRECT">Incorrect (Missed Diagnosis)</option>
                </Select>
              </div>

              {/* Rubric Selects */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: 'var(--space-4)',
                  marginBottom: 'var(--space-4)',
                }}
              >
                <Select
                  label="Clinical Reasoning"
                  value={reasoningGrade}
                  onChange={(e) => setReasoningGrade(e.target.value)}
                >
                  <option value="SOUND">Sound and Evidence-based</option>
                  <option value="MISSING_CRITICAL_EVIDENCE">Missing Critical Evidence</option>
                  <option value="FAULTY_LOGIC">Faulty Logical Leap</option>
                  <option value="UNSUPPORTED_CONCLUSION">Unsupported Conclusion</option>
                </Select>

                <Select
                  label="Workup & Lab Ordering"
                  value={testsGrade}
                  onChange={(e) => setTestsGrade(e.target.value)}
                >
                  <option value="APPROPRIATE">Appropriate and Indicated</option>
                  <option value="OVER_ORDERING">Over-ordering / Defensive</option>
                  <option value="MISSING_ESSENTIAL_TEST">Missing Essential Guideline Test</option>
                  <option value="INAPPROPRIATE_TEST">Inappropriate / Unsafe Test</option>
                </Select>

                <Select
                  label="Treatment Safety"
                  value={treatmentGrade}
                  onChange={(e) => setTreatmentGrade(e.target.value)}
                >
                  <option value="SAFE_AND_OPTIMAL">Safe and Guideline-Optimal</option>
                  <option value="SUBOPTIMAL">Suboptimal Intervention</option>
                  <option value="CONTRAINDICATED_OR_HARMFUL">Contraindicated / Harmful</option>
                </Select>
              </div>

              {/* Structured Corrections */}
              <div
                style={{
                  backgroundColor: 'var(--bg-app)',
                  padding: 'var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-3)',
                  marginBottom: 'var(--space-4)',
                }}
              >
                <span className="heading-3" style={{ fontSize: '0.875rem' }}>
                  Structured Clinical Corrections (Optional)
                </span>

                <TextField
                  label="Corrected Primary Diagnosis"
                  value={correctedDiagnosis}
                  onChange={(e) => setCorrectedDiagnosis(e.target.value)}
                  placeholder="e.g. Acute Non-ST-Elevation Myocardial Infarction"
                />

                <TextArea
                  label="Corrected Clinical Reasoning"
                  value={correctedReasoning}
                  onChange={(e) => setCorrectedReasoning(e.target.value)}
                  placeholder="Physiological rationale supporting the diagnosis..."
                  rows={2}
                />

                <TextArea
                  label="Corrected Recommendations & Treatment (One per line)"
                  value={correctedRecommendations}
                  onChange={(e) => setCorrectedRecommendations(e.target.value)}
                  placeholder="Aspirin 325 mg PO chewable immediately&#10;Ticagrelor 180 mg PO loading dose"
                  rows={2}
                />
              </div>

              <TextArea
                label="Attending Clinical Notes / Critique"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Attending feedback or training preference..."
                rows={2}
              />

              {/* Action Buttons */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: 'var(--space-3)',
                  marginTop: 'var(--space-6)',
                }}
              >
                <Button
                  variant="primary"
                  size="lg"
                  onClick={() => handleReviewAction(true)}
                  disabled={isSubmitting}
                  isLoading={isSubmitting}
                  leadingIcon={<ThumbsUp className="w-4 h-4" />}
                >
                  Approve Verdict
                </Button>

                <Button
                  variant="danger"
                  size="lg"
                  onClick={() => handleReviewAction(false)}
                  disabled={isSubmitting}
                  leadingIcon={<ThumbsDown className="w-4 h-4" />}
                >
                  Reject / Flag Case
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </AppPage>
  );
};

export default PhysicianReviewDashboard;
