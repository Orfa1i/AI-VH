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

  const currentCase = cases.find((c) => c.id === selectedCaseId) || cases[0];

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            {stationId === 'LABORATORY' && (
              <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-300 shadow-lg shadow-purple-500/10">
                <FlaskConical className="w-5 h-5" />
              </div>
            )}
            {stationId === 'RADIOLOGY' && (
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-300 shadow-lg shadow-indigo-500/10">
                <Radio className="w-5 h-5" />
              </div>
            )}
            {stationId === 'NURSE_STATION' && (
              <div className="w-10 h-10 rounded-xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-300 shadow-lg shadow-cyan-500/10">
                <HeartPulse className="w-5 h-5" />
              </div>
            )}
            <div>
              <h2 className="text-base font-bold text-slate-100">
                {stationId === 'LABORATORY' && 'Clinical Pathology & Automated Analyzers'}
                {stationId === 'RADIOLOGY' && 'Radiology Suite & Diagnostic PACS Console'}
                {stationId === 'NURSE_STATION' && 'Central Rotunda Triage & Intake Desk'}
              </h2>
              <p className="text-xs text-slate-400">
                {stationId === 'LABORATORY' && 'David Chen, MLS(ASCP) • Central Laboratory Workbench'}
                {stationId === 'RADIOLOGY' && 'Dr. Hayes, MD • High-Resolution CT Gantry & X-Ray Console'}
                {stationId === 'NURSE_STATION' && 'Sarah Jenkins, RN • Patient Intake & Triage Acuity Assessment'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5 overflow-y-auto">
          {/* LABORATORY VIEW */}
          {stationId === 'LABORATORY' && (
            <>
              <div className="p-4 rounded-xl bg-purple-950/30 border border-purple-800/50 text-xs text-purple-200 leading-relaxed">
                <div className="font-bold text-purple-300 mb-1 flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-purple-400" />
                  Automated High-Throughput Diagnostic Analyzers:
                </div>
                The Clinical Laboratory executes automated spectrophotometric and chemiluminescent biomarker assays for acute inpatient encounters.
              </div>

              <div>
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                  Active Clinical Assay Panels:
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-200">High-Sensitivity Troponin-I</div>
                      <div className="text-[11px] text-slate-400">Chemiluminescence Immunoassay</div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Online
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-200">Comprehensive Metabolic Panel (CMP)</div>
                      <div className="text-[11px] text-slate-400">ISE Ion-Selective Electrode (Na, K, Cl, CO2, BUN, Cr)</div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Online
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-200">Complete Blood Count (CBC) with Diff</div>
                      <div className="text-[11px] text-slate-400">Flow Cytometry / Impedance Counting</div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Online
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-200">Arterial Blood Gas (ABG) & Lactate</div>
                      <div className="text-[11px] text-slate-400">Point-of-Care Amperometric Sensor</div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Online
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* RADIOLOGY VIEW */}
          {stationId === 'RADIOLOGY' && (
            <>
              <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-800/50 text-xs text-indigo-200 leading-relaxed">
                <div className="font-bold text-indigo-300 mb-1 flex items-center gap-1.5">
                  <Radio className="w-4 h-4 text-indigo-400" />
                  Radiology Imaging & PACS Diagnostic Suite:
                </div>
                Equipped with a 64-slice helical CT scanner with sky-blue bore illumination, motorized patient couch, and shielded lead console.
              </div>

              <div>
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                  Imaging Modalities & Diagnostic Feeds:
                </h3>
                <div className="space-y-2">
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-200">12-Lead Electrocardiogram (ECG)</div>
                      <div className="text-[11px] text-slate-400">Real-time ST-segment elevation / depression analyzer</div>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold font-mono">
                      CALIBRATED
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-200">Chest Radiography (PA & Lateral)</div>
                      <div className="text-[11px] text-slate-400">Cardiomegaly, pulmonary edema, infiltrates, and pneumothorax screen</div>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold font-mono">
                      READY
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-200">Helical CT Angiography / Non-Contrast Head CT</div>
                      <div className="text-[11px] text-slate-400">High-resolution reconstruction with lead-glass workstation</div>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold font-mono">
                      STANDBY
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* NURSE STATION VIEW */}
          {stationId === 'NURSE_STATION' && (
            <>
              <div className="p-4 rounded-xl bg-cyan-950/30 border border-cyan-800/50 text-xs text-cyan-200 leading-relaxed">
                <div className="font-bold text-cyan-300 mb-1 flex items-center gap-1.5">
                  <HeartPulse className="w-4 h-4 text-cyan-400" />
                  Central Rotunda Nurse Station:
                </div>
                Sarah Jenkins, RN conducts patient triage, vital signs acquisition, and alerts Dr. Marcus Vance for examination.
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Current Inpatient Queue:</span>
                  <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-[10px] font-mono font-bold">
                    {currentCase.id} • {currentCase.name}
                  </span>
                </div>

                <div className="text-xs text-slate-300">
                  <span className="text-slate-400">Chief Complaint:</span> {currentCase.chief_complaint}
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => {
                      if (onRunEncounter) onRunEncounter();
                      onClose();
                    }}
                    disabled={isRunning}
                    className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-bold shadow-lg shadow-cyan-600/20 border border-cyan-400/40 flex items-center gap-2 cursor-pointer transition-all"
                  >
                    {isRunning ? (
                      <>
                        <Clock className="w-4 h-4 animate-spin" />
                        <span>Encounter Running...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 fill-white" />
                        <span>Simulate Complete Encounter</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
