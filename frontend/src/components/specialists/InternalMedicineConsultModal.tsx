import React, { useState, useEffect } from 'react';
import type { SpecialistConsultResponse } from '../../types';
import {
  Stethoscope,
  BookOpen,
  Send,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { speakClinicalMessage, stopClinicalSpeech } from '../../utils/speechSynthesis';

interface InternalMedicineConsultProps {
  isOpen: boolean;
  onClose: () => void;
}


const PRESET_SCENARIOS = [
  {
    title: 'Acute Chest Pain (NSTEMI)',
    scenario:
      '62-year-old male with severe substernal chest pressure radiating to left arm and jaw for 2 hours, diaphoresis, and nausea. History of HTN, diabetes, and smoking.',
    labs: ['Troponin-I 1.84 ng/mL (High)', 'ECG: 2mm ST-depression in leads V4-V6'],
  },
  {
    title: 'Diabetic Ketoacidosis (DKA)',
    scenario:
      '24-year-old female with Type 1 Diabetes presents with severe nausea, diffuse abdominal pain, persistent vomiting, and rapid Kussmaul respirations after missing insulin doses.',
    labs: ['Glucose 488 mg/dL', 'Arterial pH 7.14', 'Anion Gap 29 mEq/L', 'Urinary Ketones (4+)'],
  },
  {
    title: 'Acute Kidney Injury (AKI)',
    scenario:
      '71-year-old female with oliguria, weakness, and confusion following acute gastroenteritis and dehydration. On ACE-inhibitor therapy.',
    labs: ['Creatinine 3.8 mg/dL (Baseline 0.9)', 'BUN 64 mg/dL', 'Potassium 5.6 mEq/L'],
  },
];

export const InternalMedicineConsultModal: React.FC<InternalMedicineConsultProps> = ({
  isOpen,
  onClose,
}) => {
  const [scenario, setScenario] = useState(PRESET_SCENARIOS[0].scenario);
  const [labsInput, setLabsInput] = useState(PRESET_SCENARIOS[0].labs.join(', '));
  const [isLoading, setIsLoading] = useState(false);
  const [consultResult, setConsultResult] = useState<SpecialistConsultResponse | null>(null);
  const [expandedCitationIndex, setExpandedCitationIndex] = useState<number | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      stopClinicalSpeech();
      setIsSpeaking(false);
    }
  }, [isOpen]);

  const handleToggleSpeech = () => {
    if (isSpeaking) {
      stopClinicalSpeech();
      setIsSpeaking(false);
    } else if (consultResult) {
      const textToSpeak = `Dr. Marcus Vance, Internal Medicine consult. ${consultResult.evidence_brief.clinical_summary} Guideline therapy includes: ${consultResult.recommendations.guideline_therapy.join('. ')}.`;
      speakClinicalMessage(
        textToSpeak,
        'DR_VANCE',
        () => setIsSpeaking(true),
        () => setIsSpeaking(false)
      );
    }

  };

  if (!isOpen) return null;


  const handleRunConsult = async () => {
    if (!scenario.trim()) return;
    setIsLoading(true);
    try {
      const abnormalLabs = labsInput
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const res = await fetch('/api/specialists/internal-medicine/consult', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clinical_scenario: scenario,
          abnormal_labs: abnormalLabs,
        }),
      });

      if (!res.ok) throw new Error('Consultation request failed');
      const data: SpecialistConsultResponse = await res.json();
      setConsultResult(data);
    } catch (err) {
      console.error('Consultation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectPreset = (preset: (typeof PRESET_SCENARIOS)[0]) => {
    setScenario(preset.scenario);
    setLabsInput(preset.labs.join(', '));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-4xl rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden text-slate-200 animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-500/20 text-white font-bold">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100">
                  Internal Medicine Specialist & RAG Consult
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-bold font-mono">
                  DR. MARCUS VANCE, MD, FACP
                </span>
              </div>
              <div className="flex items-center gap-1 text-xs text-purple-400 mt-0.5">
                <BookOpen className="w-3.5 h-3.5" />
                <span>Harrison's Principles of Internal Medicine, 21st Edition (2022)</span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer text-sm"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Quick Presets */}
          <div>
            <span className="text-xs font-semibold text-slate-400 block mb-2">
              Select Clinical Vignette Preset:
            </span>
            <div className="flex flex-wrap gap-2">
              {PRESET_SCENARIOS.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectPreset(p)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 transition-all flex items-center gap-1.5 cursor-pointer"
                >
                  <Sparkles className="w-3 h-3 text-emerald-400" />
                  <span>{p.title}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Scenario Input & Labs Input */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Patient Presentation & History
              </label>
              <textarea
                rows={3}
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                placeholder="Enter patient chief complaint, HPI, and clinical findings..."
                className="w-full bg-slate-800/70 border border-slate-700 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Key Abnormal Labs / Imaging (comma-separated)
              </label>
              <textarea
                rows={3}
                value={labsInput}
                onChange={(e) => setLabsInput(e.target.value)}
                placeholder="e.g. Troponin 1.84, ST depression, Glucose 488..."
                className="w-full bg-slate-800/70 border border-slate-700 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors font-mono text-[11px]"
              />
            </div>
          </div>

          {/* Submit Consult Button */}
          <button
            onClick={handleRunConsult}
            disabled={isLoading || !scenario.trim()}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/25 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Searching Harrison's Internal Medicine 2022 & Synthesizing...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Consult Internal Medicine Specialist & Harrison's RAG</span>
              </>
            )}
          </button>

          {/* Consult Results View */}
          {consultResult && (
            <div className="space-y-5 pt-4 border-t border-slate-800 animate-in fade-in duration-300">
              {/* Evidence Brief Header */}
              <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/80">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-bold uppercase tracking-wider">
                      {consultResult.domain}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      Attending: {consultResult.specialist}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleToggleSpeech}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                        isSpeaking
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          : 'bg-slate-700/60 hover:bg-slate-700 text-slate-200 border border-slate-600'
                      }`}
                    >
                      {isSpeaking ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                      <span>{isSpeaking ? 'Stop Voice' : 'Dr. Vance Voice'}</span>
                    </button>
                    <span className="text-xs text-purple-400 font-mono flex items-center gap-1">
                      <BookOpen className="w-3.5 h-3.5" />
                      {consultResult.citations.length} Textbook Passages
                    </span>
                  </div>

                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-sans">
                  {consultResult.evidence_brief.clinical_summary}
                </p>
              </div>

              {/* 3 Columns: Workup, Therapy, Contraindications */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                {/* Immediate Workup */}
                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800">
                  <div className="flex items-center gap-2 font-bold text-sky-400 uppercase tracking-wider mb-2.5 text-[11px]">
                    <FileText className="w-4 h-4" /> Recommended Workup
                  </div>
                  <ul className="space-y-2">
                    {consultResult.recommendations.immediate_workup.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-slate-300 leading-snug">
                        <span className="text-sky-400 font-bold">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Guideline Therapy */}
                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800">
                  <div className="flex items-center gap-2 font-bold text-emerald-400 uppercase tracking-wider mb-2.5 text-[11px]">
                    <CheckCircle2 className="w-4 h-4" /> Guideline-Directed Therapy
                  </div>
                  <ul className="space-y-2">
                    {consultResult.recommendations.guideline_therapy.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-slate-300 leading-snug">
                        <span className="text-emerald-400 font-bold">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Contraindications & Pitfalls */}
                <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-900/40">
                  <div className="flex items-center gap-2 font-bold text-rose-400 uppercase tracking-wider mb-2.5 text-[11px]">
                    <AlertTriangle className="w-4 h-4" /> Contraindications & Pitfalls
                  </div>
                  <ul className="space-y-2">
                    {consultResult.recommendations.contraindications.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-rose-200/90 leading-snug">
                        <span className="text-rose-400 font-bold">✕</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Verified Textbook Citations */}
              <div>
                <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <BookOpen className="w-4 h-4" /> Verified Citations from Harrison's Internal
                  Medicine 21st Edition (2022)
                </h4>
                <div className="space-y-2">
                  {consultResult.citations.map((cit, idx) => {
                    const isExpanded = expandedCitationIndex === idx;
                    return (
                      <div
                        key={idx}
                        className="rounded-xl bg-purple-950/20 border border-purple-900/40 overflow-hidden text-xs"
                      >
                        <div
                          className="p-3 flex items-center justify-between cursor-pointer hover:bg-purple-900/20 transition-colors"
                          onClick={() => setExpandedCitationIndex(isExpanded ? null : idx)}
                        >
                          <div>
                            <span className="font-bold text-purple-200 block">
                              {cit.chapter}
                            </span>
                            <span className="text-[11px] text-purple-400 font-mono">
                              Page {cit.page} • Topic: {cit.topic}
                              {cit.relevance_score && ` • Score: ${cit.relevance_score}`}
                            </span>
                          </div>
                          <button className="text-purple-400">
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                        {isExpanded && (
                          <div className="p-3 pt-0 text-[11px] text-slate-300 italic border-t border-purple-900/30 bg-purple-950/30">
                            "{cit.text}"
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
