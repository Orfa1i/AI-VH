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

  const currentCase = cases.find((c) => c.id === selectedCaseId) || (cases.length > 0 ? cases[0] : null);

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 text-slate-800">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-3">
            {stationId === 'LABORATORY' && (
              <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-700 shadow-xs">
                <FlaskConical className="w-5 h-5" />
              </div>
            )}
            {stationId === 'RADIOLOGY' && (
              <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-700 shadow-xs">
                <Radio className="w-5 h-5" />
              </div>
            )}
            {stationId === 'NURSE_STATION' && (
              <div className="w-10 h-10 rounded-xl bg-cyan-50 border border-cyan-200 flex items-center justify-center text-cyan-700 shadow-xs">
                <HeartPulse className="w-5 h-5" />
              </div>
            )}
            <div>
              <h2 className="text-base font-bold text-slate-900">
                {stationId === 'LABORATORY' && 'Clinical Pathology & Automated Analyzers'}
                {stationId === 'RADIOLOGY' && 'Radiology Suite & Diagnostic PACS Console'}
                {stationId === 'NURSE_STATION' && 'Central Rotunda Triage & Intake Desk'}
              </h2>
              <p className="text-xs text-slate-500">
                {stationId === 'LABORATORY' && 'David Chen, MLS(ASCP) • Central Laboratory Workbench'}
                {stationId === 'RADIOLOGY' && 'Dr. Hayes, MD • High-Resolution CT Gantry & X-Ray Console'}
                {stationId === 'NURSE_STATION' && 'Sarah Jenkins, RN • Patient Intake & Triage Acuity Assessment'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5 overflow-y-auto bg-white">
          {/* LABORATORY VIEW */}
          {stationId === 'LABORATORY' && (
            <>
              <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-200 text-xs text-purple-900 leading-relaxed">
                <div className="font-bold text-purple-800 mb-1 flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-purple-600" />
                  Automated High-Throughput Diagnostic Analyzers:
                </div>
                The Clinical Laboratory executes automated spectrophotometric and chemiluminescent biomarker assays for acute inpatient encounters.
              </div>

              <div>
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Active Clinical Assay Panels:
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-900">High-Sensitivity Troponin-I</div>
                      <div className="text-[11px] text-slate-500">Chemiluminescence Immunoassay</div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-800 border border-emerald-300 flex items-center gap-1 font-semibold">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Online
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-900">Comprehensive Metabolic Panel (CMP)</div>
                      <div className="text-[11px] text-slate-500">ISE Ion-Selective Electrode (Na, K, Cl, CO2, BUN, Cr)</div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-800 border border-emerald-300 flex items-center gap-1 font-semibold">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Online
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-900">Complete Blood Count (CBC) with Diff</div>
                      <div className="text-[11px] text-slate-500">Flow Cytometry / Impedance Counting</div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-800 border border-emerald-300 flex items-center gap-1 font-semibold">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Online
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-900">Arterial Blood Gas (ABG) & Lactate</div>
                      <div className="text-[11px] text-slate-500">Point-of-Care Amperometric Sensor</div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-800 border border-emerald-300 flex items-center gap-1 font-semibold">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Online
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* RADIOLOGY VIEW */}
          {stationId === 'RADIOLOGY' && (
            <>
              <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200 text-xs text-indigo-900 leading-relaxed">
                <div className="font-bold text-indigo-800 mb-1 flex items-center gap-1.5">
                  <Radio className="w-4 h-4 text-indigo-600" />
                  Radiology Imaging & PACS Diagnostic Suite:
                </div>
                Equipped with a 64-slice helical CT scanner with sky-blue bore illumination, motorized patient couch, and shielded lead console.
              </div>

              <div>
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Imaging Modalities & Diagnostic Feeds:
                </h3>
                <div className="space-y-2">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-900">12-Lead Electrocardiogram (ECG)</div>
                      <div className="text-[11px] text-slate-500">Real-time ST-segment elevation / depression analyzer</div>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-indigo-50 text-indigo-800 border border-indigo-300 text-[10px] font-bold font-mono">
                      CALIBRATED
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-900">Chest Radiography (PA & Lateral)</div>
                      <div className="text-[11px] text-slate-500">Cardiomegaly, pulmonary edema, infiltrates, and pneumothorax screen</div>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-indigo-50 text-indigo-800 border border-indigo-300 text-[10px] font-bold font-mono">
                      READY
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-900">Helical CT Angiography / Non-Contrast Head CT</div>
                      <div className="text-[11px] text-slate-500">High-resolution reconstruction with lead-glass workstation</div>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-indigo-50 text-indigo-800 border border-indigo-300 text-[10px] font-bold font-mono">
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
              <div className="p-4 rounded-xl bg-cyan-50/60 border border-cyan-200 text-xs text-cyan-900 leading-relaxed">
                <div className="font-bold text-cyan-800 mb-1 flex items-center gap-1.5">
                  <HeartPulse className="w-4 h-4 text-cyan-600" />
                  Central Rotunda Nurse Station:
                </div>
                Sarah Jenkins, RN conducts patient triage, vital signs acquisition, and alerts Dr. Marcus Vance for examination.
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                {currentCase ? (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-500">Current Inpatient Queue:</span>
                      <span className="px-2 py-0.5 rounded bg-cyan-50 text-cyan-800 border border-cyan-300 text-[10px] font-mono font-bold">
                        {currentCase.id} • {currentCase.name}
                      </span>
                    </div>

                    <div className="text-xs text-slate-700">
                      <span className="text-slate-500">Chief Complaint:</span> {currentCase.chief_complaint}
                    </div>

                    <div className="pt-2 flex justify-end">
                      <button
                        onClick={() => {
                          if (onRunEncounter) onRunEncounter();
                          onClose();
                        }}
                        disabled={isRunning}
                        className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-cyan-600/20 border border-cyan-500 flex items-center gap-2 cursor-pointer transition-all"
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
                  </>
                ) : (
                  <div className="text-center py-4 text-xs text-slate-500 font-mono">
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
