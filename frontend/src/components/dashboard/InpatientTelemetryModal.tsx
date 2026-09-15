import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Activity,
  Heart,
  Droplets,
  RefreshCw,
  Volume2,
  VolumeX,
} from 'lucide-react';

import { speakClinicalMessage, stopClinicalSpeech } from '../../utils/speechSynthesis';

export interface InpatientRoom {
  room_number: string;
  room_name: string;
  patient_name: string;
  age: number;
  sex: string;
  diagnosis: string;
  acuity: string;
  heart_rate: number;
  systolic_bp: number;
  diastolic_bp: number;
  respiratory_rate: number;
  spo2: number;
  rhythm_strip: string;
  active_infusion: string;
  diet: string;
  nurse_assigned: string;
  status: string;
}

const DEFAULT_ROOMS: InpatientRoom[] = [
  {
    room_number: '101',
    room_name: 'Inpatient Suite 101 - Cardiac Telemetry',
    patient_name: 'Robert Miller',
    age: 62,
    sex: 'Male',
    diagnosis: 'Acute NSTEMI (Post-Angiography)',
    acuity: 'URGENT',
    heart_rate: 76,
    systolic_bp: 128,
    diastolic_bp: 82,
    respiratory_rate: 16,
    spo2: 98.0,
    rhythm_strip: 'Normal Sinus Rhythm with resolving ST depression',
    active_infusion: 'Unfractionated Heparin 18 units/kg/hr IV',
    diet: 'Cardiac / Low Sodium',
    nurse_assigned: 'Sarah Jenkins, RN',
    status: 'STABLE_MONITORED',
  },
  {
    room_number: '102',
    room_name: 'Inpatient Suite 102 - Medical ICU Bed',
    patient_name: 'Elena Rostova',
    age: 24,
    sex: 'Female',
    diagnosis: 'Diabetic Ketoacidosis (Closing Anion Gap)',
    acuity: 'EMERGENT',
    heart_rate: 96,
    systolic_bp: 110,
    diastolic_bp: 70,
    respiratory_rate: 20,
    spo2: 99.0,
    rhythm_strip: 'Sinus Rhythm without ectopy',
    active_infusion: 'Regular Insulin 5 units/hr + D5W 0.45% NS with 20 mEq KCl',
    diet: 'NPO (strict)',
    nurse_assigned: 'Sarah Jenkins, RN',
    status: 'ACUTE_IMPROVING',
  },
  {
    room_number: '103',
    room_name: 'Inpatient Suite 103 - Step-Down Bed',
    patient_name: 'Arthur Pendelton',
    age: 68,
    sex: 'Male',
    diagnosis: 'Acute Kidney Injury Stage 3 (Resolving)',
    acuity: 'URGENT',
    heart_rate: 80,
    systolic_bp: 118,
    diastolic_bp: 74,
    respiratory_rate: 16,
    spo2: 97.0,
    rhythm_strip: 'Sinus Rhythm with first-degree AV block',
    active_infusion: 'Plasmalyte @ 125 mL/hr IV Maintenance',
    diet: 'Renal Diet (Low Potassium / Phosphorus)',
    nurse_assigned: 'Sarah Jenkins, RN',
    status: 'DIURESIS_RECOVERY',
  },
  {
    room_number: '104',
    room_name: 'Inpatient Suite 104 - Step-Down Bed',
    patient_name: 'Clara Vance',
    age: 52,
    sex: 'Female',
    diagnosis: 'Submassive Pulmonary Embolism',
    acuity: 'EMERGENT',
    heart_rate: 92,
    systolic_bp: 116,
    diastolic_bp: 76,
    respiratory_rate: 20,
    spo2: 96.0,
    rhythm_strip: 'Sinus Tachycardia with S1Q3T3 morphology',
    active_infusion: 'Enoxaparin 80 mg SC q12h + 2L Nasal Cannula O2',
    diet: 'Regular as tolerated',
    nurse_assigned: 'Sarah Jenkins, RN',
    status: 'STABLE_ANTICOAGULATED',
  },
];

interface InpatientTelemetryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const InpatientTelemetryModal: React.FC<InpatientTelemetryModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [rooms, setRooms] = useState<InpatientRoom[]>(DEFAULT_ROOMS);
  const [loading, setLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [animOffset, setAnimOffset] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<'Connecting' | 'Live' | 'Offline'>('Offline');
  const wsRef = useRef<WebSocket | null>(null);

  const canvasRefs = useRef<{ [key: string]: HTMLCanvasElement | null }>({});

  useEffect(() => {
    if (isOpen) {
      fetchRooms();
      
      setConnectionStatus('Connecting');
      const ws = new WebSocket(`ws://127.0.0.1:8000/api/inpatient/telemetry/stream`);
      wsRef.current = ws;

      ws.onopen = () => setConnectionStatus('Live');
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setRooms(data);
        } catch (e) {
          console.error("Error parsing telemetry WebSocket data", e);
        }
      };
      ws.onclose = () => setConnectionStatus('Offline');
      ws.onerror = (error) => {
        console.error("Telemetry WebSocket error", error);
        setConnectionStatus('Offline');
      };
    } else {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setConnectionStatus('Offline');
      stopClinicalSpeech();
      setIsSpeaking(false);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isOpen]);

  // Real-time animated ECG drawing loop
  useEffect(() => {
    if (!isOpen) return;
    let animId: number;

    const renderWaveforms = () => {
      setAnimOffset((prev) => (prev + 2) % 300);

      rooms.forEach((room) => {
        const canvas = canvasRefs.current[room.room_number];
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const width = canvas.width;
        const height = canvas.height;
        const midY = height / 2;

        ctx.fillStyle = '#090d16';
        ctx.fillRect(0, 0, width, height);

        // Grid lines
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 0.5;
        for (let x = 0; x < width; x += 15) {
          ctx.beginPath();
          ctx.moveTo(x, 0);
          ctx.lineTo(x, height);
          ctx.stroke();
        }
        for (let y = 0; y < height; y += 15) {
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(width, y);
          ctx.stroke();
        }

        // Green ECG trace
        ctx.strokeStyle = '#22c55e';
        ctx.lineWidth = 1.8;
        ctx.beginPath();

        const wavelength = 60;
        for (let x = 0; x < width; x++) {
          const pos = (x + animOffset) % wavelength;
          let y = midY;

          // P-Q-R-S-T wave model
          if (pos > 10 && pos < 16) {
            // P wave
            y -= Math.sin(((pos - 10) / 6) * Math.PI) * 4;
          } else if (pos === 22) {
            // Q dip
            y += 4;
          } else if (pos >= 23 && pos <= 26) {
            // R spike
            y -= 24;
          } else if (pos === 27) {
            // S dip
            y += 7;
          } else if (pos > 34 && pos < 44) {
            // T wave
            y -= Math.sin(((pos - 34) / 10) * Math.PI) * 7;
          }

          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      });

      animId = requestAnimationFrame(renderWaveforms);
    };

    animId = requestAnimationFrame(renderWaveforms);
    return () => cancelAnimationFrame(animId);
  }, [isOpen, rooms, animOffset]);

  const fetchRooms = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/inpatient/rooms');
      if (res.ok) {
        const data = await res.json();
        setRooms(data);
      }
    } catch (err) {
      console.warn('Using default telemetry rooms:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceReport = () => {
    if (isSpeaking) {
      stopClinicalSpeech();
      setIsSpeaking(false);
    } else {
      const text = `Inpatient Wing Nurse Report. All four suites are occupied. Room 101, Robert Miller, telemetry is stable on heparin infusion. Room 102, Elena Rostova, acidosis is resolving with IV regular insulin. Room 103, Arthur Pendelton, diuresis has recovered with normal saline hydration. Room 104, Clara Vance, oxygen saturations are 96 percent on 2 liters oxygen.`;
      speakClinicalMessage(
        text,
        'NURSE_SARAH',
        () => setIsSpeaking(true),
        () => setIsSpeaking(false)
      );
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-6xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-gradient-to-r from-slate-900 via-sky-950/40 to-slate-900 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500 to-teal-600 flex items-center justify-center shadow-lg shadow-sky-500/25 text-white">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100">
                  East Inpatient Wing: Central Telemetry Console
                </h2>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold flex items-center gap-1.5 border ${
                  connectionStatus === 'Live' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' :
                  connectionStatus === 'Connecting' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
                  'bg-rose-500/20 text-rose-300 border-rose-500/30'
                }`}>
                  {connectionStatus === 'Live' && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />}
                  {connectionStatus === 'Live' ? 'LIVE 4-BED CENTRAL MONITORING' : `${connectionStatus.toUpperCase()}`}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Continuous Multi-Lead Cardiac Telemetry, Vital Signs & Active Continuous Infusions
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchRooms}
              disabled={loading}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-all"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Refreshing...' : 'Refresh Telemetry'}</span>
            </button>

            <button
              onClick={handleVoiceReport}
              className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-all ${
                isSpeaking
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-200'
              }`}
            >
              {isSpeaking ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
              <span>{isSpeaking ? 'Mute Report' : 'Nurse Handoff Report'}</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-all cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Telemetry Grid */}
        <div className="p-6 flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-5">
          {rooms.map((room) => (
            <div
              key={room.room_number}
              className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition-all space-y-3"
            >
              {/* Patient Banner */}
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-lg bg-sky-500/20 text-sky-400 font-mono text-xs font-bold flex items-center justify-center">
                    {room.room_number}
                  </span>
                  <div>
                    <span className="text-sm font-bold text-slate-100">{room.patient_name}</span>
                    <span className="text-xs text-slate-400 ml-1.5">
                      ({room.age}{room.sex === 'Male' ? 'M' : 'F'})
                    </span>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  {room.status}
                </span>
              </div>

              {/* Diagnosis */}
              <div className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                <span className="text-slate-500">Diagnosis:</span>
                <span className="font-semibold text-slate-200">{room.diagnosis}</span>
              </div>

              {/* Animated ECG Waveform Canvas */}
              <div className="relative rounded-lg overflow-hidden border border-slate-800">
                <canvas
                  ref={(el) => {
                    canvasRefs.current[room.room_number] = el;
                  }}
                  width={420}
                  height={65}
                  className="w-full h-[65px] block bg-slate-950"
                />

                <div className="absolute top-1.5 left-2 flex items-center gap-2">
                  <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                    LEAD II
                  </span>
                </div>
                <div className="absolute bottom-1 right-2 text-[10px] font-mono text-slate-400 truncate max-w-[280px]">
                  {room.rhythm_strip}
                </div>
              </div>

              {/* Vitals Telemetry Numbers */}
              <div className="grid grid-cols-4 gap-2 pt-1">
                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                    <Heart className="w-3 h-3 text-rose-400" />
                    <span>HR</span>
                  </div>
                  <div className="text-base font-black text-rose-400 mt-0.5">
                    {room.heart_rate} <span className="text-[10px] font-normal text-slate-500">bpm</span>
                  </div>
                </div>

                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-400">BP</div>
                  <div className="text-base font-black text-sky-400 mt-0.5">
                    {room.systolic_bp}/{room.diastolic_bp}
                  </div>
                </div>

                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-400">SpO2</div>
                  <div className="text-base font-black text-emerald-400 mt-0.5">
                    {room.spo2}%
                  </div>
                </div>

                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-400">RR</div>
                  <div className="text-base font-black text-indigo-400 mt-0.5">
                    {room.respiratory_rate}
                  </div>
                </div>
              </div>

              {/* Active Infusion & Diet */}
              <div className="pt-2 border-t border-slate-800/80 space-y-1.5 text-xs">
                <div className="flex items-center gap-1.5 text-slate-300">
                  <Droplets className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  <span className="text-slate-400">Infusion:</span>
                  <span className="font-medium text-slate-200 truncate">{room.active_infusion}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>Diet: {room.diet}</span>
                  <span className="text-slate-500">Nurse: {room.nurse_assigned}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
