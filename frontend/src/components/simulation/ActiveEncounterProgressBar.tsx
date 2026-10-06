import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  CheckCircle2,
  Stethoscope,
  FlaskConical,
  FileCheck2,
  ChevronUp,
  ChevronDown,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { Badge, Button } from '../ui';

export interface ActiveEncounterProgressBarProps {
  isRunning: boolean;
  patientName?: string;
  encounterId?: string;
  activeStage?: string;
  onViewReport?: () => void;
  onDismiss?: () => void;
}

const MILESTONES = [
  { id: 'INTAKE', label: 'Intake & Vitals', target: 20, icon: Activity },
  { id: 'TRIAGE', label: 'Nurse Triage', target: 45, icon: Stethoscope },
  { id: 'EXAM', label: 'Doctor Exam & RAG', target: 70, icon: Sparkles },
  { id: 'LABS', label: 'Labs & Pharmacy', target: 90, icon: FlaskConical },
  { id: 'REPORT', label: 'Clinical Report', target: 100, icon: FileCheck2 },
];

export const ActiveEncounterProgressBar: React.FC<ActiveEncounterProgressBarProps> = ({
  isRunning,
  patientName = 'Active Encounter',
  encounterId,
  activeStage,
  onViewReport,
  onDismiss,
}) => {
  const [progress, setProgress] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const animationFrameRef = useRef<number | null>(null);
  const targetProgressRef = useRef(0);

  // Active progression simulation engine
  useEffect(() => {
    if (isRunning) {
      setIsCompleted(false);
      setProgress(5);
      targetProgressRef.current = 25;

      const timer1 = setTimeout(() => {
        targetProgressRef.current = 45;
      }, 700);

      const timer2 = setTimeout(() => {
        targetProgressRef.current = 70;
      }, 1500);

      const timer3 = setTimeout(() => {
        targetProgressRef.current = 90;
      }, 2400);

      const timer4 = setTimeout(() => {
        targetProgressRef.current = 100;
      }, 3300);

      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
        clearTimeout(timer4);
      };
    } else if (progress >= 95 || isCompleted) {
      targetProgressRef.current = 100;
    }
  }, [isRunning]);

  // Smooth frame interpolation
  useEffect(() => {
    const updateProgress = () => {
      setProgress((prev) => {
        const target = targetProgressRef.current;
        const diff = target - prev;
        if (Math.abs(diff) < 0.1) {
          if (target >= 100) {
            setIsCompleted(true);
          }
          return target;
        }
        const step = diff * 0.08;
        const next = prev + step;
        if (next >= 99.5 && target >= 100) {
          setIsCompleted(true);
          return 100;
        }
        animationFrameRef.current = requestAnimationFrame(updateProgress);
        return next;
      });
    };

    animationFrameRef.current = requestAnimationFrame(updateProgress);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isRunning]);

  if (!isRunning && !isCompleted && progress <= 0) {
    return null;
  }

  const roundedPct = Math.min(100, Math.round(progress));

  const getCurrentMilestoneLabel = () => {
    if (roundedPct >= 98) return 'Encounter complete — clinical report synthesized';
    if (roundedPct >= 85) return 'Pharmacy medication reconciliation & safety verification';
    if (roundedPct >= 65) return 'Medical Book RAG & specialist diagnostic evaluation';
    if (roundedPct >= 40) return 'Attending clinical examination & symptom synthesis';
    if (roundedPct >= 20) return 'Triage assessment & vital signs registration';
    return activeStage || 'Patient intake & bed allocation';
  };

  return (
    <div
      style={{
        width: '100%',
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-default)',
        padding: 'var(--space-2) var(--space-6)',
        boxShadow: 'var(--shadow-xs)',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* Top Header Row */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 'var(--radius-sm)',
                background: isCompleted ? 'var(--success-50)' : 'var(--indigo-50)',
                color: isCompleted ? 'var(--success-600)' : 'var(--indigo-500)',
                display: 'grid',
                placeItems: 'center',
                flexShrink: 0,
              }}
            >
              {isCompleted ? <CheckCircle2 aria-hidden="true" style={{ width: 16, height: 16 }} /> : <Activity aria-hidden="true" style={{ width: 16, height: 16 }} />}
            </div>

            <div style={{ minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="caption" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {patientName}
                </span>
                {encounterId && (
                  <span className="caption ak-num" style={{ color: 'var(--text-tertiary)' }}>
                    {encounterId}
                  </span>
                )}
                <Badge variant={isCompleted ? 'success' : 'ai'}>
                  {isCompleted ? 'Complete' : `${roundedPct}% live`}
                </Badge>
              </div>
              <p className="caption" style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
                {getCurrentMilestoneLabel()}
              </p>
            </div>
          </div>

          {/* Right Action Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {isCompleted && onViewReport && (
              <Button size="sm" variant="primary" onClick={onViewReport}>
                <span>View report</span>
                <ArrowRight aria-hidden="true" style={{ width: 14, height: 14 }} />
              </Button>
            )}

            <button
              type="button"
              className="ak-btn ak-btn--ghost ak-btn--sm ak-btn--icon"
              onClick={() => setIsCollapsed(!isCollapsed)}
              title={isCollapsed ? 'Expand Trajectory' : 'Collapse Trajectory'}
              aria-label={isCollapsed ? 'Expand Trajectory' : 'Collapse Trajectory'}
            >
              {isCollapsed ? <ChevronDown aria-hidden="true" style={{ width: 16, height: 16 }} /> : <ChevronUp aria-hidden="true" style={{ width: 16, height: 16 }} />}
            </button>

            {onDismiss && (
              <Button size="sm" variant="ghost" onClick={onDismiss}>
                Dismiss
              </Button>
            )}
          </div>
        </div>

        {/* Neural Spectrum Progress Bar */}
        <div style={{ marginTop: 8 }}>
          <div
            role="progressbar"
            aria-valuenow={roundedPct}
            aria-valuemin={0}
            aria-valuemax={100}
            className={`ak-progress ak-progress--sm ${isCompleted ? 'ak-progress--success' : 'ak-progress--spectrum'}`}
            style={{ '--value': `${roundedPct}%` } as React.CSSProperties}
          >
            <div className="ak-progress__bar" />
          </div>
        </div>

        {/* Milestones Row */}
        {!isCollapsed && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(5, 1fr)',
              gap: 8,
              marginTop: 10,
              paddingTop: 8,
              borderTop: '1px solid var(--border-default)',
            }}
          >
            {MILESTONES.map((step) => {
              const isPassed = roundedPct >= step.target;
              const isCurrent = roundedPct < step.target && roundedPct >= step.target - 25;
              const Icon = step.icon;

              return (
                <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div
                    style={{
                      width: 20,
                      height: 20,
                      borderRadius: 'var(--radius-xs)',
                      display: 'grid',
                      placeItems: 'center',
                      background: isPassed ? 'var(--success-50)' : isCurrent ? 'var(--indigo-50)' : 'var(--neutral-50)',
                      color: isPassed ? 'var(--success-600)' : isCurrent ? 'var(--indigo-500)' : 'var(--neutral-400)',
                      flexShrink: 0,
                    }}
                  >
                    <Icon aria-hidden="true" style={{ width: 12, height: 12 }} />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <span
                      className="caption"
                      style={{
                        display: 'block',
                        fontWeight: isPassed || isCurrent ? 600 : 400,
                        color: isPassed ? 'var(--text-primary)' : isCurrent ? 'var(--text-brand)' : 'var(--text-tertiary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {step.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
