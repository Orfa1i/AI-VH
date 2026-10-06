import React, { useState, useEffect } from 'react';
import type { SpecialistConsultResponse } from '../../types';
import {
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
  X,
} from 'lucide-react';
import { speakClinicalMessage, stopClinicalSpeech } from '../../utils/speechSynthesis';
import drMarcusPhoto from '../../assets/dr_marcus_vance.jpg';
import { Button } from '../ui/Button';
import { Badge, Chip } from '../ui/Badge';

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
  const [scenario, setScenario] = useState('');
  const [labsInput, setLabsInput] = useState('');
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--ak-color-text-primary)]/40 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="bg-[var(--ak-color-bg-surface)] border border-[var(--ak-color-border-subtle)] w-full max-w-4xl rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden text-[var(--ak-color-text-primary)] animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="p-5 border-b border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-subtle)] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="relative shrink-0">
              <img
                src={drMarcusPhoto}
                alt="Dr. Marcus Vance"
                className="w-11 h-11 rounded-xl object-cover object-top border border-[var(--ak-color-primary)] shadow-sm"
              />
              <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-[var(--ak-color-success)] border-2 border-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-[var(--ak-color-text-primary)]">
                  Internal medicine specialist and Harrison's consult
                </h2>
                <Badge variant="success" size="sm">
                  Dr. Marcus Vance, MD, FACP
                </Badge>
              </div>
              <div className="flex items-center gap-1 text-xs text-[var(--ak-color-text-muted)] mt-0.5 font-medium">
                <BookOpen className="w-3.5 h-3.5 text-[var(--ak-color-primary)]" />
                <span>Harrison's Principles of Internal Medicine, 21st Edition</span>
              </div>
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

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[var(--ak-color-bg-surface)]">
          {/* Quick Presets */}
          <div>
            <span className="text-xs font-semibold text-[var(--ak-color-text-muted)] block mb-2 font-mono">
              Optional reference vignettes:
            </span>
            <div className="flex flex-wrap gap-2">
              {PRESET_SCENARIOS.map((p, idx) => (
                <Chip
                  key={idx}
                  clickable
                  onClick={() => handleSelectPreset(p)}
                >
                  <Sparkles className="w-3 h-3 text-[var(--ak-color-primary)] mr-1 inline" />
                  <span>{p.title}</span>
                </Chip>
              ))}
            </div>
          </div>

          {/* Scenario Input & Labs Input */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-[var(--ak-color-text-primary)] mb-1">
                Patient presentation and history
              </label>
              <textarea
                rows={3}
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                placeholder="Enter patient chief complaint, history of present illness, and clinical findings..."
                className="w-full bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] focus:border-[var(--ak-color-primary)] rounded-xl p-3 text-xs text-[var(--ak-color-text-primary)] placeholder-[var(--ak-color-text-muted)] focus:outline-none transition-colors shadow-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--ak-color-text-primary)] mb-1">
                Key abnormal labs or imaging (comma-separated)
              </label>
              <textarea
                rows={3}
                value={labsInput}
                onChange={(e) => setLabsInput(e.target.value)}
                placeholder="e.g. Troponin 1.84, ST depression, Glucose 488..."
                className="w-full bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] focus:border-[var(--ak-color-primary)] rounded-xl p-3 text-xs text-[var(--ak-color-text-primary)] placeholder-[var(--ak-color-text-muted)] focus:outline-none transition-colors font-mono text-[11px] shadow-xs"
              />
            </div>
          </div>

          {/* Submit Consult Button */}
          <Button
            variant="primary"
            size="md"
            onClick={handleRunConsult}
            disabled={isLoading || !scenario.trim()}
            leadingIcon={
              isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin text-white" />
              ) : (
                <Send className="w-4 h-4" />
              )
            }
            className="w-full justify-center"
          >
            {isLoading
              ? "Searching Harrison's Internal Medicine guidelines..."
              : "Consult specialist"}
          </Button>

          {/* Consult Results View */}
          {consultResult && (
            <div className="space-y-5 pt-4 border-t border-[var(--ak-color-border-subtle)] animate-in fade-in duration-300">
              {/* Evidence Brief Header */}
              <div className="p-4 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)]">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="primary" size="sm">
                      {consultResult.domain}
                    </Badge>
                    <span className="text-xs text-[var(--ak-color-text-muted)] font-mono">
                      Attending: {consultResult.specialist}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleToggleSpeech}
                      leadingIcon={isSpeaking ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                    >
                      {isSpeaking ? 'Stop voice' : 'Dr. Vance voice'}
                    </Button>
                    <span className="text-xs text-[var(--ak-color-text-muted)] font-mono flex items-center gap-1">
                      <BookOpen className="w-3.5 h-3.5 text-[var(--ak-color-primary)]" />
                      {consultResult.citations.length} Textbook passages
                    </span>
                  </div>
                </div>
                <p className="text-xs text-[var(--ak-color-text-secondary)] leading-relaxed font-sans">
                  {consultResult.evidence_brief.clinical_summary}
                </p>
              </div>

              {/* 3 Columns: Workup, Therapy, Contraindications */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                {/* Immediate Workup */}
                <div className="p-4 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)]">
                  <div className="flex items-center gap-2 font-semibold text-[var(--ak-color-primary)] uppercase tracking-wider mb-2.5 text-[11px]">
                    <FileText className="w-4 h-4" /> Recommended workup
                  </div>
                  <ul className="space-y-2">
                    {consultResult.recommendations.immediate_workup.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-[var(--ak-color-text-secondary)] leading-snug">
                        <span className="text-[var(--ak-color-primary)] font-bold">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Guideline Therapy */}
                <div className="p-4 rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)]">
                  <div className="flex items-center gap-2 font-semibold text-[var(--ak-color-success)] uppercase tracking-wider mb-2.5 text-[11px]">
                    <CheckCircle2 className="w-4 h-4" /> Guideline-directed therapy
                  </div>
                  <ul className="space-y-2">
                    {consultResult.recommendations.guideline_therapy.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-[var(--ak-color-text-secondary)] leading-snug">
                        <span className="text-[var(--ak-color-success)] font-bold">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Contraindications & Pitfalls */}
                <div className="p-4 rounded-xl bg-[var(--ak-color-warning-soft)] border border-[var(--ak-color-border-subtle)]">
                  <div className="flex items-center gap-2 font-semibold text-[var(--ak-color-danger)] uppercase tracking-wider mb-2.5 text-[11px]">
                    <AlertTriangle className="w-4 h-4" /> Contraindications & pitfalls
                  </div>
                  <ul className="space-y-2">
                    {consultResult.recommendations.contraindications.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-[var(--ak-color-text-secondary)] leading-snug">
                        <span className="text-[var(--ak-color-danger)] font-bold">✕</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Verified Textbook Citations */}
              <div>
                <h4 className="text-xs font-semibold text-[var(--ak-color-text-primary)] uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <BookOpen className="w-4 h-4 text-[var(--ak-color-primary)]" /> Verified citations from Harrison's Internal Medicine 21st Edition
                </h4>
                <div className="space-y-2">
                  {consultResult.citations.map((cit, idx) => {
                    const isExpanded = expandedCitationIndex === idx;
                    return (
                      <div
                        key={idx}
                        className="rounded-xl bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] overflow-hidden text-xs"
                      >
                        <div
                          className="p-3 flex items-center justify-between cursor-pointer hover:bg-[var(--ak-color-bg-app)] transition-colors"
                          onClick={() => setExpandedCitationIndex(isExpanded ? null : idx)}
                        >
                          <div>
                            <span className="font-semibold text-[var(--ak-color-text-primary)] block">
                              {cit.chapter}
                            </span>
                            <span className="text-[11px] text-[var(--ak-color-text-muted)] font-mono">
                              Page {cit.page} • Topic: {cit.topic}
                              {cit.relevance_score && ` • Score: ${cit.relevance_score}`}
                            </span>
                          </div>
                          <button className="text-[var(--ak-color-text-muted)] hover:text-[var(--ak-color-text-primary)]">
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                        {isExpanded && (
                          <div className="p-3 pt-0 text-[11px] text-[var(--ak-color-text-secondary)] italic border-t border-[var(--ak-color-border-subtle)]">
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
