import React, { useState, useEffect } from 'react';
import type { DPOPreferencePair, DPOStatistics } from '../../types';
import {
  X,
  Sparkles,
  Download,
  ShieldAlert,
  BookOpen,
  CheckCircle2,
  XCircle,
  Loader2,
  Play,
  AlertTriangle,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Stat } from '../ui/DisplayPrimitives';

interface RLDatasetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const RLDatasetModal: React.FC<RLDatasetModalProps> = ({ isOpen, onClose }) => {
  const [pairs, setPairs] = useState<DPOPreferencePair[]>([]);
  const [stats, setStats] = useState<DPOStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'HUMAN' | 'BENCHMARK' | 'SAFETY'>('ALL');
  const [exporting, setExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [training, setTraining] = useState(false);
  const [trainMessage, setTrainMessage] = useState<string | null>(null);
  const [trainError, setTrainError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<any | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [showValidation, setShowValidation] = useState(false);

  const handleValidateGates = async () => {
    setIsValidating(true);
    try {
      const res = await fetch('/api/rl/train/validate');
      if (res.ok) {
        const data = await res.json();
        setValidationResult(data);
        setShowValidation(true);
      }
    } catch (err) {
      console.error('Validation fetch error:', err);
    } finally {
      setIsValidating(false);
    }
  };

  const fetchDataset = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/rl/dataset');
      if (res.ok) {
        const data = await res.json();
        setStats(data.statistics);
        setPairs(data.pairs || []);
      }
    } catch (err) {
      console.error('Failed to load DPO dataset:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchDataset();
    }
  }, [isOpen]);

  const handleExportJSONL = async () => {
    setExporting(true);
    setExportMessage(null);
    try {
      const res = await fetch('/api/rl/dataset/export', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setExportMessage(`Exported ${data.exported_count} pairs to ${data.filepath}`);
        setTimeout(() => setExportMessage(null), 5000);
      }
    } catch (err) {
      setExportMessage('Failed to export dataset. Check server logs.');
    } finally {
      setExporting(false);
    }
  };

  const handleManualTrain = async () => {
    if (!window.confirm('Trigger manual DPO model fine-tuning with verified preference pairs?')) {
      return;
    }
    setTraining(true);
    setTrainMessage(null);
    setTrainError(null);
    try {
      const res = await fetch('/api/rl/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ epochs: 4, dry_run: false }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Training failed' }));
        if (res.status === 503) {
          throw new Error(
            'Training temporarily disabled until Phase 5 data hygiene is complete (HTTP 503). Your reviews are saved — nothing is lost.'
          );
        }
        if (res.status === 422) {
          const detail = err.detail || {};
          setValidationResult(detail.validation || detail);
          setShowValidation(true);
          const failedGates = detail.validation?.failed_gates || [];
          throw new Error(
            `Training blocked by pre-training safety gates (${failedGates.join(', ') || 'Validation gates failed'}). Dataset remains unchanged.`
          );
        }
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Training failed. Check network or server configuration.');
      }
      const data = await res.json();
      setTrainMessage(`Model fine-tuning finished. Status: ${data.status}, Pairs: ${data.training_summary?.pairs_trained || data.pairs_trained || 0}, Output: ${data.manifest?.manifest_id || 'models/medgemma-dpo-lora'}`);
      setTimeout(() => setTrainMessage(null), 8000);
    } catch (err: any) {
      setTrainError(err.message || 'Manual fine-tuning failed. Please retry.');
      setTimeout(() => setTrainError(null), 8000);
    } finally {
      setTraining(false);
    }
  };

  if (!isOpen) return null;

  const filteredPairs = pairs.filter((p) => {
    if (filter === 'HUMAN') return p.source === 'HUMAN_PHYSICIAN';
    if (filter === 'BENCHMARK') return p.source === 'CALIBRATED_BENCHMARK';
    if (filter === 'SAFETY') return p.is_safety_critical;
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-[var(--ak-color-text-primary)]/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-6xl max-h-[92vh] bg-[var(--ak-color-bg-surface)] border border-[var(--ak-color-border-subtle)] rounded-2xl shadow-2xl flex flex-col overflow-hidden text-[var(--ak-color-text-primary)]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-subtle)] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--ak-color-primary-soft)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-primary)]">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-[var(--ak-color-text-primary)]">
                  RL / Direct Preference Optimization (DPO) Corpus
                </h2>
                <Badge variant="primary" size="sm">
                  TRL Compliant
                </Badge>
              </div>
              <p className="text-xs text-[var(--ak-color-text-muted)]">
                Reward-calibrated preference pairs synthesized from physician reviews and Harrison's ground truth.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              variant="primary"
              size="sm"
              onClick={handleManualTrain}
              disabled={training}
              leadingIcon={
                training ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current" />
                )
              }
              title="Manually trigger model fine-tuning with verified dataset"
            >
              {training ? 'Training model...' : 'Send Data for Training'}
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={handleValidateGates}
              disabled={isValidating}
              leadingIcon={
                isValidating ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <ShieldAlert className="w-3.5 h-3.5" />
                )
              }
              title="Run 14-point pre-training validation checklist without starting training"
            >
              {isValidating ? 'Auditing...' : 'Audit gates'}
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={handleExportJSONL}
              disabled={exporting}
              leadingIcon={
                exporting ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Download className="w-3.5 h-3.5" />
                )
              }
            >
              {exporting ? 'Exporting...' : 'Export JSONL'}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              title="Close modal"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Notifications */}
        {trainMessage && (
          <div className="px-6 py-2 bg-[var(--ak-color-success-soft)] border-b border-[var(--ak-color-border-subtle)] text-[var(--ak-color-success)] text-xs flex items-center gap-2 font-mono">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{trainMessage}</span>
          </div>
        )}

        {trainError && (
          <div data-testid="train-blocked-503" className="px-6 py-2 bg-[var(--ak-color-warning-soft)] border-b border-[var(--ak-color-border-subtle)] text-[var(--ak-color-danger)] text-xs flex items-center gap-2 font-mono">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{trainError}</span>
          </div>
        )}

        {/* Pre-Training 14-Gate Validation Result Panel */}
        {validationResult && showValidation && (
          <div className="px-6 py-3 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] font-mono text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--ak-color-border-subtle)] mb-2">
              <div className="flex items-center gap-2">
                <Badge variant={validationResult.passed ? 'success' : 'danger'} size="sm">
                  {validationResult.passed ? 'All 14 gates passed' : `${validationResult.gates_failed} of 14 gates blocked`}
                </Badge>
                <span className="text-[var(--ak-color-text-muted)] text-[11px]">
                  Evaluated {validationResult.eligible_records_count} eligible records
                </span>
              </div>
              <button
                onClick={() => setShowValidation(false)}
                className="text-[var(--ak-color-primary)] hover:underline text-[11px] cursor-pointer"
              >
                Dismiss
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
              {validationResult.gate_results?.map((g: any) => (
                <div
                  key={g.gate_id}
                  className={`p-2 rounded-lg border flex items-start gap-2 ${g.passed ? 'bg-[var(--ak-color-bg-surface)] border-[var(--ak-color-border-subtle)]' : 'bg-[var(--ak-color-warning-soft)] border-[var(--ak-color-border-subtle)] text-[var(--ak-color-danger)]'}`}
                >
                  {g.passed ? (
                    <CheckCircle2 className="w-4 h-4 text-[var(--ak-color-success)] shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="w-4 h-4 text-[var(--ak-color-danger)] shrink-0 mt-0.5" />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] font-semibold leading-tight flex items-center justify-between">
                      <span>Gate {g.gate_id}: {g.name}</span>
                      <Badge variant={g.passed ? 'success' : 'danger'} size="sm">
                        {g.passed ? 'Pass' : 'Fail'}
                      </Badge>
                    </p>
                    {g.failure_reason && (
                      <p className="text-[10px] text-[var(--ak-color-text-secondary)] mt-1 leading-normal">
                        {g.failure_reason}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {exportMessage && (
          <div className="px-6 py-2 bg-[var(--ak-color-success-soft)] border-b border-[var(--ak-color-border-subtle)] text-[var(--ak-color-success)] text-xs flex items-center gap-2 font-mono">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{exportMessage}</span>
          </div>
        )}

        {/* Alignment Stats Bar */}
        {stats && (
          <div className="px-6 py-3 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] grid grid-cols-2 sm:grid-cols-4 gap-3 shrink-0">
            <Stat label="Total preference pairs" value={stats.total_pairs} />
            <Stat label="Avg reward margin" value={`+${stats.average_reward_margin.toFixed(2)}`} />
            <Stat label="Safety violations" value={stats.safety_critical_count} />
            <Stat label="Foundation model" value="Clinical AI 4B" />
          </div>
        )}

        {/* Filter Navigation */}
        <div className="px-6 py-2.5 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] flex items-center justify-between text-xs shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="text-[var(--ak-color-text-muted)] font-medium mr-1 text-[11px]">Filter pairs:</span>
            {(['ALL', 'HUMAN', 'BENCHMARK', 'SAFETY'] as const).map((mode) => (
              <Button
                key={mode}
                variant={filter === mode ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setFilter(mode)}
              >
                {mode === 'ALL' && 'All pairs'}
                {mode === 'HUMAN' && `Physician reviews (${stats?.human_reviews_count || 0})`}
                {mode === 'BENCHMARK' && `Benchmark calibrations (${stats?.benchmark_calibrations_count || 0})`}
                {mode === 'SAFETY' && `Safety critical (${stats?.safety_critical_count || 0})`}
              </Button>
            ))}
          </div>

          <span className="text-[var(--ak-color-text-muted)] text-[11px] font-mono">
            Showing {filteredPairs.length} of {pairs.length} pairs
          </span>
        </div>

        {/* Scrollable Corpus List */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-[var(--ak-color-bg-app)]">
          {loading ? (
            <div className="h-48 flex items-center justify-center gap-2 text-[var(--ak-color-text-muted)] text-xs">
              <Loader2 className="w-5 h-5 animate-spin text-[var(--ak-color-primary)]" />
              <span>Compiling preference dataset...</span>
            </div>
          ) : filteredPairs.length === 0 ? (
            <div className="text-center py-12 text-[var(--ak-color-text-muted)] text-xs">
              No preference pairs match this filter criteria.
            </div>
          ) : (
            filteredPairs.map((pair) => (
              <div
                key={pair.id}
                className="rounded-xl border border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-surface)] overflow-hidden shadow-xs"
              >
                {/* Pair Header Banner */}
                <div className="px-4 py-2.5 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-[var(--ak-color-primary)]">
                      {pair.id}
                    </span>
                    <span className="text-xs font-semibold text-[var(--ak-color-text-primary)]">
                      {pair.case_id}
                    </span>
                    <span className="text-[var(--ak-color-border-subtle)] text-xs">•</span>
                    <span className="text-xs text-[var(--ak-color-text-muted)] font-mono">
                      {pair.source === 'CALIBRATED_BENCHMARK' ? 'Calibrated Harrison benchmark' : 'Human physician review'}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {pair.is_safety_critical && (
                      <Badge variant="danger" size="sm">
                        <ShieldAlert className="w-3 h-3 mr-1" />
                        Safety Critical
                      </Badge>
                    )}
                    <Badge variant="success" size="sm">
                      ΔR: +{pair.reward_margin.toFixed(2)}
                    </Badge>
                  </div>
                </div>

                {/* Prompt Vignette */}
                <div className="px-4 py-3 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)]">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--ak-color-text-muted)] mb-1">
                    Clinical scenario and history:
                  </p>
                  <p className="text-xs text-[var(--ak-color-text-primary)] leading-relaxed font-sans whitespace-pre-line">
                    {pair.prompt}
                  </p>
                </div>

                {/* Side-by-Side Chosen vs Rejected Response */}
                <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-[var(--ak-color-border-subtle)]">
                  {/* CHOSEN RESPONSE */}
                  <div className="p-4 bg-[var(--ak-color-bg-surface)]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5 text-[var(--ak-color-success)] font-semibold text-xs">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Chosen (Guideline-Adherent)</span>
                      </div>
                      <Badge variant="success" size="sm">
                        Reward: +{pair.reward_chosen.toFixed(2)}
                      </Badge>
                    </div>
                    <div className="text-xs text-[var(--ak-color-text-primary)] whitespace-pre-line font-sans leading-relaxed bg-[var(--ak-color-bg-subtle)] p-3 rounded-lg border border-[var(--ak-color-border-subtle)]">
                      {pair.chosen}
                    </div>
                  </div>

                  {/* REJECTED RESPONSE */}
                  <div className="p-4 bg-[var(--ak-color-bg-surface)]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5 text-[var(--ak-color-danger)] font-semibold text-xs">
                        <XCircle className="w-4 h-4" />
                        <span>Rejected (Suboptimal)</span>
                      </div>
                      <Badge variant="danger" size="sm">
                        Reward: {pair.reward_rejected.toFixed(2)}
                      </Badge>
                    </div>
                    <div className="text-xs text-[var(--ak-color-text-secondary)] whitespace-pre-line font-sans leading-relaxed bg-[var(--ak-color-bg-subtle)] p-3 rounded-lg border border-[var(--ak-color-border-subtle)]">
                      {pair.rejected}
                    </div>
                  </div>
                </div>

                {/* Evidence Citations Footer */}
                {pair.harrison_citations && pair.harrison_citations.length > 0 && (
                  <div className="px-4 py-2 bg-[var(--ak-color-bg-subtle)] border-t border-[var(--ak-color-border-subtle)] flex items-center gap-2 flex-wrap text-[11px]">
                    <span className="text-[var(--ak-color-text-muted)] flex items-center gap-1 font-medium">
                      <BookOpen className="w-3.5 h-3.5 text-[var(--ak-color-primary)]" />
                      <span>Harrison's textbook citations:</span>
                    </span>
                    {pair.harrison_citations.map((cite, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded bg-[var(--ak-color-bg-surface)] border border-[var(--ak-color-border-subtle)] text-[var(--ak-color-primary)] text-[10px] font-medium"
                      >
                        {cite}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
