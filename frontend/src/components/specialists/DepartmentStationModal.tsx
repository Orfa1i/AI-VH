import React from 'react';
import {
  FlaskConical,
  Radio,
  HeartPulse,
  X,
  CheckCircle2,
  Clock,
  Play,
  Zap,
} from 'lucide-react';
import type { BenchmarkCase } from '../../types';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

interface DepartmentStationModalProps {
  stationId: string | null;
  isOpen: boolean;
  onClose: () => void;
  cases: BenchmarkCase[];
  selectedCaseId: string;
  onRunEncounter?: () => void;
  isRunning?: boolean;
}

export const DepartmentStationModal: React.FC<DepartmentStationModalProps> = ({
  stationId,
  isOpen,
  onClose,
  cases,
  selectedCaseId,
  onRunEncounter,
  isRunning,
}) => {
  if (!isOpen || !stationId) return null;

  const currentCase = cases.find((c) => c.id === selectedCaseId) || (cases.length > 0 ? cases[0] : null);

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[var(--ak-color-bg-surface)] border border-[var(--ak-color-border-subtle)] rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 text-[var(--ak-color-text-primary)]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[var(--ak-color-border-subtle)] flex items-center justify-between bg-[var(--ak-color-bg-subtle)]">
          <div className="flex items-center gap-3">
            {stationId === 'LABORATORY' && (
              <div className="w-10 h-10 rounded-xl bg-[var(--ak-color-primary-soft)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-primary)]">
                <FlaskConical className="w-5 h-5" />
              </div>
            )}
            {stationId === 'RADIOLOGY' && (
              <div className="w-10 h-10 rounded-xl bg-[var(--ak-color-primary-soft)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-primary)]">
                <Radio className="w-5 h-5" />
              </div>
            )}
            {stationId === 'NURSE_STATION' && (
              <div className="w-10 h-10 rounded-xl bg-[var(--ak-color-primary-soft)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-primary)]">
                <HeartPulse className="w-5 h-5" />
              </div>
            )}
            <div>
              <h2 className="text-base font-semibold text-[var(--ak-color-text-primary)]">
                {stationId === 'LABORATORY' && 'Clinical pathology and automated analyzers'}
                {stationId === 'RADIOLOGY' && 'Radiology suite and diagnostic PACS console'}
                {stationId === 'NURSE_STATION' && 'Central rotunda triage and intake desk'}
              </h2>
              <p className="text-xs text-[var(--ak-color-text-muted)]">
                {stationId === 'LABORATORY' && 'David Chen, MLS(ASCP) • Central laboratory workbench'}
                {stationId === 'RADIOLOGY' && 'Dr. Hayes, MD • High-resolution CT gantry and X-ray console'}
                {stationId === 'NURSE_STATION' && 'Sarah Jenkins, RN • Patient intake and triage acuity assessment'}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            title="Close modal"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5 overflow-y-auto bg-[var(--ak-color-bg-surface)]">
          {/* LABORATORY VIEW */}
          {stationId === 'LABORATORY' && (
            <>
              <div className="p-4 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs text-[var(--ak-color-text-primary)] leading-relaxed">
                <div className="font-semibold text-[var(--ak-color-text-primary)] mb-1 flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-[var(--ak-color-primary)]" />
                  Automated high-throughput diagnostic analyzers:
                </div>
                The clinical laboratory executes automated spectrophotometric and chemiluminescent biomarker assays for acute inpatient encounters.
              </div>

              <div>
                <h3 className="text-xs font-semibold text-[var(--ak-color-text-muted)] uppercase tracking-wider mb-2">
                  Active clinical assay panels:
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  <div className="p-3 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs flex items-center justify-between">
                    <div>
                      <div className="font-medium text-[var(--ak-color-text-primary)]">High-sensitivity Troponin-I</div>
                      <div className="text-[11px] text-[var(--ak-color-text-muted)]">Chemiluminescence immunoassay</div>
                    </div>
                    <Badge variant="success" size="sm">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Online
                    </Badge>
                  </div>

                  <div className="p-3 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs flex items-center justify-between">
                    <div>
                      <div className="font-medium text-[var(--ak-color-text-primary)]">Comprehensive Metabolic Panel (CMP)</div>
                      <div className="text-[11px] text-[var(--ak-color-text-muted)]">ISE Ion-Selective Electrode</div>
                    </div>
                    <Badge variant="success" size="sm">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Online
                    </Badge>
                  </div>

                  <div className="p-3 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs flex items-center justify-between">
                    <div>
                      <div className="font-medium text-[var(--ak-color-text-primary)]">Complete Blood Count (CBC)</div>
                      <div className="text-[11px] text-[var(--ak-color-text-muted)]">Flow cytometry counting</div>
                    </div>
                    <Badge variant="success" size="sm">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Online
                    </Badge>
                  </div>

                  <div className="p-3 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs flex items-center justify-between">
                    <div>
                      <div className="font-medium text-[var(--ak-color-text-primary)]">Arterial Blood Gas (ABG) & Lactate</div>
                      <div className="text-[11px] text-[var(--ak-color-text-muted)]">Point-of-care amperometric sensor</div>
                    </div>
                    <Badge variant="success" size="sm">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Online
                    </Badge>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* RADIOLOGY VIEW */}
          {stationId === 'RADIOLOGY' && (
            <>
              <div className="p-4 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs text-[var(--ak-color-text-primary)] leading-relaxed">
                <div className="font-semibold text-[var(--ak-color-text-primary)] mb-1 flex items-center gap-1.5">
                  <Radio className="w-4 h-4 text-[var(--ak-color-primary)]" />
                  Radiology imaging and PACS diagnostic suite:
                </div>
                Equipped with a 64-slice helical CT scanner with bore illumination, motorized couch, and shielded lead console.
              </div>

              <div>
                <h3 className="text-xs font-semibold text-[var(--ak-color-text-muted)] uppercase tracking-wider mb-2">
                  Imaging modalities and diagnostic feeds:
                </h3>
                <div className="space-y-2">
                  <div className="p-3 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs flex items-center justify-between">
                    <div>
                      <div className="font-medium text-[var(--ak-color-text-primary)]">12-Lead Electrocardiogram (ECG)</div>
                      <div className="text-[11px] text-[var(--ak-color-text-muted)]">ST-segment elevation analyzer</div>
                    </div>
                    <Badge variant="primary" size="sm">
                      Calibrated
                    </Badge>
                  </div>

                  <div className="p-3 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs flex items-center justify-between">
                    <div>
                      <div className="font-medium text-[var(--ak-color-text-primary)]">Chest Radiography (PA & Lateral)</div>
                      <div className="text-[11px] text-[var(--ak-color-text-muted)]">Cardiomegaly and infiltrates screen</div>
                    </div>
                    <Badge variant="primary" size="sm">
                      Ready
                    </Badge>
                  </div>

                  <div className="p-3 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs flex items-center justify-between">
                    <div>
                      <div className="font-medium text-[var(--ak-color-text-primary)]">Helical CT Angiography / Head CT</div>
                      <div className="text-[11px] text-[var(--ak-color-text-muted)]">High-resolution reconstruction</div>
                    </div>
                    <Badge variant="neutral" size="sm">
                      Standby
                    </Badge>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* NURSE STATION VIEW */}
          {stationId === 'NURSE_STATION' && (
            <>
              <div className="p-4 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-xs text-[var(--ak-color-text-primary)] leading-relaxed">
                <div className="font-semibold text-[var(--ak-color-text-primary)] mb-1 flex items-center gap-1.5">
                  <HeartPulse className="w-4 h-4 text-[var(--ak-color-primary)]" />
                  Central rotunda nurse station:
                </div>
                Sarah Jenkins, RN conducts patient triage, vital signs acquisition, and alerts Dr. Marcus Vance for examination.
              </div>

              <div className="p-4 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] space-y-3">
                {currentCase ? (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[var(--ak-color-text-muted)]">Current inpatient queue:</span>
                      <Badge variant="primary" size="sm">
                        {currentCase.id} • {currentCase.name}
                      </Badge>
                    </div>

                    <div className="text-xs text-[var(--ak-color-text-secondary)]">
                      <span className="text-[var(--ak-color-text-muted)]">Chief Complaint:</span> {currentCase.chief_complaint}
                    </div>

                    <div className="pt-2 flex justify-end">
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          if (onRunEncounter) onRunEncounter();
                          onClose();
                        }}
                        disabled={isRunning}
                        leadingIcon={
                          isRunning ? (
                            <Clock className="w-4 h-4 animate-spin" />
                          ) : (
                            <Play className="w-4 h-4 fill-white" />
                          )
                        }
                      >
                        {isRunning ? 'Encounter running...' : 'Simulate encounter'}
                      </Button>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-4 text-xs text-[var(--ak-color-text-muted)] font-mono">
                    No active patients in admission queue. Admit patients via Case Intake.
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
