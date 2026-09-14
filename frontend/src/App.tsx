import React, { useState, useEffect, useRef } from 'react';
import { HospitalCanvas } from './components/hospital3d/HospitalCanvas';
import { EventStreamHUD } from './components/dashboard/EventStreamHUD';
import { VitalsMonitorHUD } from './components/dashboard/VitalsMonitorHUD';
import { PhysicianReviewDashboard } from './components/dashboard/PhysicianReviewDashboard';
import { CaseSelector } from './components/dashboard/CaseSelector';
import { InternalMedicineConsultModal } from './components/specialists/InternalMedicineConsultModal';
import { PharmacistModal } from './components/specialists/PharmacistModal';
import { DepartmentStationModal } from './components/specialists/DepartmentStationModal';
import { RLDatasetModal } from './components/rl/RLDatasetModal';
import type {
  HospitalEvent,
  ClinicalReport,
  BenchmarkCase,
  PhysicianReviewPayload,
  VitalSigns,
} from './types';

export const App: React.FC = () => {
  // Navigation
  const [activeView, setActiveView] = useState<'HOSPITAL_3D' | 'PHYSICIAN_REVIEW'>('HOSPITAL_3D');

  // Simulation State
  const [cases, setCases] = useState<BenchmarkCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('CASE-101');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [events, setEvents] = useState<HospitalEvent[]>([]);
  const [reports, setReports] = useState<ClinicalReport[]>([]);
  const [activeVitals, setActiveVitals] = useState<VitalSigns | null>(null);
  const [currentPatientName, setCurrentPatientName] = useState<string>('Robert Miller');
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);

  // Modals & Interactive Stations
  const [isConsultOpen, setIsConsultOpen] = useState<boolean>(false);
  const [isPharmacyOpen, setIsPharmacyOpen] = useState<boolean>(false);
  const [departmentStationId, setDepartmentStationId] = useState<string | null>(null);
  const [isRLModalOpen, setIsRLModalOpen] = useState<boolean>(false);

  // 3D Department & Agent Positions
  const [activeDepartment, setActiveDepartment] = useState<string>('RECEPTION');
  const [patientPos, setPatientPos] = useState<[number, number, number]>([-8, 0, -6]);
  const [nursePos, setNursePos] = useState<[number, number, number]>([6, 0, -6]);
  const [doctorPos, setDoctorPos] = useState<[number, number, number]>([6.5, 0, 1]);

  const [patientAction, setPatientAction] = useState<string>('Waiting in Intake');
  const [nurseAction, setNurseAction] = useState<string>('At Nurse Station');
  const [doctorAction, setDoctorAction] = useState<string>('Reviewing Inpatient Charts');
  const [pharmAction, setPharmAction] = useState<string>('Dispensing & Reconciling Prescriptions');

  const wsRef = useRef<WebSocket | null>(null);

  // Fetch initial cases and reports
  useEffect(() => {
    fetch('/api/cases')
      .then((res) => res.json())
      .then((data) => {
        setCases(data);
        if (data.length > 0) {
          setSelectedCaseId(data[0].id);
        }
      })
      .catch((err) => console.error('Failed to load cases:', err));

    fetch('/api/reports')
      .then((res) => res.json())
      .then((data) => setReports(data))
      .catch((err) => console.error('Failed to load reports:', err));

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

  // Update 3D scene representation when events arrive
  const handleIncomingEvent = (evt: HospitalEvent) => {
    setEvents((prev) => [...prev.slice(-100), evt]);

    // Update 3D spatial positions based on event type
    switch (evt.event_type) {
      case 'PATIENT_ARRIVED':
        setActiveDepartment('RECEPTION');
        setPatientPos([-8, 0, -6]);
        setPatientAction('Arrived at ER Reception');
        if (evt.payload.name) setCurrentPatientName(evt.payload.name);
        break;

      case 'NURSE_TRIAGE_STARTED':
      case 'VITALS_RECORDED':
        setActiveDepartment('NURSE_STATION');
        setPatientPos([4, 0, -6]);
        setNursePos([6, 0, -6]);
        setPatientAction('In Triage Bay');
        setNurseAction('Measuring Vital Signs');
        if (evt.payload.heart_rate) {
          setActiveVitals(evt.payload as VitalSigns);
        }
        break;

      case 'TRIAGE_COMPLETED':
        setNurseAction('Paged Attending Physician');
        break;

      case 'DOCTOR_ASSIGNED':
      case 'EXAMINATION_STARTED':
      case 'PATIENT_INTERVIEWED':
        setActiveDepartment('EXAMINATION_ROOM_1');
        setPatientPos([-7, 0, 1]);
        setDoctorPos([-5.5, 0, 1]);
        setPatientAction('Exam Room Bed 1');
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
        setActiveDepartment('PHARMACY');
        setPharmAction('Screening Contraindications & Renal Dosing');
        break;

      case 'PHARMACY_REVIEW_COMPLETED':
      case 'MEDICATION_DISPENSED':
        setActiveDepartment('PHARMACY');
        setPharmAction(evt.summary || 'Medication Orders Reconciled');
        break;

      case 'CLINICAL_REPORT_GENERATED':
        setActiveDepartment('DOCTOR_STATION');
        setDoctorAction('Report Finalized & Queued');
        // Fetch updated reports list
        fetch('/api/reports')
          .then((res) => res.json())
          .then((data) => setReports(data))
          .catch(console.error);
        break;
    }
  };

  // Run a new clinical simulation encounter
  const handleRunSimulation = async () => {
    setIsRunning(true);
    try {
      const res = await fetch('/api/simulation/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: selectedCaseId }),
      });
      const data = await res.json();
      if (data.report) {
        setReports((prev) => [data.report, ...prev.filter((r) => r.id !== data.report.id)]);
      }
    } catch (err) {
      console.error('Failed to run simulation:', err);
    } finally {
      setIsRunning(false);
    }
  };

  // Submit physician review
  const handleSubmitReview = async (reviewPayload: PhysicianReviewPayload) => {
    const res = await fetch('/api/reviews', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reviewPayload),
    });
    if (!res.ok) {
      throw new Error('Failed to submit physician review');
    }
  };

  // Handle station interaction triggers (from pressing [E] or HUD click in 1st person)
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

  return (
    <div className="w-screen h-screen flex flex-col bg-slate-950 overflow-hidden select-none font-sans">
      {/* Top Header Bar */}
      <CaseSelector
        cases={cases}
        selectedCaseId={selectedCaseId}
        onSelectCase={(id) => setSelectedCaseId(id)}
        onRunSimulation={handleRunSimulation}
        isRunning={isRunning}
        activeView={activeView}
        onChangeView={(v) => setActiveView(v)}
        reportsCount={reports.length}
        onOpenConsult={() => setIsConsultOpen(true)}
        onOpenPharmacy={() => setIsPharmacyOpen(true)}
        onOpenRLDataset={() => setIsRLModalOpen(true)}
      />

      {/* Main Body View */}
      <div className="flex-1 relative flex overflow-hidden">
        {activeView === 'HOSPITAL_3D' ? (
          <>
            {/* 3D Hospital Canvas */}
            <HospitalCanvas
              activeDepartment={activeDepartment}
              patientPos={patientPos}
              nursePos={nursePos}
              doctorPos={doctorPos}
              patientAction={patientAction}
              nurseAction={nurseAction}
              doctorAction={doctorAction}
              pharmAction={pharmAction}
              onDepartmentClick={(dept) => setActiveDepartment(dept)}
              onStationInteract={handleStationInteract}
            />

            {/* Floating Glassmorphism Vitals Telemetry */}
            <VitalsMonitorHUD vitals={activeVitals} patientName={currentPatientName} />

            {/* Floating Real-Time Event Feed */}
            <EventStreamHUD events={events} isConnected={isWsConnected} />
          </>
        ) : (
          /* Physician Review Dashboard */
          <PhysicianReviewDashboard
            reports={reports}
            onSubmitReview={handleSubmitReview}
          />
        )}
      </div>

      {/* Internal Medicine Specialist & Harrison's RAG Consultation Modal */}
      <InternalMedicineConsultModal
        isOpen={isConsultOpen}
        onClose={() => setIsConsultOpen(false)}
      />

      {/* Clinical Pharmacy & Medication Safety Modal */}
      <PharmacistModal
        isOpen={isPharmacyOpen}
        onClose={() => setIsPharmacyOpen(false)}
        cases={cases}
      />

      {/* Department Station Inspector Modal (Lab / Radiology / Nurse Triage) */}
      <DepartmentStationModal
        stationId={departmentStationId}
        isOpen={departmentStationId !== null}
        onClose={() => setDepartmentStationId(null)}
        cases={cases}
        selectedCaseId={selectedCaseId}
        onRunEncounter={handleRunSimulation}
        isRunning={isRunning}
      />

      {/* Phase 6: RL / DPO Preference Alignment Corpus Modal */}
      <RLDatasetModal
        isOpen={isRLModalOpen}
        onClose={() => setIsRLModalOpen(false)}
      />
    </div>
  );
};

export default App;
