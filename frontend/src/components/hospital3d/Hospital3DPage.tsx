import React, { useState, useEffect, useRef } from 'react';
import { HospitalCanvas } from './HospitalCanvas';
import { HospitalFlowDiagram } from '../diagram/HospitalFlowDiagram';
import { EventStreamHUD } from '../dashboard/EventStreamHUD';
import { VitalsMonitorHUD } from '../dashboard/VitalsMonitorHUD';
import { InternalMedicineConsultModal } from '../specialists/InternalMedicineConsultModal';
import { PharmacistModal } from '../specialists/PharmacistModal';
import { DepartmentStationModal } from '../specialists/DepartmentStationModal';
import { InpatientTelemetryModal } from '../dashboard/InpatientTelemetryModal';
import { toggleGlobalMute, isGlobalMuted } from '../../utils/speechSynthesis';
import type { HospitalEvent, BenchmarkCase, VitalSigns } from '../../types';

interface Hospital3DPageProps {
  onBackToPortal: () => void;
}

export const Hospital3DPage: React.FC<Hospital3DPageProps> = ({ onBackToPortal }) => {
  const [viewMode, setViewMode] = useState<'DIAGRAM' | '3D'>('DIAGRAM');
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
  const [isPharmacyOpen, setIsPharmacyOpen] = useState<boolean>(false);
  const [departmentStationId, setDepartmentStationId] = useState<string | null>(null);
  const [isInpatientOpen, setIsInpatientOpen] = useState<boolean>(false);

  // 3D Department & Agent Position
  const [activeDepartment, setActiveDepartment] = useState<string>('RECEPTION');
  const [doctorPos, setDoctorPos] = useState<[number, number, number]>([6.5, 0, 1]);
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
        setDoctorPos([-5.5, 0, 1]);
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
        setDoctorPos([6.5, 0, 1]);
        setDoctorAction('MedGemma Diagnosis Established');
        break;

      case 'PHARMACY_REVIEW_INITIATED':
      case 'PHARMACY_REVIEW_COMPLETED':
      case 'MEDICATION_DISPENSED':
        setActiveDepartment('PHARMACY');
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
      case 'PHARMACY':
        setIsPharmacyOpen(true);
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
    <div className="w-screen h-screen flex flex-col bg-slate-950 overflow-hidden select-none font-sans relative">
      {/* 3D Simulation Top Command Header */}
      <header className="h-14 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 flex items-center justify-between z-30 shadow-lg">
        {/* Left: Branding & Back to Portal Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToPortal}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-cyan-300 font-medium text-xs rounded-lg border border-slate-700 transition shadow"
            title="Return to Clinical Management & Data Portal"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>Back to Management Portal</span>
          </button>

          <div className="h-4 w-px bg-slate-700 mx-1" />

          <div className="flex items-center gap-2">
            <span className="text-sm font-bold bg-gradient-to-r from-cyan-400 via-sky-400 to-blue-500 bg-clip-text text-transparent">
              AI-VH Clinical Flow Architecture
            </span>
            <span className={`px-2 py-0.5 text-[10px] font-mono rounded border ${
              viewMode === 'DIAGRAM'
                ? 'bg-cyan-950 text-cyan-400 border-cyan-800/60'
                : 'bg-indigo-950 text-indigo-400 border-indigo-800/60'
            }`}>
              {viewMode === 'DIAGRAM' ? '2D Process Flow' : '3D Spatial View'}
            </span>
          </div>
        </div>

        {/* Center: Live Status & View Mode Switcher */}
        <div className="hidden md:flex items-center gap-3">
          {/* View Switcher Controls */}
          <div className="bg-slate-950/90 p-0.5 rounded-lg border border-slate-800 flex items-center">
            <button
              onClick={() => setViewMode('DIAGRAM')}
              className={`px-3 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
                viewMode === 'DIAGRAM'
                  ? 'bg-cyan-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>📊</span>
              <span>Flow Diagram</span>
            </button>
            <button
              onClick={() => setViewMode('3D')}
              className={`px-3 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
                viewMode === '3D'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>🌐</span>
              <span>3D Spatial</span>
            </button>
          </div>

          <div className="flex items-center gap-2 bg-slate-950/80 px-3 py-1 rounded-full border border-slate-800 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-400">Department:</span>
            <span className="text-slate-200 font-semibold">{activeDepartment.replace(/_/g, ' ')}</span>
          </div>
        </div>

        {/* Right: Quick Action Modals & Audio */}
        <div className="flex items-center gap-2">
          {/* Central Telemetry */}
          <button
            onClick={() => setIsInpatientOpen(true)}
            className="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-rose-300 text-xs rounded border border-rose-900/40 flex items-center gap-1.5 transition"
            title="Open 4-Bed Central Inpatient Telemetry Console"
          >
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span>Telemetry Console</span>
          </button>

          {/* Specialist Consult */}
          <button
            onClick={() => setIsConsultOpen(true)}
            className="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-cyan-300 text-xs rounded border border-cyan-900/40 transition"
          >
            Dr. Vance RAG
          </button>

          {/* Pharmacy Safety */}
          <button
            onClick={() => setIsPharmacyOpen(true)}
            className="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-amber-300 text-xs rounded border border-amber-900/40 transition"
          >
            Pharmacy Safety
          </button>

          {/* Audio Mute Toggle */}
          <button
            onClick={() => setIsAudioMuted(toggleGlobalMute())}
            className={`p-1.5 rounded border text-xs transition ${
              isAudioMuted
                ? 'bg-slate-800 text-slate-500 border-slate-700'
                : 'bg-cyan-950 text-cyan-400 border-cyan-800'
            }`}
            title={isAudioMuted ? 'Unmute Audio Voice Synthesis' : 'Mute Audio Voice Synthesis'}
          >
            {isAudioMuted ? '🔇' : '🔊'}
          </button>
        </div>
      </header>

      {/* Main Viewport: 2D Flow Diagram (Default) or 3D Spatial Canvas */}
      <main className="flex-1 relative overflow-hidden flex flex-col">
        {viewMode === 'DIAGRAM' ? (
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
            onOpenPharmacy={() => setIsPharmacyOpen(true)}
            onOpenTelemetry={() => setIsInpatientOpen(true)}
            onOpenDepartmentStation={handleStationInteract}
            onToggleTo3D={() => setViewMode('3D')}
          />
        ) : (
          <HospitalCanvas
            activeDepartment={activeDepartment}
            doctorPos={doctorPos}
            doctorAction={doctorAction}
            onDepartmentClick={(dept) => setActiveDepartment(dept)}
            onStationInteract={handleStationInteract}
          />
        )}

        {/* Floating Glassmorphism Vitals Telemetry (available in both views) */}
        <VitalsMonitorHUD vitals={activeVitals} patientName={currentPatientName} />

        {/* Floating Real-Time Event Feed (available in both views) */}
        <EventStreamHUD events={events} isConnected={isWsConnected} />
      </main>

      {/* Modals */}
      <InternalMedicineConsultModal
        isOpen={isConsultOpen}
        onClose={() => setIsConsultOpen(false)}
      />

      <PharmacistModal
        isOpen={isPharmacyOpen}
        onClose={() => setIsPharmacyOpen(false)}
        cases={cases}
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

      <InpatientTelemetryModal
        isOpen={isInpatientOpen}
        onClose={() => setIsInpatientOpen(false)}
      />
    </div>
  );
};

export default Hospital3DPage;
