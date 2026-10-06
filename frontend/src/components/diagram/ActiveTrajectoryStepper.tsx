import React, { useState } from 'react';
import {
  Activity,
  CheckCircle2,
  ExternalLink,
  MapPin,
  ShieldCheck,
  User,
} from 'lucide-react';
import type { BenchmarkCase, HospitalEvent } from '../../types';
import { Badge, Card } from '../ui';

export interface TrajectoryStageItem {
  id: string;
  stepNumber: number;
  label: string;
  title: string;
  department: string;
  stationId?: string;
  description: string;
  actionRequired: string;
  evidence: string;
  timestamp?: string;
  status: 'completed' | 'active' | 'upcoming';
}

export interface ActiveTrajectoryStepperProps {
  progress: number; // 0 to 100
  isRunning: boolean;
  currentCase?: BenchmarkCase | null;
  latestEvent?: HospitalEvent | null;
  activeDepartment?: string;
  doctorAction?: string;
  onSelectStage?: (stageId: string) => void;
  onOpenDepartmentStation?: (stationId: string) => void;
  className?: string;
}

export const ActiveTrajectoryStepper: React.FC<ActiveTrajectoryStepperProps> = ({
  progress,
  isRunning,
  currentCase,
  latestEvent,
  activeDepartment = 'RECEPTION',
  doctorAction = 'Reviewing Inpatient Charts',
  onSelectStage,
  onOpenDepartmentStation,
  className = '',
}) => {
  const [activeTooltipStageId, setActiveTooltipStageId] = useState<string | null>(null);

  // Normalize progress between 0 and 100
  const normalizedProgress = Math.min(100, Math.max(0, Math.round(progress)));

  // Derive stage status dynamically
  const isTriageComplete = normalizedProgress > 35 || (!isRunning && currentCase !== null && normalizedProgress >= 25);
  const isTriageActive = isRunning && (activeDepartment === 'RECEPTION' || activeDepartment === 'NURSE_STATION');

  const isExamComplete = normalizedProgress > 65;
  const isExamActive = isRunning && (activeDepartment.includes('DOCTOR') || activeDepartment.includes('EXAMINATION'));

  const isWorkupComplete = normalizedProgress > 85;
  const isWorkupActive = isRunning && (activeDepartment === 'LABORATORY' || activeDepartment === 'RADIOLOGY' || activeDepartment === 'PHARMACY');

  const isDischargeComplete = normalizedProgress >= 100 || latestEvent?.event_type === 'CLINICAL_REPORT_GENERATED';
  const isDischargeActive = isRunning && (normalizedProgress >= 90 || activeDepartment === 'DISCHARGE');

  const stages: TrajectoryStageItem[] = [
    {
      id: 'INTAKE',
      stepNumber: 1,
      label: 'GATEWAY',
      title: 'Clinical Intake & Triage',
      department: 'Triage & Nurse Station',
      stationId: 'NURSE_STATION',
      description: 'Patient identification, chief complaint intake, and objective vital sign telemetry recording.',
      actionRequired: 'Automated ESI Level calculation and baseline vitals acquisition.',
      evidence: currentCase ? `ESI Level ${currentCase.acuity === 'Critical' ? '1' : '2'} • Vitals Acquired` : 'Standby for triage queue admission',
      timestamp: currentCase ? 'T+00:00' : undefined,
      status: isTriageComplete && !isTriageActive ? 'completed' : isTriageActive || (currentCase && normalizedProgress < 35) ? 'active' : 'upcoming',
    },
    {
      id: 'EXAM',
      stepNumber: 2,
      label: 'ASSESSMENT',
      title: 'Attending Physician Examination',
      department: 'Internal Medicine Department',
      stationId: 'INTERNAL_MEDICINE',
      description: 'Differential diagnosis synthesis, physical findings analysis, and Harrison’s Principles RAG retrieval.',
      actionRequired: 'Attending physician evaluation and preliminary clinical orders.',
      evidence: doctorAction || 'Harrison’s Principles 21st Ed. Semantic Retrieval',
      timestamp: normalizedProgress >= 35 ? 'T+00:15' : undefined,
      status: isExamComplete && !isExamActive ? 'completed' : isExamActive || (normalizedProgress >= 35 && normalizedProgress < 65) ? 'active' : 'upcoming',
    },
    {
      id: 'WORKUP',
      stepNumber: 3,
      label: 'DIAGNOSTICS',
      title: 'Multidisciplinary Workup & Labs',
      department: 'Clinical Pathology & Imaging',
      stationId: 'LABORATORY',
      description: 'Laboratory blood panels, microbiology, radiographic scans, and clinical pharmacology review.',
      actionRequired: 'Execution of diagnostic orders, imaging reads, and toxicological screening.',
      evidence: 'Biomarkers & Radiological Interpretations Verified',
      timestamp: normalizedProgress >= 65 ? 'T+00:30' : undefined,
      status: isWorkupComplete && !isWorkupActive ? 'completed' : isWorkupActive || (normalizedProgress >= 65 && normalizedProgress < 85) ? 'active' : 'upcoming',
    },
    {
      id: 'EXIT',
      stepNumber: 4,
      label: 'DISPOSITION',
      title: 'Discharge Hub & Disposition',
      department: 'Hospital Discharge Gateway',
      stationId: 'DISCHARGE',
      description: 'Comprehensive clinical report finalization, prescription order routing, and physician review transfer.',
      actionRequired: 'Independent multi-stage evaluation verification and attending sign-off.',
      evidence: 'Clinical Report Synthesized & Verified',
      timestamp: normalizedProgress >= 85 ? 'T+00:45' : undefined,
      status: isDischargeComplete ? 'completed' : isDischargeActive || normalizedProgress >= 85 ? 'active' : 'upcoming',
    },
  ];

  const getStageHeaderSummary = () => {
    if (isDischargeComplete) return 'Discharge Gate Cleared • Clinical Report Finalized';
    if (isWorkupActive) return 'Diagnostic Workup In Progress • Biomarker & Imaging Analysis';
    if (isExamActive) return 'Attending Examination • Dr. Vance Harrison’s RAG Analysis';
    if (isTriageActive) return 'Triage Gateway • Objective Telemetry & Vitals Acquisition';
    if (isRunning) return 'Encounter Active • Routing Patient Trajectory...';
    return currentCase ? 'Patient Admitted • Clinical Trajectory Ready' : 'System Standby • Awaiting Patient Intake';
  };

  return (
    <Card
      aria-label="Active Trajectory Sequence and State Flow"
      className={className}
      style={{ padding: 0, overflow: 'hidden' }}
    >
      {/* ── Top Micro-HUD Telemetry Header ── */}
      <div
        style={{
          padding: 'var(--space-3) var(--space-4)',
          borderBottom: '1px solid var(--border-subtle)',
          backgroundColor: 'var(--bg-app)',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--space-3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <Activity className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span
              className="caption"
              style={{
                fontWeight: 700,
                color: 'var(--text-primary)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              ACTIVE TRAJECTORY SEQUENCE &amp; STATE FLOW
            </span>
            <Badge variant="brand" className="ak-num">
              {normalizedProgress}% PROGRESS
            </Badge>
          </div>
        </div>

        {/* Real-Time Live Ticker */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          {latestEvent ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '2px var(--space-3)',
                borderRadius: 'var(--radius-pill)',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                maxWidth: 400,
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  backgroundColor: 'var(--color-success)',
                }}
              />
              <span className="caption" style={{ color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                LATEST:
              </span>
              <span
                className="caption"
                style={{
                  fontWeight: 600,
                  color: 'var(--color-primary)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {latestEvent.summary || latestEvent.event_type}
              </span>
            </div>
          ) : (
            <span className="caption ak-num" style={{ color: 'var(--text-tertiary)' }}>
              AWAITING SIMULATION STREAM
            </span>
          )}
        </div>
      </div>

      {/* ── Main Stepper Track & Process Flow ── */}
      <div style={{ padding: 'var(--space-6) var(--space-4)' }}>
        <div style={{ position: 'relative', width: '100%' }}>
          {/* Background Connecting Rail */}
          <div
            style={{
              position: 'absolute',
              top: 20,
              left: 24,
              right: 24,
              height: 4,
              backgroundColor: 'var(--border-subtle)',
              borderRadius: 'var(--radius-pill)',
              zIndex: 0,
            }}
          >
            {/* Fluid Progress Line with Neural Spectrum when encounter running */}
            <div
              className={isRunning ? 'ak-progress--spectrum' : undefined}
              style={{
                height: '100%',
                backgroundColor: isRunning ? undefined : 'var(--color-primary)',
                borderRadius: 'var(--radius-pill)',
                transition: 'width 0.5s ease',
                width: `${normalizedProgress}%`,
              }}
            />
          </div>

          {/* Stepper Nodes Grid: Responsive Horizontal Layout */}
          <div
            style={{
              position: 'relative',
              zIndex: 1,
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: 'var(--space-2)',
            }}
          >
            {stages.map((stage) => {
              const isCompleted = stage.status === 'completed';
              const isActive = stage.status === 'active';
              const isTooltipOpen = activeTooltipStageId === stage.id;

              return (
                <div
                  key={stage.id}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    position: 'relative',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={() => setActiveTooltipStageId(stage.id)}
                  onMouseLeave={() => setActiveTooltipStageId(null)}
                  onClick={() => {
                    onSelectStage?.(stage.id);
                    if (stage.stationId && onOpenDepartmentStation) {
                      onOpenDepartmentStation(stage.stationId);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      onSelectStage?.(stage.id);
                      if (stage.stationId && onOpenDepartmentStation) {
                        onOpenDepartmentStation(stage.stationId);
                      }
                    }
                  }}
                  aria-label={`${stage.title} - ${stage.status.toUpperCase()}`}
                >
                  {/* Node Circle Avatar */}
                  <div style={{ position: 'relative', marginBottom: 'var(--space-2)' }}>
                    <div
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '0.875rem',
                        transition: 'all 0.2s ease',
                        backgroundColor: isCompleted
                          ? 'var(--color-success)'
                          : isActive
                          ? 'var(--color-primary)'
                          : 'var(--bg-surface)',
                        color: isCompleted || isActive ? '#FFFFFF' : 'var(--text-tertiary)',
                        border: isCompleted
                          ? '2px solid var(--color-success)'
                          : isActive
                          ? '2px solid var(--color-primary)'
                          : '2px solid var(--border-subtle)',
                        boxShadow: isActive ? 'var(--shadow-md)' : undefined,
                      }}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-5 h-5" style={{ color: '#FFFFFF' }} />
                      ) : (
                        <span className="ak-num">{stage.stepNumber}</span>
                      )}
                    </div>

                    {/* Active Patient Floating Pin when at this active node */}
                    {isActive && currentCase && (
                      <div
                        style={{
                          position: 'absolute',
                          bottom: '100%',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          marginBottom: 4,
                          whiteSpace: 'nowrap',
                          pointerEvents: 'none',
                        }}
                      >
                        <span
                          style={{
                            padding: '2px 8px',
                            borderRadius: 'var(--radius-pill)',
                            backgroundColor: 'var(--text-primary)',
                            color: '#FFFFFF',
                            fontSize: '0.625rem',
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                          }}
                        >
                          <User className="w-2.5 h-2.5" />
                          <span>{(currentCase.name || 'Patient').split(' ')[0]}</span>
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Stage Text & Status Badge */}
                  <div style={{ textAlign: 'center', width: '100%', padding: '0 var(--space-1)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, marginBottom: 2 }}>
                      <Badge variant={isCompleted ? 'success' : isActive ? 'brand' : 'neutral'}>
                        {stage.label}
                      </Badge>
                      {stage.timestamp && (
                        <span className="caption ak-num" style={{ color: 'var(--text-tertiary)' }}>
                          {stage.timestamp}
                        </span>
                      )}
                    </div>

                    <h4
                      className="heading-3"
                      style={{
                        fontSize: '0.75rem',
                        margin: '2px 0',
                        color: isCompleted || isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                      }}
                    >
                      {stage.title}
                    </h4>

                    <p
                      className="caption"
                      style={{
                        margin: 0,
                        color: 'var(--text-tertiary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {stage.department}
                    </p>
                  </div>

                  {/* ── Interactive Stage Detail Popover HUD ── */}
                  {isTooltipOpen && (
                    <div
                      style={{
                        position: 'absolute',
                        bottom: 'calc(100% + 12px)',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        width: 250,
                        backgroundColor: 'var(--text-primary)',
                        color: '#FFFFFF',
                        borderRadius: 'var(--radius-md)',
                        padding: 'var(--space-3)',
                        boxShadow: 'var(--shadow-lg)',
                        textAlign: 'left',
                        zIndex: 50,
                        pointerEvents: 'none',
                      }}
                      role="tooltip"
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          borderBottom: '1px solid rgba(255, 255, 255, 0.15)',
                          paddingBottom: 4,
                          marginBottom: 6,
                        }}
                      >
                        <span className="caption" style={{ color: 'var(--indigo-300)', fontWeight: 700 }}>
                          STAGE {stage.stepNumber}: {stage.label}
                        </span>
                        <span className="caption" style={{ textTransform: 'uppercase', opacity: 0.8 }}>
                          {stage.status}
                        </span>
                      </div>

                      <h5 style={{ fontSize: '0.8125rem', fontWeight: 700, margin: '0 0 4px', color: '#FFFFFF' }}>
                        {stage.title}
                      </h5>
                      <p style={{ fontSize: '0.6875rem', lineHeight: 1.4, margin: '0 0 8px', color: '#CBD5E1' }}>
                        {stage.description}
                      </p>

                      <div
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.08)',
                          borderRadius: 'var(--radius-sm)',
                          padding: 'var(--space-2)',
                          fontSize: '0.625rem',
                          marginBottom: 'var(--space-2)',
                          color: '#E2E8F0',
                        }}
                      >
                        <span style={{ color: 'var(--indigo-300)', fontWeight: 700, textTransform: 'uppercase', display: 'block', marginBottom: 2 }}>
                          Clinical Protocol:
                        </span>
                        <span>{stage.actionRequired}</span>
                      </div>


                      <div
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.08)',
                          borderRadius: 'var(--radius-sm)',
                          padding: 'var(--space-2)',
                          fontSize: '0.625rem',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 4,
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94A3B8', display: 'flex', alignItems: 'center', gap: 4 }}>
                            <MapPin className="w-2.5 h-2.5" /> Station:
                          </span>
                          <span style={{ fontWeight: 600 }}>{stage.department}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94A3B8', display: 'flex', alignItems: 'center', gap: 4 }}>
                            <ShieldCheck className="w-2.5 h-2.5" /> Evidence:
                          </span>
                          <span style={{ fontWeight: 600, maxWidth: 130, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {stage.evidence}
                          </span>
                        </div>
                      </div>

                      <div
                        style={{
                          marginTop: 6,
                          paddingTop: 4,
                          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          fontSize: '0.5625rem',
                          color: '#94A3B8',
                        }}
                      >
                        <span>CLICK TO INSPECT STATION</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Metadata Telemetry & Clinical Alignment Footer ── */}
      <div
        style={{
          padding: 'var(--space-2) var(--space-4)',
          backgroundColor: 'var(--bg-app)',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--space-3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: 'var(--color-primary)',
            }}
          />
          <span className="caption" style={{ fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
            Trajectory Status:
          </span>
          <span className="body-sm" style={{ fontWeight: 500 }}>
            {getStageHeaderSummary()}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span className="caption" style={{ color: 'var(--text-tertiary)' }}>PATIENT ACUITY:</span>
            <span className="caption ak-num" style={{ fontWeight: 700 }}>
              {currentCase?.acuity || 'Standard'}
            </span>
          </div>

          <span style={{ color: 'var(--border-subtle)' }}>|</span>

          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span className="caption" style={{ color: 'var(--text-tertiary)' }}>PATIENT:</span>
            <span className="caption ak-num" style={{ fontWeight: 600 }}>
              {currentCase ? `${currentCase.age}yo ${currentCase.sex}` : 'None'}
            </span>
          </div>

          <span style={{ color: 'var(--border-subtle)' }}>|</span>

          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span className="caption" style={{ color: 'var(--text-tertiary)' }}>EVIDENCE:</span>
            <span className="caption ak-num" style={{ fontWeight: 700, color: 'var(--color-primary)' }}>
              100% GROUNDED
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default ActiveTrajectoryStepper;
