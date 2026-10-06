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
            MANUAL MODEL TRAINING
          </Button>

          <Button
            variant="secondary"
            size="md"
            onClick={fetchReviewedReports}
            disabled={loading}
            leadingIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          >
            Refresh
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
                  {sc === 'ALL' ? 'All Scores' : sc === '3_OR_LESS' ? '≤3★' : `${sc}★`}
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
                        fontSize: '0.6875rem',
                      }}
                    >
                      <span className="caption" style={{ color: 'var(--text-tertiary)' }}>
                        {item.physician_name || 'Attending Physician'}
                      </span>
                      <span className="ak-num" style={{ fontWeight: 700, color: '#EAB308' }}>
                        {item.overall_score}/5 ★
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
                    <Star className="w-3.5 h-3.5" style={{ marginRight: 4, fill: '#EAB308', display: 'inline-block' }} />
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
