import React, { useState, useEffect, useRef, useCallback } from 'react';
import { HospitalFlowDiagram } from './HospitalFlowDiagram';
import { VitalsMonitorHUD } from '../dashboard/VitalsMonitorHUD';
import { InternalMedicineConsultModal } from '../specialists/InternalMedicineConsultModal';
import { DepartmentStationModal } from '../specialists/DepartmentStationModal';
import { toggleGlobalMute, isGlobalMuted } from '../../utils/speechSynthesis';
import type { HospitalEvent, BenchmarkCase, VitalSigns } from '../../types';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import {
  Activity,
  ArrowLeft,
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
  const [doctorAction, setDoctorAction] = useState<string>('Reviewing inpatient charts');

  const wsRef = useRef<WebSocket | null>(null);
  const isMountedRef = useRef<boolean>(true);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleIncomingEvent = useCallback((evt: HospitalEvent) => {
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
        setDoctorAction('Conducting clinical exam and interview');
        break;

      case 'RAG_QUERY_INITIATED':
      case 'RAG_KNOWLEDGE_RETRIEVED':
        setDoctorAction("Querying Harrison's Internal Medicine");
        break;

      case 'LAB_ORDERED':
      case 'LAB_RESULT_READY':
        setActiveDepartment('LABORATORY');
        setDoctorAction('Reviewing laboratory biomarkers');
        break;

      case 'DIAGNOSIS_MADE':
      case 'TREATMENT_ORDERED':
        setActiveDepartment('DOCTOR_STATION');
        setDoctorAction('Physician diagnosis established');
        break;

      case 'CLINICAL_REPORT_GENERATED':
        setActiveDepartment('DOCTOR_STATION');
        setDoctorAction('Report finalized and queued');
        break;

      case 'ENCOUNTER_CLOSED':
        setActiveDepartment('DISCHARGE');
        setDoctorAction('Patient discharged and route closed');
        break;
    }
  }, []);

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
    isMountedRef.current = true;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/simulation`;

    const connectWs = () => {
      if (!isMountedRef.current) return;
      try {
        const socket = new WebSocket(wsUrl);
        wsRef.current = socket;

        socket.onopen = () => {
          if (isMountedRef.current) setIsWsConnected(true);
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
          if (isMountedRef.current) {
            setIsWsConnected(false);
            if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = setTimeout(connectWs, 3000);
          }
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
      isMountedRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [handleIncomingEvent]);

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
    <div className="w-full h-full flex flex-col bg-[var(--ak-color-bg-app)] overflow-hidden select-none font-sans relative isolate text-[var(--ak-color-text-primary)]">
      {/* Top Clinical Header */}
      <header className="h-14 bg-[var(--ak-color-bg-surface)] border-b border-[var(--ak-color-border-subtle)] px-4 flex items-center justify-between z-30 shrink-0">
        {/* Left: Branding & Back Button */}
        <div className="flex items-center gap-3">
          {onBackToPortal && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onBackToPortal}
              leadingIcon={<ArrowLeft className="w-3.5 h-3.5" />}
              title="Return to Clinical Management Portal"
            >
              Back to portal
            </Button>
          )}

          {onBackToPortal && <div className="h-4 w-px bg-[var(--ak-color-border-subtle)] mx-1" />}

          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[var(--ak-color-primary-soft)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-primary)]">
              <Activity className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <span className="text-sm font-semibold text-[var(--ak-color-text-primary)]">
                Clinical flow architecture and patient journey
              </span>
              <span className="hidden sm:inline-block ml-2">
                <Badge variant="success" size="sm">
                  2D clinical pathway
                </Badge>
              </span>
            </div>
          </div>
        </div>

        {/* Center: Real-Time Department Tracker */}
        <div className="hidden md:flex items-center gap-2 bg-[var(--ak-color-bg-subtle)] px-3.5 py-1 rounded-full border border-[var(--ak-color-border-subtle)] text-xs">
          <span className={`w-2 h-2 rounded-full ${isWsConnected ? 'bg-[var(--ak-color-success)] animate-pulse' : 'bg-[var(--ak-color-warning)]'}`} />
          <span className="text-[var(--ak-color-text-muted)]">Current station:</span>
          <span className="text-[var(--ak-color-text-primary)] font-medium font-mono">{activeDepartment.replace(/_/g, ' ')}</span>
        </div>

        {/* Right: Audio Toggle */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsAudioMuted(toggleGlobalMute())}
            title={isAudioMuted ? 'Unmute voice synthesis' : 'Mute voice synthesis'}
          >
            {isAudioMuted ? <VolumeX className="w-4 h-4 text-[var(--ak-color-text-muted)]" /> : <Volume2 className="w-4 h-4 text-[var(--ak-color-primary)]" />}
          </Button>
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

        {/* Floating Vitals Telemetry */}
        <VitalsMonitorHUD vitals={activeVitals} patientName={currentPatientName} />
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
