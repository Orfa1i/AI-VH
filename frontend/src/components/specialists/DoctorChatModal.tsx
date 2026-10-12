import React, { useState, useEffect, useRef, useMemo } from 'react';
import type { DoctorChatMessage, DoctorChatResponse } from '../../types';
import agentInternalMed from '../../assets/vh-agent-internal-medicine-512.png';
import agentSurgery from '../../assets/vh-agent-surgery-512.png';
import agentCardiology from '../../assets/vh-agent-cardiology-512.png';
import agentEmergency from '../../assets/vh-agent-emergency-512.png';
import agentNeurology from '../../assets/vh-agent-neurology-512.png';
import agentGynecology from '../../assets/vh-agent-gynecology-512.png';
import agentObstetrics from '../../assets/vh-agent-obstetrics-512.png';
import {
  Send,
  Loader2,
  Sparkles,
  BookOpen,
  Volume2,
  VolumeX,
  X,
  Trash2,
  AlertTriangle,
  Stethoscope,
  Activity,
  Cpu,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { speakClinicalMessage, stopClinicalSpeech } from '../../utils/speechSynthesis';
import { Button } from '../ui/Button';
import { Badge, Chip } from '../ui/Badge';

export interface DoctorChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientContext?: Record<string, any>;
  specialty?: string;
  doctorName?: string;
  agentKey?: string;
}

interface SpecialtyProfile {
  name: string;
  postNominals: string;
  shortName: string;
  roleTitle: string;
  bookTitle: string;
  avatar: string;
  voiceKey: string;
  streamEndpoint: string;
  syncEndpoint: string;
  starterPrompts: { title: string; prompt: string }[];
  greetingText: string;
  placeholderText: string;
  analyzingText: string;
}

const SURGERY_PROFILE: SpecialtyProfile = {
  name: 'Dr. Sarah Lin',
  postNominals: 'MD, FACS',
  shortName: 'Dr. Lin',
  roleTitle: 'Lead Attending Surgeon, General & Acute Care Surgery',
  bookTitle: "Schwartz's Principles of Surgery (10th Ed)",
  avatar: agentSurgery,
  voiceKey: 'DR_LIN',
  streamEndpoint: '/api/specialists/surgery/chat/stream',
  syncEndpoint: '/api/specialists/surgery/chat',
  starterPrompts: [
    {
      title: 'Acute Appendicitis',
      prompt: 'Dr. Lin, for a 28yo with acute RLQ pain, migratory periumbilical pain, and leukocytosis (14,500), what are the diagnostic criteria, ultrasound/CT indications, and operative timing in Schwartz?',
    },
    {
      title: 'Small Bowel Obstruction',
      prompt: 'What are the clinical, radiographic, and laboratory signs in Schwartz that mandate immediate exploratory laparotomy vs conservative decompression in small bowel obstruction?',
    },
    {
      title: 'Acute Cholecystitis',
      prompt: 'According to Schwartz and Tokyo guidelines, what is the optimal surgical timing for acute calculous cholecystitis, and how are high-risk or delayed presentations handled?',
    },
    {
      title: 'Strangulated Hernia',
      prompt: 'A 67-year-old male presents with tender, irreducible groin swelling with overlying erythema and fever. What are the urgent surgical management steps and contraindications to forceful taxis?',
    },
  ],
  greetingText:
    "Greetings. I am Dr. Sarah Lin, MD, FACS, Lead Attending Surgeon. My surgical decision-making and operative guidance are grounded directly in Schwartz's Principles of Surgery (10th Edition).\n\nHow may I assist you with acute abdominal evaluations, operative indications, surgical contraindications, or perioperative management today?",
  placeholderText:
    "Ask Dr. Lin about acute surgical cases, operative indications, or Schwartz's guidelines...",
  analyzingText: "Dr. Lin is analyzing Schwartz's Principles of Surgery and operative indications...",
};

const CARDIOLOGY_PROFILE: SpecialtyProfile = {
  name: 'Dr. Rachel Vance',
  postNominals: 'MD, FACC',
  shortName: 'Dr. Rachel Vance',
  roleTitle: 'Attending Cardiologist, Cardiovascular Medicine',
  bookTitle: "Braunwald's Heart Disease (12th Ed)",
  avatar: agentCardiology,
  voiceKey: 'DR_RACHEL_VANCE',
  streamEndpoint: '/api/specialists/cardiology/chat/stream',
  syncEndpoint: '/api/specialists/cardiology/chat',
  starterPrompts: [
    {
      title: 'NSTEMI Protocol',
      prompt: 'What is the emergent diagnostic workup and initial guideline-directed medical therapy for acute retrosternal chest pressure and elevated troponin in Braunwald?',
    },
    {
      title: 'Atrial Fibrillation RVR',
      prompt: 'For hemodynamically stable new-onset AF with rapid ventricular response (HR 145), what are the rate control and anticoagulation protocols according to Braunwald?',
    },
    {
      title: 'Acute Decompensated HF',
      prompt: 'What are the volume assessment, loop diuretic escalation, and vasodilator titration guidelines in Braunwald for acute pulmonary edema?',
    },
    {
      title: 'Cardiogenic Shock',
      prompt: 'How do you differentiate SCAI shock stages and initiate inotrope versus mechanical circulatory support according to Braunwald?',
    },
  ],
  greetingText:
    "Greetings. I am Dr. Rachel Vance, MD, FACC, Attending Cardiologist. My cardiovascular reasoning is grounded directly in Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine (12th Edition).\n\nHow may I assist you with acute coronary syndromes, arrhythmias, heart failure, hemodynamic management, or valvular disease today?",
  placeholderText:
    "Ask Dr. Rachel Vance about cardiac cases, ECG findings, or Braunwald's guidelines...",
  analyzingText: "Dr. Rachel Vance is analyzing Braunwald's cardiovascular knowledge and guidelines...",
};

const INTERNAL_MEDICINE_PROFILE: SpecialtyProfile = {
  name: 'Dr. Marcus Vance',
  postNominals: 'MD, FACP',
  shortName: 'Dr. Vance',
  roleTitle: 'Chief Attending Physician, Internal Medicine',
  bookTitle: "Harrison's Principles of Internal Medicine (21st Ed)",
  avatar: agentInternalMed,
  voiceKey: 'DR_VANCE',
  streamEndpoint: '/api/specialists/internal-medicine/chat/stream',
  syncEndpoint: '/api/specialists/internal-medicine/chat',
  starterPrompts: [
    {
      title: 'NSTEMI Protocol',
      prompt: 'Doctor Vance, what is the emergent diagnostic workup and initial guideline-directed medical therapy for a 62yo male with acute retrosternal chest pressure and elevated troponin?',
    },
    {
      title: 'DKA & Potassium Safety',
      prompt: '24-year-old with Type 1 Diabetes presents with severe DKA, anion gap 29, and pH 7.14. What are the strict rules for initiating intravenous insulin with respect to serum potassium?',
    },
    {
      title: 'PE Thrombolysis Contraindications',
      prompt: 'What are the absolute and relative contraindications to systemic thrombolysis (tPA) in submassive PE, particularly regarding recent gastrointestinal bleeding?',
    },
    {
      title: 'Acute Kidney Injury',
      prompt: 'Patient with dehydration on ACE inhibitor presents with acute oliguria and potassium 5.6 mEq/L. How should I categorize and manage this acute kidney injury?',
    },
  ],
  greetingText:
    "Greetings. I am Dr. Marcus Vance, Chief Attending Physician of Internal Medicine. My clinical reasoning is grounded in Harrison's Principles of Internal Medicine (21st Edition) and internal medicine clinical guidance models.\n\nHow may I assist you with clinical cases, differential diagnoses, evidence-based therapies, or medication contraindications today?",
  placeholderText:
    "Ask Dr. Vance about clinical cases, differential diagnoses, or Harrison's guidelines...",
  analyzingText: "Dr. Vance is analyzing Harrison's clinical knowledge and guidelines...",
};

const EMERGENCY_PROFILE: SpecialtyProfile = {
  name: 'Dr. David Kim',
  postNominals: 'MD, FACEP',
  shortName: 'Dr. David Kim',
  roleTitle: 'Lead Attending Physician, Emergency Medicine & Trauma Resuscitation',
  bookTitle: "Tintinalli's Emergency Medicine Manual",
  avatar: agentEmergency,
  voiceKey: 'DR_KIM',
  streamEndpoint: '/api/specialists/emergency/chat/stream',
  syncEndpoint: '/api/specialists/emergency/chat',
  starterPrompts: [
    {
      title: 'Acute Anaphylaxis',
      prompt: 'Dr. Kim, for severe acute anaphylaxis with stridor, hypotension (BP 82/50), and diffuse urticaria, what is the exact intramuscular epinephrine dose, concentration, injection site, and refractory escalation protocol in Tintinalli?',
    },
    {
      title: 'Airway RSI & Pre-oxygenation',
      prompt: 'What is the rapid sequence intubation (RSI) protocol, preoxygenation strategy, and induction/paralytic dosing in Tintinalli for a critically hypoxic patient with acute respiratory failure?',
    },
    {
      title: 'Tension Pneumothorax',
      prompt: 'For a patient with acute hypotension, absent breath sounds on the right, and tracheal deviation, what is the immediate needle decompression landmark and definitive tube thoracostomy management in Tintinalli?',
    },
    {
      title: 'Septic Shock Resuscitation',
      prompt: 'According to Tintinalli, what are the initial crystalloid resuscitation volume (30 mL/kg), target MAP goals, and first-line vasopressor selection in septic shock refractory to fluid administration?',
    },
  ],
  greetingText:
    "Greetings. I am Dr. David Kim, MD, FACEP, Lead Attending Physician in Emergency Medicine and Trauma Resuscitation. My clinical management and critical intervention protocols are grounded directly in Tintinalli's Emergency Medicine Manual.\n\nHow may I assist you with acute resuscitation, airway emergencies, anaphylaxis, trauma stabilization, toxicology, or emergent clinical decision-making today?",
  placeholderText:
    "Ask Dr. Kim about resuscitation protocols, airway, or Tintinalli's guidelines...",
  analyzingText: "Dr. David Kim is analyzing Tintinalli's Emergency Medicine resuscitation protocols and guidelines...",
};

const INFECTIOUS_DISEASES_PROFILE: SpecialtyProfile = {
  name: 'Dr. Anthony Mercer',
  postNominals: 'MD, FIDSA',
  shortName: 'Dr. Mercer',
  roleTitle: 'Attending Physician, Infectious Diseases & Antimicrobial Stewardship',
  bookTitle: "Harrison's Infectious Diseases (Fauci & Kasper)",
  avatar: agentInternalMed,
  voiceKey: 'DR_MERCER',
  streamEndpoint: '/api/specialists/infectious-diseases/chat/stream',
  syncEndpoint: '/api/specialists/infectious-diseases/chat',
  starterPrompts: [
    {
      title: 'Septic Shock & Empiric Regimen',
      prompt: 'What is the guideline-directed empiric antimicrobial regimen for suspected gram-negative bacteremia and septic shock with unknown source in a neutropenic host?',
    },
    {
      title: 'Fever of Unknown Origin (FUO)',
      prompt: 'What are the diagnostic criteria, initial diagnostic workup (blood cultures, imaging, inflammatory markers), and rules regarding empiric antibiotics in classical FUO?',
    },
    {
      title: 'Infective Endocarditis',
      prompt: 'For suspected native-valve subacute bacterial endocarditis meeting modified Duke criteria, what are the blood culture protocols and empiric antibiotic combinations before MIC returns?',
    },
    {
      title: 'Hospital-Acquired Pneumonia (HAP)',
      prompt: 'What are the empiric coverage guidelines for MRSA and Pseudomonas aeruginosa in hospital-acquired pneumonia according to IDSA/ATS guidelines?',
    },
  ],
  greetingText:
    "Greetings. I am Dr. Anthony Mercer, MD, FIDSA, Attending Physician in Infectious Diseases and Antimicrobial Stewardship. My clinical reasoning and antimicrobial guidance are grounded directly in Harrison's Infectious Diseases (Fauci & Kasper).\n\nHow may I assist you with diagnostic workup, targeted antimicrobial selection, fever of unknown origin, sepsis protocols, or pathogen resistance today?",
  placeholderText:
    "Ask Dr. Mercer about antimicrobial therapy, sepsis protocols, or Harrison's ID guidance...",
  analyzingText: "Dr. Anthony Mercer is analyzing Harrison's Infectious Diseases protocols and antimicrobial regimens...",
};

const GYNECOLOGY_PROFILE: SpecialtyProfile = {
  name: 'Dr. Evelyn Reed',
  postNominals: 'MD, FACOG',
  shortName: 'Dr. Reed',
  roleTitle: 'Attending Physician, Gynecology & Minimally Invasive Pelvic Surgery',
  bookTitle: 'Williams Gynecology',
  avatar: agentGynecology,
  voiceKey: 'DR_REED',
  streamEndpoint: '/api/specialists/gynecology/chat/stream',
  syncEndpoint: '/api/specialists/gynecology/chat',
  starterPrompts: [
    {
      title: 'AUB & FIGO PALM-COEIN',
      prompt: 'For a 42yo woman with heavy menstrual bleeding and iron deficiency anemia, how should we systematically evaluate structural vs non-structural causes using PALM-COEIN and when is endometrial biopsy indicated in Williams Gynecology?',
    },
    {
      title: 'Ectopic Pregnancy & hCG Triage',
      prompt: 'What are the beta-hCG discriminatory zone rules, ultrasound criteria, and contraindications for medical management with methotrexate in suspected ectopic pregnancy according to Williams Gynecology?',
    },
    {
      title: 'Acute PID & Inpatient Criteria',
      prompt: 'What are the diagnostic thresholds for acute pelvic inflammatory disease (PID), and what clinical presentations mandate immediate inpatient admission and parenteral antibiotics?',
    },
    {
      title: 'Endometriosis Management',
      prompt: 'What is the recommended stepwise medical and surgical management algorithm for severe cyclic dysmenorrhea and suspected deep infiltrating endometriosis in Williams Gynecology?',
    },
  ],
  greetingText:
    "Greetings. I am Dr. Evelyn Reed, MD, FACOG, Attending Gynecologist. My clinical and surgical reasoning is grounded directly in Williams Gynecology.\n\nHow may I assist you with abnormal uterine bleeding, pelvic pain, ectopic pregnancy, adnexal masses, or gynecologic surgical planning today?",
  placeholderText:
    "Ask Dr. Evelyn Reed about gynecologic conditions, PALM-COEIN, or Williams Gynecology...",
  analyzingText: "Dr. Evelyn Reed is analyzing Williams Gynecology evidence and clinical algorithms...",
};

const NEUROLOGY_PROFILE: SpecialtyProfile = {
  name: 'Dr. Alexander Hayes',
  postNominals: 'MD, PhD, FAAN',
  shortName: 'Dr. Hayes',
  roleTitle: 'Attending Neurologist, Comprehensive Stroke Center & Clinical Neurophysiology',
  bookTitle: "Adams and Victor's Principles of Neurology (8th Edition)",
  avatar: agentNeurology,
  voiceKey: 'DR_ALEXANDER_HAYES',
  streamEndpoint: '/api/specialists/neurology/chat/stream',
  syncEndpoint: '/api/specialists/neurology/chat',
  starterPrompts: [
    {
      title: 'Acute Ischemic Stroke & tPA / EVT',
      prompt: 'For a 64yo patient presenting with sudden right hemiparesis and aphasia (NIHSS 16, last known normal 2.5 hours ago), outline the emergency neuroimaging protocol, thrombolytic criteria, and indications for mechanical thrombectomy according to Adams and Victor\'s Principles of Neurology.',
    },
    {
      title: 'Status Epilepticus Escalation',
      prompt: 'What is the staged pharmacological escalation algorithm for generalized convulsive status epilepticus refractory to initial IV benzodiazepines according to Adams and Victor\'s Principles of Neurology?',
    },
    {
      title: 'Myasthenic Crisis vs Cholinergic Crisis',
      prompt: 'How do you differentiate a myasthenic crisis from a cholinergic crisis, what bedside respiratory parameters (FVC/NIF) mandate mechanical ventilation, and what medications are strictly contraindicated?',
    },
    {
      title: 'Subarachnoid Hemorrhage & LP Timing',
      prompt: 'When evaluating a thunderclap headache with a normal non-contrast head CT, what is the optimal timing and diagnostic criteria for lumbar puncture and CSF xanthochromia in Adams and Victor\'s Principles of Neurology?',
    },
  ],
  greetingText:
    "Greetings. I am Dr. Alexander Hayes, MD, PhD, FAAN, Attending Neurologist. My clinical and diagnostic reasoning is grounded directly in Adams and Victor's Principles of Neurology (8th Edition).\n\nHow may I assist you with acute stroke evaluation, seizures and status epilepticus, neuromuscular emergencies, coma assessment, or complex neuro-critical care today?",
  placeholderText:
    "Ask Dr. Alexander Hayes about acute stroke, seizures, or Adams and Victor's guidelines...",
  analyzingText: "Dr. Alexander Hayes is analyzing Adams and Victor's Principles of Neurology and clinical neurophysiology...",
};

const OBSTETRICS_PROFILE: SpecialtyProfile = {
  name: 'Dr. Evelyn Reed',
  postNominals: 'MD, FACOG',
  shortName: 'Dr. Reed',
  roleTitle: 'Attending Physician, Maternal-Fetal Medicine & Obstetrics',
  bookTitle: 'Williams Obstetrics (26th Ed)',
  avatar: agentObstetrics,
  voiceKey: 'DR_REED',
  streamEndpoint: '/api/specialists/obstetrics/chat/stream',
  syncEndpoint: '/api/specialists/obstetrics/chat',
  starterPrompts: [
    {
      title: 'Preeclampsia with Severe Features',
      prompt: 'For a 34-week gestation patient with BP 168/112 and severe persistent headache, what is the emergent magnesium sulfate neuroprotection protocol and antihypertensive titration in Williams Obstetrics?',
    },
    {
      title: 'Postpartum Hemorrhage (PPH)',
      prompt: 'What are the stepwise uterotonic escalation steps (oxytocin, methergine, carboprost, misoprostol) and intrauterine balloon tamponade indications in Williams Obstetrics?',
    },
    {
      title: 'Premature Rupture of Membranes',
      prompt: 'What are the latency antibiotic regimens, GBS prophylaxis criteria, and delivery timing thresholds for preterm PROM according to Williams Obstetrics?',
    },
    {
      title: 'Gestational Diabetes Mellitus',
      prompt: 'What are the diagnostic thresholds for the 3-hour 100g OGTT and first-line glycemic targets in Williams Obstetrics?',
    },
  ],
  greetingText:
    "Greetings. I am Dr. Evelyn Reed, MD, FACOG, Attending Obstetrician. My clinical and obstetrical management protocols are grounded directly in Williams Obstetrics (26th Edition).\n\nHow may I assist you with high-risk pregnancy, preeclampsia, fetal monitoring, or postpartum complications today?",
  placeholderText:
    "Ask Dr. Reed about obstetrical conditions, preeclampsia, or Williams Obstetrics...",
  analyzingText: "Dr. Evelyn Reed is analyzing Williams Obstetrics evidence and maternal-fetal algorithms...",
};

const getSpecialistProfile = (specialty?: string, agentKey?: string): SpecialtyProfile => {
  const normKey = (agentKey || '').toLowerCase();
  const normSpec = (specialty || '').toUpperCase();

  if (normKey === 'su' || normSpec === 'SURGERY') {
    return SURGERY_PROFILE;
  }
  if (normKey === 'ca' || normSpec === 'CARDIOLOGY') {
    return CARDIOLOGY_PROFILE;
  }
  if (normKey === 'em' || normSpec === 'EMERGENCY' || normSpec === 'EMERGENCY_MEDICINE') {
    return EMERGENCY_PROFILE;
  }
  if (normKey === 'ob' || normSpec === 'OBSTETRICS' || normSpec === 'OB') {
    return OBSTETRICS_PROFILE;
  }
  if (normKey === 'id' || normSpec === 'INFECTIOUS_DISEASES' || normSpec === 'INFECTIOUS DISEASES') {
    return INFECTIOUS_DISEASES_PROFILE;
  }
  if (normKey === 'gy' || normSpec === 'GYNECOLOGY' || normSpec === 'GYN') {
    return GYNECOLOGY_PROFILE;
  }
  if (normKey === 'ne' || normSpec === 'NEUROLOGY' || normSpec === 'NEURO') {
    return NEUROLOGY_PROFILE;
  }
  return INTERNAL_MEDICINE_PROFILE;
};

const buildInitialGreeting = (profile: SpecialtyProfile): DoctorChatMessage => ({
  id: `msg-welcome-${profile.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}`,
  sender: 'DOCTOR',
  content: profile.greetingText,
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  telemetry: {
    live_gpu_inference: true,
    model: 'Clinical AI 4B (NF4 LoRA Aligned)',
    knowledge_source: profile.bookTitle,
    latency_ms: 0,
  },
});

export const DoctorChatModal: React.FC<DoctorChatModalProps> = ({
  isOpen,
  onClose,
  patientContext,
  specialty,
  doctorName,
  agentKey,
}) => {
  const profile = useMemo(() => getSpecialistProfile(specialty, agentKey), [specialty, agentKey]);

  const [messages, setMessages] = useState<DoctorChatMessage[]>([buildInitialGreeting(profile)]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isOpen) {
      setMessages([buildInitialGreeting(profile)]);
      setTimeout(() => inputRef.current?.focus(), 150);
    } else {
      stopClinicalSpeech();
      setSpeakingMessageId(null);
    }
  }, [isOpen, profile]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (!isOpen) return null;

  const toggleCitations = (msgId: string) => {
    setExpandedCitations((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleToggleSpeech = (msg: DoctorChatMessage) => {
    if (speakingMessageId === msg.id) {
      stopClinicalSpeech();
      setSpeakingMessageId(null);
    } else {
      stopClinicalSpeech();
      setSpeakingMessageId(msg.id);
      speakClinicalMessage(
        msg.content,
        profile.voiceKey,
        () => setSpeakingMessageId(msg.id),
        () => setSpeakingMessageId(null)
      );
    }
  };

  const handleClearHistory = () => {
    stopClinicalSpeech();
    setSpeakingMessageId(null);
    setMessages([buildInitialGreeting(profile)]);
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputText).trim();
    if (!query || isLoading) return;

    const userMessage: DoctorChatMessage = {
      id: `msg-user-${Date.now()}`,
      sender: 'USER',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    const doctorMsgId = `msg-doc-${Date.now()}`;
    const timestampStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    try {
      const historyForApi = messages
        .filter((m) => !m.id.startsWith('msg-welcome'))
        .slice(-6)
        .map((m) => ({
          role: m.sender === 'USER' ? 'user' : 'assistant',
          content: m.content,
        }));

      // Add blank doctor message for real-time token accumulation
      setMessages((prev) => [
        ...prev,
        {
          id: doctorMsgId,
          sender: 'DOCTOR',
          content: '',
          timestamp: timestampStr,
        },
      ]);

      // Attempt high-speed streaming endpoint
      let streamedSuccess = false;
      try {
        const streamRes = await fetch(profile.streamEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: query,
            conversation_history: historyForApi,
            patient_context: patientContext,
          }),
        });

        if (streamRes.ok && streamRes.body) {
          const reader = streamRes.body.getReader();
          const decoder = new TextDecoder('utf-8');
          let buffer = '';
          let accumulatedContent = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed.startsWith('data: ')) continue;
              try {
                const payload = JSON.parse(trimmed.slice(6));
                if (payload.token) {
                  accumulatedContent += payload.token;
                  setMessages((prev) =>
                    prev.map((m) => (m.id === doctorMsgId ? { ...m, content: accumulatedContent } : m))
                  );
                }
                if (payload.done) {
                  streamedSuccess = true;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === doctorMsgId
                        ? {
                            ...m,
                            differential: payload.differential,
                            immediate_workup: payload.immediate_workup,
                            guideline_therapy: payload.guideline_therapy,
                            contraindications: payload.contraindications,
                            citations: payload.citations,
                            telemetry: payload.telemetry,
                          }
                        : m
                    )
                  );
                }
              } catch {
                // Ignore incomplete line parse
              }
            }
          }
        }
      } catch (streamErr) {
        console.warn('Streaming fetch failed, falling back to standard endpoint:', streamErr);
      }

      // If streaming didn't complete, fallback to standard synchronous endpoint
      if (!streamedSuccess) {
        const res = await fetch(profile.syncEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: query,
            conversation_history: historyForApi,
            patient_context: patientContext,
          }),
        });

        if (!res.ok) {
          throw new Error(`Server returned HTTP ${res.status}`);
        }

        const data: DoctorChatResponse = await res.json();
        setMessages((prev) =>
          prev.map((m) =>
            m.id === doctorMsgId
              ? {
                  ...m,
                  content: data.reply,
                  differential: data.differential,
                  immediate_workup: data.immediate_workup,
                  guideline_therapy: data.guideline_therapy,
                  contraindications: data.contraindications,
                  citations: data.citations,
                  telemetry: data.telemetry,
                }
              : m
          )
        );
      }
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === doctorMsgId
            ? {
                ...m,
                content: `Clinical consultation error: ${err.message || 'Unable to connect to diagnostic engine'}. Please retry.`,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-[var(--scrim)] backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-[var(--bg-surface)] border border-[var(--border-default)] w-full max-w-3xl h-[72vh] min-h-[500px] max-h-[640px] rounded-2xl shadow-xl flex flex-col overflow-hidden text-[var(--text-primary)] my-auto transition-all">
        {/* Header */}
        <div className="px-4 sm:px-5 py-2.5 sm:py-3 border-b border-[var(--border-default)] bg-[var(--bg-surface)] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            {/* Specialist Avatar */}
            <div className="relative shrink-0">
              <img
                src={profile.avatar}
                alt={`${profile.name}, ${profile.postNominals}`}
                className="w-10 h-10 rounded-xl object-cover object-top border border-[var(--indigo-500)]/30 shadow-xs"
              />
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-[var(--success-600)] border-2 border-white animate-pulse" />
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-sm sm:text-base font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
                  <span>{doctorName || `${profile.name}, ${profile.postNominals}`}</span>
                </h2>
                <Badge variant="success" size="sm">
                  On duty
                </Badge>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--text-secondary)] mt-0.5">
                <span className="text-[var(--indigo-600)] font-medium text-[11px] sm:text-xs">{profile.roleTitle}</span>
                <span className="text-[var(--border-default)]">•</span>
                <span className="flex items-center gap-1 font-mono text-[10px] sm:text-[11px] text-[var(--text-tertiary)]">
                  <BookOpen className="w-3 h-3 text-[var(--indigo-500)]" />
                  <span>Clinical Evidence RAG</span>
                </span>
                <span className="text-[var(--border-default)] hidden sm:inline">•</span>
                <span className="hidden sm:flex items-center gap-1 font-mono text-[10px] sm:text-[11px] text-[var(--text-tertiary)]">
                  <Cpu className="w-3 h-3 text-[var(--indigo-500)]" />
                  <span>AI guidance</span>
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleClearHistory}
              leadingIcon={<Trash2 className="w-3.5 h-3.5" />}
              title="Reset conversation"
              className="text-xs py-1 h-7 sm:h-8"
            >
              <span className="hidden sm:inline">Reset</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              title="Close modal"
              aria-label="Close modal"
              className="h-7 w-7 sm:h-8 sm:w-8 p-0"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Quick Scenario Starter Chips */}
        <div className="px-4 py-1.5 bg-[var(--bg-subtle)] border-b border-[var(--border-default)] flex items-center gap-1.5 overflow-x-auto text-xs shrink-0">
          <span className="text-[var(--text-tertiary)] font-medium shrink-0 flex items-center gap-1 text-[11px]">
            <Sparkles className="w-3 h-3 text-[var(--indigo-500)]" />
            <span>Presets:</span>
          </span>
          {profile.starterPrompts.map((item, idx) => (
            <Chip
              key={idx}
              clickable
              onClick={() => handleSendMessage(item.prompt)}
              className="whitespace-nowrap text-[11px] py-0.5 px-2 bg-[var(--bg-surface)] hover:bg-[var(--indigo-50)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[var(--indigo-600)] transition"
            >
              {item.title}
            </Chip>
          ))}
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-3.5 sm:p-4 space-y-3 bg-[var(--bg-page)]">
          {messages.map((msg) => {
            const isDoc = msg.sender === 'DOCTOR';
            const citationsOpen = !!expandedCitations[msg.id];
            const isSpeaking = speakingMessageId === msg.id;

            return (
              <div
                key={msg.id}
                className={`flex gap-2.5 ${isDoc ? 'items-start' : 'items-end justify-end'}`}
              >
                {/* Doctor Avatar on Left */}
                {isDoc && (
                  <img
                    src={profile.avatar}
                    alt={profile.shortName}
                    className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg object-cover object-top border border-[var(--border-default)] shrink-0 mt-0.5 shadow-xs"
                  />
                )}

                <div
                  className={`max-w-xl rounded-xl p-3 sm:p-3.5 shadow-xs transition-all ${
                    isDoc
                      ? 'bg-[var(--bg-surface)] border border-[var(--border-default)] text-[var(--text-primary)]'
                      : 'bg-[var(--indigo-500)] border border-[var(--indigo-500)] text-white'
                  }`}
                >
                  {/* Sender & Timestamp Header */}
                  <div className={`flex items-center justify-between gap-2.5 mb-1.5 pb-1 border-b text-[11px] ${
                    isDoc ? 'border-[var(--border-default)]' : 'border-white/20'
                  }`}>
                    <div className="flex items-center gap-1.5 font-semibold tracking-wide">
                      {isDoc ? (
                        <>
                          <span className="text-[var(--indigo-600)]">{profile.name}, {profile.postNominals}</span>
                          <Badge variant="primary" size="sm">
                            Attending
                          </Badge>
                        </>
                      ) : (
                        <span className="text-white font-medium">Clinician</span>
                      )}
                    </div>
                    <div className={`flex items-center gap-1.5 text-[10px] ${
                      isDoc ? 'text-[var(--text-tertiary)]' : 'text-white/80'
                    }`}>
                      <span>{msg.timestamp}</span>
                      {isDoc && (
                        <button
                          onClick={() => handleToggleSpeech(msg)}
                          className="p-0.5 rounded transition hover:bg-[var(--bg-subtle)] cursor-pointer text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
                          title={isSpeaking ? 'Stop voice readout' : `Listen to ${profile.shortName} read response`}
                        >
                          {isSpeaking ? (
                            <VolumeX className="w-3.5 h-3.5 text-[var(--danger-600)] animate-pulse" />
                          ) : (
                            <Volume2 className="w-3.5 h-3.5" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Body Text */}
                  <div className="text-xs sm:text-[13px] leading-relaxed whitespace-pre-wrap font-sans">
                    {msg.content}
                  </div>

                  {/* Structured Clinical Sections (Doctor only) */}
                  {isDoc && (
                    <>
                      {/* Differential Diagnosis Tags */}
                      {msg.differential && msg.differential.length > 0 && (
                        <div className="mt-2.5 pt-2 border-t border-[var(--border-default)]">
                          <span className="text-[10px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wider block mb-1.5 font-mono">
                            Differential diagnosis:
                          </span>
                          <div className="space-y-1">
                            {msg.differential.map((diff, dIdx) => (
                              <div
                                key={dIdx}
                                className="flex items-center justify-between gap-2 px-2.5 py-1 rounded-md bg-[var(--bg-subtle)] border border-[var(--border-default)] text-xs"
                              >
                                <span className="font-medium text-[var(--text-primary)]">{diff.condition}</span>
                                <div className="flex items-center gap-2 shrink-0">
                                  {diff.notes && (
                                    <span className="text-[10px] text-[var(--text-tertiary)] hidden sm:inline">
                                      {diff.notes}
                                    </span>
                                  )}
                                  <Badge variant="primary" size="sm">
                                    {(diff.likelihood * 100).toFixed(0)}%
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Safety Alerts / Contraindications */}
                      {msg.contraindications && msg.contraindications.length > 0 && (
                        <div className="mt-2 p-2 rounded-lg bg-[var(--warning-50)] border border-[var(--warning-600)]/20 text-[var(--text-primary)]">
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--warning-600)] mb-0.5">
                            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                            <span>Clinical safety & contraindications:</span>
                          </div>
                          <ul className="list-disc list-inside text-[11px] sm:text-xs space-y-0.5 text-[var(--text-secondary)] pl-1">
                            {msg.contraindications.map((c, cIdx) => (
                              <li key={cIdx}>{c}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Immediate Workup */}
                      {msg.immediate_workup && msg.immediate_workup.length > 0 && (
                        <div className="mt-2 p-2 rounded-lg bg-[var(--bg-subtle)] border border-[var(--border-default)]">
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--indigo-600)] mb-1">
                            <Activity className="w-3.5 h-3.5" />
                            <span>Recommended diagnostic workup:</span>
                          </div>
                          <ul className="list-disc list-inside text-[11px] sm:text-xs space-y-0.5 text-[var(--text-secondary)] pl-1">
                            {msg.immediate_workup.map((wk, wkIdx) => (
                              <li key={wkIdx}>{wk}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Guideline Therapy & Workup */}
                      {msg.guideline_therapy && msg.guideline_therapy.length > 0 && (
                        <div className="mt-2 p-2 rounded-lg bg-[var(--bg-subtle)] border border-[var(--border-default)]">
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--success-600)] mb-1">
                            <Stethoscope className="w-3.5 h-3.5" />
                            <span>Guideline-directed management:</span>
                          </div>
                          <ul className="list-disc list-inside text-[11px] sm:text-xs space-y-0.5 text-[var(--text-secondary)] pl-1">
                            {msg.guideline_therapy.map((rx, rxIdx) => (
                              <li key={rxIdx}>{rx}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Expandable Citations */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-2 pt-1.5">
                          <button
                            onClick={() => toggleCitations(msg.id)}
                            className="text-[11px] text-[var(--indigo-600)] hover:underline flex items-center gap-1 transition cursor-pointer font-medium"
                          >
                            <BookOpen className="w-3.5 h-3.5" />
                            <span>
                              {citationsOpen ? 'Hide' : 'View'} {msg.citations.length} textbook citations ({profile.bookTitle})
                            </span>
                            {citationsOpen ? (
                              <ChevronUp className="w-3 h-3" />
                            ) : (
                              <ChevronDown className="w-3 h-3" />
                            )}
                          </button>

                          {citationsOpen && (
                            <div className="mt-1.5 space-y-1.5 animate-in fade-in duration-150">
                              {msg.citations.map((cite, cIdx) => (
                                <div
                                  key={cIdx}
                                  className="p-2 rounded-md bg-[var(--bg-subtle)] border border-[var(--border-default)] text-xs"
                                >
                                  <div className="font-semibold text-[var(--text-primary)] text-[11px] mb-0.5">
                                    {cite.chapter} {cite.page ? `(Page ${cite.page})` : ''}
                                  </div>
                                  <p className="text-[11px] text-[var(--text-secondary)] italic leading-relaxed">
                                    "{cite.text}"
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Telemetry pill */}
                      {msg.telemetry && (
                        <div className="mt-2 pt-1.5 border-t border-[var(--border-default)] flex flex-wrap items-center justify-between text-[10px] text-[var(--text-tertiary)] font-mono">
                          <span className="flex items-center gap-1">
                            <Activity className="w-3 h-3 text-[var(--indigo-500)]" />
                            <span>{msg.telemetry.model}</span>
                          </span>
                          <span>{msg.telemetry.latency_ms > 0 ? `${msg.telemetry.latency_ms} ms` : 'Cached'}</span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            );
          })}

          {/* Typing / Loading indicator */}
          {isLoading && (
            <div className="flex gap-2.5 items-start animate-in fade-in duration-150">
              <img
                src={profile.avatar}
                alt={profile.shortName}
                className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg object-cover object-top border border-[var(--border-default)] shrink-0 mt-0.5 shadow-xs"
              />
              <div className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl px-3 py-2 flex items-center gap-2.5 text-xs text-[var(--text-secondary)] shadow-xs">
                <Loader2 className="w-3.5 h-3.5 text-[var(--indigo-500)] animate-spin" />
                <span>{profile.analyzingText}</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="px-3.5 sm:px-4 py-2.5 bg-[var(--bg-surface)] border-t border-[var(--border-default)] shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-end gap-2.5"
          >
            <div className="flex-1 bg-[var(--bg-subtle)] border border-[var(--border-default)] focus-within:border-[var(--indigo-500)] focus-within:ring-1 focus-within:ring-[var(--indigo-500)]/20 rounded-xl px-3 py-2 shadow-xs transition">
              <textarea
                ref={inputRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={profile.placeholderText}
                rows={1}
                className="w-full bg-transparent text-[var(--text-primary)] placeholder-[var(--text-tertiary)] text-xs sm:text-[13px] leading-5 focus:outline-none resize-none font-sans min-h-[28px] max-h-[80px]"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!inputText.trim() || isLoading}
              leadingIcon={isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              className="h-9 sm:h-10 px-3.5 shrink-0"
            >
              Send
            </Button>
          </form>
          <div className="flex items-center justify-between text-[10px] text-[var(--text-tertiary)] mt-1.5 px-1 font-mono">
            <span>Enter to send · Shift+Enter for newline</span>
            <span className="hidden sm:inline">Grounding: {profile.bookTitle}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
