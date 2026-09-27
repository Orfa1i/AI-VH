import React, { useState, useEffect, useRef } from 'react';
import { HospitalFlowDiagram } from './HospitalFlowDiagram';
import { EventStreamHUD } from '../dashboard/EventStreamHUD';
import { VitalsMonitorHUD } from '../dashboard/VitalsMonitorHUD';
import { InternalMedicineConsultModal } from '../specialists/InternalMedicineConsultModal';
import { DepartmentStationModal } from '../specialists/DepartmentStationModal';
import { toggleGlobalMute, isGlobalMuted } from '../../utils/speechSynthesis';
import type { HospitalEvent, BenchmarkCase, VitalSigns } from '../../types';
import {
  Activity,
  ArrowLeft,
  Stethoscope,
  Volume2,
  VolumeX,
} from 'lucide-react';

interface PatientJourneyFlowPageProps {
  onBackToPortal?: () => void;
}

export const PatientJourneyFlowPage: React.FC<PatientJourneyFlowPageProps> = ({ onBackToPortal }) => {
  const [cases, setCases] = useState<BenchmarkCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('CASE-101');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [events, setEvents] = useState<HospitalEvent[]>([]);
  const [activeVitals, setActiveVitals] = useState<VitalSigns | null>(null);
  const [currentPatientName, setCurrentPatientName] = useState<string>('');
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(isGlobalMuted());

  // Modals
  const [isConsultOpen, setIsConsultOpen] = useState<boolean>(false);
  const [departmentStationId, setDepartmentStationId] = useState<string | null>(null);

  // Department State
  const [activeDepartment, setActiveDepartment] = useState<string>('RECEPTION');
  const [doctorAction, setDoctorAction] = useState<string>('Reviewing Inpatient Charts');

  const wsRef = useRef<WebSocket | null>(null);

  // Fetch cases and recent events
  useEffect(() => {
    fetch('/api/cases')
      .then((res) => res.json())
      .then((data) => {
        setCases(data);
        if (data.length > 0) setSelectedCaseId(data[0].id);
      })
      .catch((err) => console.error('Failed to load cases:', err));

    fetch('/api/simulation/events')
      .then((res) => res.json())
      .then((data) => setEvents(data))
      .catch((err) => console.error('Failed to load events:', err));
  }, []);

  // Setup WebSocket connection
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/simulation`;

    const connectWs = () => {
      try {
        const socket = new WebSocket(wsUrl);
        wsRef.current = socket;

        socket.onopen = () => {
          setIsWsConnected(true);
        };

        socket.onmessage = (event) => {
          try {
            const parsedEvent: HospitalEvent = JSON.parse(event.data);
            handleIncomingEvent(parsedEvent);
          } catch (e) {
            console.error('Error parsing event payload:', e);
          }
        };

        socket.onclose = () => {
          setIsWsConnected(false);
          setTimeout(connectWs, 3000);
        };

        socket.onerror = () => {
          socket.close();
        };
      } catch (err) {
        console.warn('WebSocket connection error:', err);
      }
    };

    connectWs();

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const handleIncomingEvent = (evt: HospitalEvent) => {
    setEvents((prev) => [...prev.slice(-100), evt]);

    switch (evt.event_type) {
      case 'PATIENT_ARRIVED':
        setActiveDepartment('RECEPTION');
        if (evt.payload.name) setCurrentPatientName(evt.payload.name);
        break;

      case 'NURSE_TRIAGE_STARTED':
      case 'VITALS_RECORDED':
        setActiveDepartment('NURSE_STATION');
        if (evt.payload.heart_rate) {
          setActiveVitals(evt.payload as VitalSigns);
        }
        break;

      case 'DOCTOR_ASSIGNED':
      case 'EXAMINATION_STARTED':
      case 'PATIENT_INTERVIEWED':
        setActiveDepartment('EXAMINATION_ROOM_1');
        setDoctorAction('Conducting Clinical Exam & Interview');
        break;

      case 'RAG_QUERY_INITIATED':
      case 'RAG_KNOWLEDGE_RETRIEVED':
        setDoctorAction("Querying Harrison's Internal Medicine");
        break;

      case 'LAB_ORDERED':
      case 'LAB_RESULT_READY':
        setActiveDepartment('LABORATORY');
        setDoctorAction('Reviewing Lab Biomarkers');
        break;

      case 'DIAGNOSIS_MADE':
      case 'TREATMENT_ORDERED':
        setActiveDepartment('DOCTOR_STATION');
        setDoctorAction('Physician Diagnosis Established');
        break;

      case 'CLINICAL_REPORT_GENERATED':
        setActiveDepartment('DOCTOR_STATION');
        setDoctorAction('Report Finalized & Queued');
        break;
    }
  };

  const handleStationInteract = (stationId: string) => {
    switch (stationId) {
      case 'INTERNAL_MEDICINE':
        setIsConsultOpen(true);
        break;
      case 'LABORATORY':
      case 'RADIOLOGY':
      case 'NURSE_STATION':
        setDepartmentStationId(stationId);
        break;
    }
  };

  const handleRunSimulation = async () => {
    setIsRunning(true);
    try {
      await fetch('/api/simulation/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: selectedCaseId }),
      });
    } catch (err) {
      console.error('Failed to run simulation:', err);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-slate-950 overflow-hidden select-none font-sans relative isolate telemetry-grid">
      {/* Top Clinical Header */}
      <header className="h-14 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 flex items-center justify-between z-30 shrink-0 shadow-lg">
        {/* Left: Branding & Back Button */}
        <div className="flex items-center gap-3">
          {onBackToPortal && (
            <button
              onClick={onBackToPortal}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-sky-400 hover:text-sky-300 font-medium text-xs rounded-lg border border-slate-700 transition shadow cursor-pointer active:scale-95"
              title="Return to Clinical Management Portal"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Portal</span>
            </button>
          )}

          {onBackToPortal && <div className="h-4 w-px bg-slate-700 mx-1" />}

          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-sky-500/10 border border-sky-400/30 flex items-center justify-center text-sky-400 shadow-[0_0_12px_rgba(56,189,248,0.25)]">
              <Activity className="w-4 h-4 text-sky-400 animate-pulse" />
            </div>
            <div>
              <span className="text-sm font-bold bg-gradient-to-r from-sky-400 via-cyan-400 to-teal-400 bg-clip-text text-transparent">
                AI-VH Clinical Flow Architecture & Patient Journey
              </span>
              <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-[10px] font-mono rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-semibold">
                2D Clinical Process Pathway
              </span>
            </div>
          </div>
        </div>

        {/* Center: Real-Time Department Tracker */}
        <div className="hidden md:flex items-center gap-2 bg-slate-950/80 px-3.5 py-1 rounded-full border border-slate-800 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-slate-400">Current Station:</span>
          <span className="text-slate-200 font-semibold font-mono">{activeDepartment.replace(/_/g, ' ')}</span>
        </div>

        {/* Right: Specialist Consult & Audio Toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsConsultOpen(true)}
            className="px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-sky-300 text-xs font-mono font-medium rounded-lg border border-sky-900/40 hover:border-sky-700/60 transition flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <Stethoscope className="w-3.5 h-3.5 text-sky-400" />
            <span>Dr. Vance RAG</span>
          </button>

          <button
            onClick={() => setIsAudioMuted(toggleGlobalMute())}
            className={`p-1.5 rounded-lg border text-xs transition cursor-pointer ${
              isAudioMuted
                ? 'bg-slate-800 text-slate-500 border-slate-700'
                : 'bg-sky-950 text-sky-400 border-sky-800'
            }`}
            title={isAudioMuted ? 'Unmute Audio Voice Synthesis' : 'Mute Audio Voice Synthesis'}
          >
            {isAudioMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5 text-sky-400" />}
          </button>
        </div>
      </header>

      {/* Main Viewport: 2D Clinical Flow Diagram & Encounter Trajectory */}
      <main className="flex-1 relative overflow-hidden flex flex-col">
        <HospitalFlowDiagram
          cases={cases}
          selectedCaseId={selectedCaseId}
          onSelectCase={(id) => setSelectedCaseId(id)}
          onRunSimulation={handleRunSimulation}
          isRunning={isRunning}
          activeDepartment={activeDepartment}
          doctorAction={doctorAction}
          events={events}
          activeVitals={activeVitals}
          onOpenConsult={() => setIsConsultOpen(true)}
          onOpenDepartmentStation={handleStationInteract}
        />

        {/* Floating Glassmorphism Vitals Telemetry */}
        <VitalsMonitorHUD vitals={activeVitals} patientName={currentPatientName} />

        {/* Floating Real-Time Event Feed */}
        <EventStreamHUD events={events} isConnected={isWsConnected} />
      </main>

      {/* Modals */}
      <InternalMedicineConsultModal
        isOpen={isConsultOpen}
        onClose={() => setIsConsultOpen(false)}
      />

      <DepartmentStationModal
        stationId={departmentStationId}
        isOpen={departmentStationId !== null}
        onClose={() => setDepartmentStationId(null)}
        cases={cases}
        selectedCaseId={selectedCaseId}
        onRunEncounter={handleRunSimulation}
        isRunning={isRunning}
      />
    </div>
  );
};

export default PatientJourneyFlowPage;
