import React, { useState, useEffect, useRef, useCallback } from 'react';
import { HospitalFlowDiagram } from './HospitalFlowDiagram';
import { VitalsMonitorHUD } from '../dashboard/VitalsMonitorHUD';
import { InternalMedicineConsultModal } from '../specialists/InternalMedicineConsultModal';
import { DepartmentStationModal } from '../specialists/DepartmentStationModal';
import { toggleGlobalMute, isGlobalMuted } from '../../utils/speechSynthesis';
import type { HospitalEvent, BenchmarkCase, VitalSigns } from '../../types';
import { Button } from '../ui/Button';
import { Volume2, VolumeX } from 'lucide-react';
import { AppPage } from '../layout/Templates';

interface PatientJourneyFlowPageProps {
  onBackToPortal?: () => void;
}

export const PatientJourneyFlowPage: React.FC<PatientJourneyFlowPageProps> = () => {
  const [cases, setCases] = useState<BenchmarkCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('CASE-101');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [events, setEvents] = useState<HospitalEvent[]>([]);
  const [activeVitals, setActiveVitals] = useState<VitalSigns | null>(null);
  const [currentPatientName, setCurrentPatientName] = useState<string>('');
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
          // Connected to simulation event stream
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
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        wsRef.current.close();
      }
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
    <AppPage
      title="Patient Journey & Clinical Flow"
      description="Real-time encounter trajectory, department transitions, and interactive clinical simulation stations."
      breadcrumbs={[
        { label: 'Clinical Ops', href: '#' },
        { label: 'Patient Journey & Flow', isCurrent: true },
      ]}
      actions={
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsAudioMuted(toggleGlobalMute())}
            title={isAudioMuted ? 'Unmute voice synthesis' : 'Mute voice synthesis'}
            aria-label={isAudioMuted ? 'Unmute voice synthesis' : 'Mute voice synthesis'}
          >
            {isAudioMuted ? (
              <VolumeX className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
            ) : (
              <Volume2 className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
            )}
          </Button>
        </div>
      }
    >
      {/* 2D Clinical Flow Diagram & Encounter Trajectory */}
      <div className="relative w-full flex flex-col">
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
      </div>

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
    </AppPage>
  );
};

export default PatientJourneyFlowPage;
