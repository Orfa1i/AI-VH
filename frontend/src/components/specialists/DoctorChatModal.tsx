import React, { useState, useEffect, useRef } from 'react';
import type { DoctorChatMessage, DoctorChatResponse } from '../../types';
import drMarcusPhoto from '../../assets/dr_marcus_vance.jpg';
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

interface DoctorChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientContext?: Record<string, any>;
}

const STARTER_PROMPTS = [
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
];

const INITIAL_GREETING: DoctorChatMessage = {
  id: 'msg-welcome',
  sender: 'DOCTOR',
  content:
    'Greetings. I am Dr. Marcus Vance, Chief Attending Physician of Internal Medicine. My clinical reasoning is grounded in Harrison\'s Principles of Internal Medicine (21st Edition) and MedGemma AI diagnostic models.\n\nHow may I assist you with clinical cases, differential diagnoses, evidence-based therapies, or medication contraindications today?',
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  telemetry: {
    live_gpu_inference: true,
    model: 'google/medgemma-4b (NF4 LoRA Aligned)',
    knowledge_source: "Harrison's Principles of Internal Medicine (21st Ed)",
    latency_ms: 0,
  },
};

export const DoctorChatModal: React.FC<DoctorChatModalProps> = ({
  isOpen,
  onClose,
  patientContext,
}) => {
  const [messages, setMessages] = useState<DoctorChatMessage[]>([INITIAL_GREETING]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    } else {
      stopClinicalSpeech();
      setSpeakingMessageId(null);
    }
  }, [isOpen]);

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
        'DR_VANCE',
        () => setSpeakingMessageId(msg.id),
        () => setSpeakingMessageId(null)
      );
    }
  };

  const handleClearHistory = () => {
    stopClinicalSpeech();
    setSpeakingMessageId(null);
    setMessages([INITIAL_GREETING]);
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
        .filter((m) => m.id !== 'msg-welcome')
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
        const streamRes = await fetch('/api/specialists/internal-medicine/chat/stream', {
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
        const res = await fetch('/api/specialists/internal-medicine/chat', {
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border-2 border-cyan-500/40 w-full max-w-4xl h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden text-slate-200 ring-1 ring-cyan-500/20">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 bg-slate-950/90 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3.5">
            {/* Dr. Vance Avatar */}
            <div className="relative shrink-0">
              <img
                src={drMarcusPhoto}
                alt="Dr. Marcus Vance, MD"
                className="w-12 h-12 rounded-xl object-cover object-top border-2 border-cyan-400 shadow-lg shadow-cyan-950/80 ring-2 ring-cyan-500/20"
              />
              <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-slate-950 shadow animate-pulse" />
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-1.5">
                  <span>Dr. Marcus Vance, MD, FACP</span>
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-600/60 text-[10px] font-bold font-mono">
                  ● ON DUTY
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400 mt-0.5">
                <span className="text-cyan-400 font-medium">Chief Attending Physician, Internal Medicine</span>
                <span className="text-slate-600">•</span>
                <span className="flex items-center gap-1 text-purple-300 font-mono text-[11px]">
                  <BookOpen className="w-3 h-3 text-purple-400" />
                  <span>Harrison's 21st Ed RAG</span>
                </span>
                <span className="text-slate-600">•</span>
                <span className="flex items-center gap-1 text-cyan-300 font-mono text-[11px]">
                  <Cpu className="w-3 h-3 text-cyan-400" />
                  <span>MedGemma Aligned</span>
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleClearHistory}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs flex items-center gap-1 transition"
              title="Reset conversation"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Reset</span>
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Quick Scenario Starter Chips */}
        <div className="px-4 py-2.5 bg-slate-950/60 border-b border-slate-800/80 flex items-center gap-2 overflow-x-auto text-xs shrink-0">
          <span className="text-slate-400 font-medium shrink-0 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Presets:</span>
          </span>
          {STARTER_PROMPTS.map((item, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(item.prompt)}
              disabled={isLoading}
              className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-cyan-950 hover:border-cyan-600 border border-slate-700 text-slate-300 hover:text-cyan-200 text-[11px] whitespace-nowrap transition cursor-pointer disabled:opacity-50"
            >
              {item.title}
            </button>
          ))}
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 bg-gradient-to-b from-slate-900/60 via-slate-900/40 to-slate-950/80">
          {messages.map((msg) => {
            const isDoc = msg.sender === 'DOCTOR';
            const citationsOpen = !!expandedCitations[msg.id];
            const isSpeaking = speakingMessageId === msg.id;

            return (
              <div
                key={msg.id}
                className={`flex gap-3 ${isDoc ? 'items-start' : 'items-end justify-end'}`}
              >
                {/* Doctor Avatar on Left */}
                {isDoc && (
                  <img
                    src={drMarcusPhoto}
                    alt="Dr. Vance"
                    className="w-8 h-8 rounded-lg object-cover object-top border border-cyan-400/80 shrink-0 mt-1 shadow"
                  />
                )}

                <div
                  className={`max-w-2xl rounded-2xl p-4 sm:p-5 shadow-xl transition-all ${
                    isDoc
                      ? 'bg-slate-800/90 border border-slate-700/80 text-slate-100 ring-1 ring-white/5'
                      : 'bg-cyan-950/90 border border-cyan-600/70 text-cyan-50'
                  }`}
                >
                  {/* Sender & Timestamp Header */}
                  <div className="flex items-center justify-between gap-3 mb-2 pb-1.5 border-b border-white/5 text-[11px]">
                    <div className="flex items-center gap-1.5 font-bold tracking-wide">
                      {isDoc ? (
                        <>
                          <span className="text-cyan-300">Dr. Marcus Vance, MD</span>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-900/50 text-cyan-200 border border-cyan-700/40">
                            Attending
                          </span>
                        </>
                      ) : (
                        <span className="text-slate-300">Clinician / User</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-slate-400 text-[10px]">
                      <span>{msg.timestamp}</span>
                      {isDoc && (
                        <button
                          onClick={() => handleToggleSpeech(msg)}
                          className={`p-1 rounded transition ${
                            isSpeaking
                              ? 'bg-rose-900/50 text-rose-300 border border-rose-600'
                              : 'hover:bg-slate-700 text-slate-400 hover:text-slate-200'
                          }`}
                          title={isSpeaking ? 'Stop clinical voice readout' : 'Listen to Dr. Vance read response'}
                        >
                          {isSpeaking ? (
                            <VolumeX className="w-3.5 h-3.5 animate-pulse" />
                          ) : (
                            <Volume2 className="w-3.5 h-3.5" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Body Text */}
                  <div className="text-xs sm:text-sm leading-relaxed whitespace-pre-wrap font-sans">
                    {msg.content}
                  </div>

                  {/* Structured Clinical Sections (Doctor only) */}
                  {isDoc && (
                    <>
                      {/* Differential Diagnosis Tags */}
                      {msg.differential && msg.differential.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-slate-700/60">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                            Evidence-Based Differential Diagnosis:
                          </span>
                          <div className="space-y-1.5">
                            {msg.differential.map((diff, dIdx) => (
                              <div
                                key={dIdx}
                                className="flex items-center justify-between gap-2 p-2 rounded-lg bg-slate-900/70 border border-slate-700/70 text-xs"
                              >
                                <span className="font-semibold text-slate-200">{diff.condition}</span>
                                <div className="flex items-center gap-2 shrink-0">
                                  {diff.notes && (
                                    <span className="text-[10px] text-slate-400 hidden sm:inline">
                                      {diff.notes}
                                    </span>
                                  )}
                                  <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 text-[10px] font-mono font-bold">
                                    {(diff.likelihood * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Safety Alerts / Contraindications */}
                      {msg.contraindications && msg.contraindications.length > 0 && (
                        <div className="mt-3 p-3 rounded-xl bg-amber-950/40 border border-amber-600/50 text-amber-200">
                          <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400 mb-1">
                            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                            <span>Clinical Safety & Contraindications:</span>
                          </div>
                          <ul className="list-disc list-inside text-xs space-y-0.5 text-amber-100/90 pl-1">
                            {msg.contraindications.map((c, cIdx) => (
                              <li key={cIdx}>{c}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Guideline Therapy & Workup */}
                      {msg.guideline_therapy && msg.guideline_therapy.length > 0 && (
                        <div className="mt-3 p-3 rounded-xl bg-slate-900/80 border border-slate-700/60">
                          <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 mb-1.5">
                            <Stethoscope className="w-3.5 h-3.5 text-emerald-400" />
                            <span>Guideline-Directed Management:</span>
                          </div>
                          <ul className="list-disc list-inside text-xs space-y-0.5 text-slate-200 pl-1">
                            {msg.guideline_therapy.map((rx, rxIdx) => (
                              <li key={rxIdx}>{rx}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Expandable Harrison's Citations */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-3 pt-2">
                          <button
                            onClick={() => toggleCitations(msg.id)}
                            className="text-[11px] text-purple-300 hover:text-purple-200 flex items-center gap-1 transition cursor-pointer font-medium"
                          >
                            <BookOpen className="w-3.5 h-3.5 text-purple-400" />
                            <span>
                              {citationsOpen ? 'Hide' : 'View'} {msg.citations.length} Harrison's Textbook Citations
                            </span>
                            {citationsOpen ? (
                              <ChevronUp className="w-3 h-3" />
                            ) : (
                              <ChevronDown className="w-3 h-3" />
                            )}
                          </button>

                          {citationsOpen && (
                            <div className="mt-2 space-y-2 animate-in fade-in duration-150">
                              {msg.citations.map((cite, cIdx) => (
                                <div
                                  key={cIdx}
                                  className="p-2.5 rounded-lg bg-slate-950/80 border border-purple-500/30 text-slate-300 text-xs"
                                >
                                  <div className="font-bold text-purple-300 text-[11px] mb-1">
                                    {cite.chapter} {cite.page ? `(Page ${cite.page})` : ''}
                                  </div>
                                  <p className="text-[11px] text-slate-400 italic leading-relaxed">
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
                        <div className="mt-3 pt-2 border-t border-white/5 flex flex-wrap items-center justify-between text-[10px] text-slate-500 font-mono">
                          <span className="flex items-center gap-1">
                            <Activity className="w-3 h-3 text-cyan-400" />
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
            <div className="flex gap-3 items-start animate-in fade-in duration-150">
              <img
                src={drMarcusPhoto}
                alt="Dr. Vance"
                className="w-8 h-8 rounded-lg object-cover object-top border border-cyan-400/80 shrink-0 mt-1 shadow"
              />
              <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-4 flex items-center gap-3 text-xs text-slate-300">
                <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                <span>Dr. Vance is analyzing Harrison's clinical knowledge & MedGemma...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-end gap-3"
          >
            <div className="flex-1 bg-slate-900 border border-slate-700 focus-within:border-cyan-500 rounded-xl px-3.5 py-2.5 shadow-inner transition">
              <textarea
                ref={inputRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask Dr. Vance about clinical cases, differential diagnoses, therapies, or Harrison's guidelines... (Press Enter to send)"
                rows={2}
                className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-xs sm:text-sm focus:outline-none resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={!inputText.trim() || isLoading}
              className="px-4 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white text-xs sm:text-sm font-bold shadow-lg shadow-cyan-950 flex items-center gap-1.5 transition cursor-pointer disabled:cursor-not-allowed shrink-0"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">Send</span>
            </button>
          </form>
          <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 px-1">
            <span>Press Enter to send, Shift+Enter for newline</span>
            <span>Grounding: Harrison's Principles of Internal Medicine 21st Ed & MedGemma</span>
          </div>
        </div>
      </div>
    </div>
  );
};
