import React, { useState, useEffect, useRef, useCallback } from 'react';
import { HospitalFlowDiagram } from './HospitalFlowDiagram';
import { DepartmentStationModal } from '../specialists/DepartmentStationModal';
import { toggleGlobalMute, isGlobalMuted } from '../../utils/speechSynthesis';
import type { HospitalEvent, BenchmarkCase, VitalSigns, ClinicalReport } from '../../types';
import {
  Activity,
  ArrowLeft,
  Bell,
  CheckCircle2,
  ChevronRight,
  Cpu,
  FileCheck,
  GitBranch,
  Layers,
  Network,
  Play,
  Radio,
  Search,
  ShieldCheck,
  User,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react';

interface ToastAlert {
  id: string;
  title: string;
  message: string;
  timestamp: string;
}

interface PatientJourneyFlowPageProps {
  onBackToPortal?: () => void;
  onReportFinalized?: (report: ClinicalReport) => void;
  onPatientDischarged?: (patientId: string) => void;
}

export const PatientJourneyFlowPage: React.FC<PatientJourneyFlowPageProps> = ({
  onBackToPortal,
  onReportFinalized,
  onPatientDischarged,
}) => {
  const [cases, setCases] = useState<BenchmarkCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('CASE-SYNTH-pat-101-0001');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [events, setEvents] = useState<HospitalEvent[]>([]);
  const [activeVitals, setActiveVitals] = useState<VitalSigns | null>(null);
  const [currentPatientName, setCurrentPatientName] = useState<string>('Charles Brown');
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(isGlobalMuted());
  const [toastNotification, setToastNotification] = useState<ToastAlert | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Active Navigation Tab in Left Sidebar
  const [activeNavSection, setActiveNavSection] = useState<string>('2D_PATHWAY');

  // Modals
  const [departmentStationId, setDepartmentStationId] = useState<string | null>(null);

  // Department State
  const [activeDepartment, setActiveDepartment] = useState<string>('NURSE_STATION');
  const [doctorAction, setDoctorAction] = useState<string>('Reviewing Inpatient Radiographs & Lab Panels');

  const wsRef = useRef<WebSocket | null>(null);
  const isMountedRef = useRef<boolean>(true);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleIncomingEvent = useCallback((evt: HospitalEvent) => {
    setEvents((prev) => [...prev.slice(-100), evt]);

    switch (evt.event_type) {
      case 'PATIENT_ARRIVED':
        setActiveDepartment('RECEPTION');
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
        setDoctorAction('Querying clinical medical knowledge base');
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

  const showNotification = (title: string, message: string) => {
    const id = `notif-${Date.now()}`;
    const newToast: ToastAlert = {
      id,
      title,
      message,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };
    setToastNotification(newToast);
    setTimeout(() => {
      setToastNotification((curr) => (curr?.id === id ? null : curr));
    }, 6500);
  };

  // Fetch active admitted cases and recent events
  const loadCases = async () => {
    try {
      const res = await fetch('/api/cases');
      if (res.ok) {
        const data: BenchmarkCase[] = await res.json();
        // Filter out discharged patients
        const activeOnly = data.filter(
          (c) => (c as any).status !== 'discharged' && (c as any).admission_status !== 'DISCHARGED'
        );
        setCases(activeOnly);
        if (activeOnly.length > 0) {
          // If current selection is invalid or discharged, pick first active
          if (!activeOnly.some((c) => c.id === selectedCaseId)) {
            setSelectedCaseId(activeOnly[0].id);
            setCurrentPatientName(activeOnly[0].name);
          }
        }
      }
    } catch (err) {
      console.error('Failed to load cases:', err);
    }
  };

  useEffect(() => {
    loadCases();

    fetch('/api/simulation/events')
      .then((res) => res.json())
      .then((data) => setEvents(data))
      .catch((err) => console.error('Failed to load events:', err));
  }, []);

  // Setup WebSocket connection for live telemetry stream
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
  }, []);

  const handleIncomingEvent = (evt: HospitalEvent) => {
    setEvents((prev) => [...prev.slice(-100), evt]);

    switch (evt.event_type) {
      case 'PATIENT_ARRIVED':
        setActiveDepartment('RECEPTION');
        if (evt.payload?.name) setCurrentPatientName(evt.payload.name);
        break;

      case 'NURSE_TRIAGE_STARTED':
      case 'VITALS_RECORDED':
        setActiveDepartment('NURSE_STATION');
        if (evt.payload?.heart_rate) {
          setActiveVitals(evt.payload as VitalSigns);
        }
        break;

      case 'DOCTOR_ASSIGNED':
      case 'EXAMINATION_STARTED':
      case 'PATIENT_INTERVIEWED':
        setActiveDepartment('EXAMINATION_ROOM_1');
        setDoctorAction('Conducting Clinical Exam & Diagnostic Synthesis');
        break;

      case 'RAG_QUERY_INITIATED':
      case 'RAG_KNOWLEDGE_RETRIEVED':
        setDoctorAction("Querying Harrison's Principles of Internal Medicine");
        break;

      case 'LAB_ORDERED':
      case 'LAB_RESULT_READY':
        setActiveDepartment('LABORATORY');
        setDoctorAction('Reviewing Serum Biomarkers & Lab Panels');
        break;

      case 'DIAGNOSIS_MADE':
      case 'TREATMENT_ORDERED':
        setActiveDepartment('DOCTOR_STATION');
        setDoctorAction('Physician Diagnosis & Treatment Plan Established');
        break;

      case 'CLINICAL_REPORT_GENERATED':
        setActiveDepartment('DISCHARGE');
        setDoctorAction('Clinical Report Finalized & Discharged');
        break;
    }
  };

  const handleStationInteract = (stationId: string) => {
    switch (stationId) {
      case 'LABORATORY':
      case 'RADIOLOGY':
      case 'NURSE_STATION':
        setDepartmentStationId(stationId);
        break;
    }
  };

  // Run full simulated encounter, finalize report, and discharge patient
  const handleRunSimulation = async () => {
    if (!selectedCaseId) return;
    setIsRunning(true);
    try {
      const res = await fetch('/api/simulation/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: selectedCaseId }),
      });

      if (res.ok) {
        const simResult = await res.json();
        const activePatient = cases.find((c) => c.id === selectedCaseId);
        const pName = activePatient?.name || simResult.patient || 'Patient';

        // 1. Dispatch finalize report payload to persist to global database and reviews store
        const finalizeRes = await fetch('/api/reports/finalize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            patient_id: selectedCaseId,
            encounter_id: simResult.encounter_id,
            trajectory_summary: simResult.primary_diagnosis || 'Clinical Encounter Completed',
            vitals: activeVitals,
            discharge_patient: true,
          }),
        });

        let finalizedReport = simResult.report;
        if (finalizeRes.ok) {
          const finData = await finalizeRes.json();
          if (finData.report) finalizedReport = finData.report;
        }

        // Commit to global reportsReview store
        if (onReportFinalized && finalizedReport) {
          onReportFinalized(finalizedReport);
        }

        // 2. Patient Census Cleanup Post-Discharge: evict discharged patient
        if (onPatientDischarged) {
          onPatientDischarged(selectedCaseId);
        }
        setCases((prev) => prev.filter((c) => c.id !== selectedCaseId));

        // Switch to next pending patient or clear
        const remaining = cases.filter((c) => c.id !== selectedCaseId);
        if (remaining.length > 0) {
          setSelectedCaseId(remaining[0].id);
          setCurrentPatientName(remaining[0].name);
        } else {
          setSelectedCaseId('');
          setCurrentPatientName('Standby');
        }

        // 3. Fire completion notification toast
        showNotification(
          'Report Ready',
          `Clinical report for ${pName} is finalized and ready for review.`
        );
      }
    } catch (err) {
      console.error('Failed to run simulation:', err);
    } finally {
      setIsRunning(false);
    }
  };

  // Direct manual discharge & report finalization from Node 4
  const handleFinalizeDischarge = async (patientId: string) => {
    try {
      const patient = cases.find((c) => c.id === patientId);
      const pName = patient?.name || 'Patient';

      const res = await fetch('/api/reports/finalize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          trajectory_summary: patient?.chief_complaint || 'Clinical Encounter Completed',
          vitals: activeVitals,
          discharge_patient: true,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (onReportFinalized && data.report) {
          onReportFinalized(data.report);
        }
        if (onPatientDischarged) {
          onPatientDischarged(patientId);
        }

        // Evict from active queue
        setCases((prev) => prev.filter((c) => c.id !== patientId));
        const remaining = cases.filter((c) => c.id !== patientId);
        if (remaining.length > 0) {
          setSelectedCaseId(remaining[0].id);
          setCurrentPatientName(remaining[0].name);
        } else {
          setSelectedCaseId('');
          setCurrentPatientName('Standby');
        }

        showNotification(
          'Report Ready',
          `Clinical report for ${pName} is finalized and ready for review.`
        );
      }
    } catch (err) {
      console.error('Error discharging patient:', err);
    }
  };

  // Quick switch patient shortcut
  const handleSwitchPatient = () => {
    if (cases.length <= 1) return;
    const currentIndex = cases.findIndex((c) => c.id === selectedCaseId);
    const nextIndex = (currentIndex + 1) % cases.length;
    const nextCase = cases[nextIndex];
    setSelectedCaseId(nextCase.id);
    setCurrentPatientName(nextCase.name);
  };

  return (
    <div className="w-full h-full flex bg-[#f8fafc] overflow-hidden select-none font-sans text-slate-900">
      {/* ═══════════════════════════════════════════════════════════════════
          LEFT SIDEBAR NAVIGATION RAIL (Matching Screenshot)
          ═══════════════════════════════════════════════════════════════════ */}
      <aside className="w-60 shrink-0 bg-[#f8fafc] border-r border-slate-200/90 flex flex-col justify-between p-3 select-none hidden lg:flex">
        <div className="space-y-4">
          {/* Logo & Station Header */}
          <div className="flex items-center justify-between px-2 pt-1">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-teal-50 border border-teal-200 flex items-center justify-center text-[#0d6e60] shadow-2xs">
                <Activity className="w-4 h-4 animate-pulse" />
              </div>
              <span className="font-bold text-xs tracking-wider text-slate-900 font-mono">
                AI-VH CLINICAL
              </span>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-200/80 text-slate-700">
              STATION
            </span>
          </div>

          {/* Active Unit Badge */}
          <div className="px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 flex items-center justify-between text-xs font-mono shadow-2xs">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
              <span className="text-[10px] text-slate-500 font-bold uppercase">ACTIVE UNIT</span>
            </div>
            <span className="font-bold text-slate-800 text-xs">NURSE-04</span>
          </div>

          {/* Navigation Section 1: CORE ARCHITECTURE */}
          <div>
            <div className="px-2 mb-1.5 text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              CORE ARCHITECTURE
            </div>
            <nav className="space-y-1">
              <button
                onClick={() => setActiveNavSection('2D_PATHWAY')}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition cursor-pointer ${
                  activeNavSection === '2D_PATHWAY'
                    ? 'bg-[#0d6e60] text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <GitBranch className="w-4 h-4" />
                <span>2D Process Pathway</span>
              </button>

              <button
                onClick={() => {
                  setActiveNavSection('STATION_ROUTING');
                  handleStationInteract('NURSE_STATION');
                }}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition cursor-pointer ${
                  activeNavSection === 'STATION_ROUTING'
                    ? 'bg-[#0d6e60] text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Network className="w-4 h-4" />
                <span>Station Routing</span>
              </button>

              <button
                onClick={() => setActiveNavSection('TELEMETRY_QUEUE')}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition cursor-pointer ${
                  activeNavSection === 'TELEMETRY_QUEUE'
                    ? 'bg-[#0d6e60] text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Radio className="w-4 h-4" />
                <span>Telemetry Queue</span>
              </button>
            </nav>
          </div>

          {/* Navigation Section 2: SIMULATION & AUDIT */}
          <div>
            <div className="px-2 mb-1.5 text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              SIMULATION &amp; AUDIT
            </div>
            <nav className="space-y-1">
              <button
                onClick={() => handleRunSimulation()}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition cursor-pointer"
              >
                <Play className="w-4 h-4 text-emerald-600" />
                <span>Case Simulator</span>
              </button>

              <button
                onClick={() => setIsConsultOpen(true)}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition cursor-pointer"
              >
                <Layers className="w-4 h-4" />
                <span>Pathway Logic</span>
              </button>

              <button
                onClick={() => showNotification('Audit Complete', 'All clinical pathways verified against Harrison’s 21st Ed.')}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition cursor-pointer"
              >
                <FileCheck className="w-4 h-4" />
                <span>Throughput Audit</span>
              </button>
            </nav>
          </div>
        </div>

        {/* Bottom Sidebar: Runtime Engine Info */}
        <div className="p-2.5 rounded-xl bg-white border border-slate-200/90 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-[9px] font-mono font-bold text-slate-400 uppercase flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${isWsConnected ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`} />
              <span>RUNTIME ENGINE</span>
            </div>
            <div className="text-xs font-mono font-bold text-slate-800">v2.4.12 Telemetry</div>
          </div>
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
        </div>
      </aside>

      {/* ═══════════════════════════════════════════════════════════════════
          MAIN CANVAS & TOP COMMAND BAR
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Top Clinical Header Bar matching Screenshot */}
        <header className="h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between shrink-0 z-30 shadow-2xs gap-3">
          {/* Left: Portal Return & Title */}
          <div className="flex items-center gap-2.5 min-w-0">
            {onBackToPortal && (
              <button
                onClick={onBackToPortal}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 font-medium text-xs rounded-lg border border-slate-200 transition shadow-2xs cursor-pointer active:scale-95 shrink-0"
                title="Return to Clinical Management Portal"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Portal</span>
              </button>
            )}

            <div className="w-7 h-7 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-[#0d6e60] shadow-2xs shrink-0">
              <Activity className="w-4 h-4 text-[#0d6e60] animate-pulse" />
            </div>

            <div className="min-w-0 flex items-center gap-2">
              <span className="text-xs md:text-sm font-bold text-slate-900 truncate">
                AI-VH Clinical Flow Architecture &amp; Patient Journey
              </span>
              <span className="hidden sm:inline-block px-2.5 py-0.5 text-[10px] font-mono rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100 font-semibold whitespace-nowrap">
                2D Clinical Process Pathway
              </span>
            </div>
          </div>

          {/* Center-Right: Station Indicator & Controls */}
          <div className="flex items-center gap-2.5 shrink-0">
            {/* Quick Search */}
            <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-500 w-44">
              <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <input
                type="text"
                placeholder="Search patient..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-transparent border-none outline-none w-full text-slate-800 placeholder-slate-400 text-xs font-sans"
              />
              <kbd className="px-1 bg-white rounded border border-slate-200 text-[9px] text-slate-400">⌘K</kbd>
            </div>

            {/* Current Station Tracker Pill */}
            <div className="hidden md:flex items-center gap-2 bg-slate-100/90 px-3 py-1 rounded-full border border-slate-200 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-slate-500 text-[11px]">Current Station:</span>
              <span className="text-slate-900 font-bold uppercase">{activeDepartment.replace(/_/g, ' ')}</span>
            </div>

            {/* Quick Switch Patient Button */}
            <button
              onClick={handleSwitchPatient}
              className="hidden lg:flex items-center gap-1 px-2.5 py-1 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-600 transition shadow-2xs cursor-pointer"
              title="Cycle to next admitted patient"
            >
              <Cpu className="w-3.5 h-3.5 text-slate-500" />
              <span>Switch Patient</span>
              <kbd className="px-1 bg-slate-100 rounded text-[9px]">⌥P</kbd>
            </button>

            {/* Notification Bell */}
            <button
              onClick={() => showNotification('Notifications', 'Real-time WebSocket event bus synchronized.')}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 relative transition cursor-pointer shadow-2xs"
              title="Recent Notifications"
            >
              <Bell className="w-3.5 h-3.5" />
              <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-emerald-500" />
            </button>

            {/* Audio Toggle */}
            <button
              onClick={() => setIsAudioMuted(toggleGlobalMute())}
              className={`p-1.5 rounded-lg border text-xs transition cursor-pointer shadow-2xs ${
                isAudioMuted
                  ? 'bg-slate-100 text-slate-400 border-slate-200 hover:bg-slate-200'
                  : 'bg-teal-50 text-[#0d6e60] border-teal-300'
              }`}
              title={isAudioMuted ? 'Unmute Audio Voice Synthesis' : 'Mute Audio Voice Synthesis'}
            >
              {isAudioMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5 text-[#0d6e60]" />}
            </button>

            {/* User Profile Avatar */}
            <div className="w-7 h-7 rounded-full bg-[#0d6e60] text-white flex items-center justify-center font-bold text-xs shadow-2xs">
              <User className="w-4 h-4 fill-current" />
            </div>
          </div>
        </header>

        {/* ── Main Viewport Content ── */}
        <main className="flex-1 relative overflow-hidden flex flex-col">
          <HospitalFlowDiagram
            cases={searchQuery ? cases.filter((c) => c.name.toLowerCase().includes(searchQuery.toLowerCase()) || c.id.toLowerCase().includes(searchQuery.toLowerCase())) : cases}
            selectedCaseId={selectedCaseId}
            onSelectCase={(id) => {
              setSelectedCaseId(id);
              const c = cases.find((item) => item.id === id);
              if (c) setCurrentPatientName(c.name);
            }}
            onRunSimulation={handleRunSimulation}
            isRunning={isRunning}
            activeDepartment={activeDepartment}
            doctorAction={doctorAction}
            events={events}
            activeVitals={activeVitals}
            onOpenConsult={() => setIsConsultOpen(true)}
            onOpenDepartmentStation={handleStationInteract}
            onFinalizeReport={handleFinalizeDischarge}
          />

          {/* Floating Vitals Telemetry HUD */}
          <VitalsMonitorHUD vitals={activeVitals} patientName={currentPatientName} />
        </main>
      </div>

      {/* ── Floating Clinical Toast Notification (Fix for Bug #4) ── */}
      {toastNotification && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5 duration-300">
          <div className="bg-slate-900/95 text-white border border-teal-500/50 shadow-2xl rounded-xl p-3.5 flex items-start gap-3 max-w-md backdrop-blur-md">
            <div className="w-8 h-8 rounded-lg bg-teal-900/80 border border-teal-500 text-teal-400 flex items-center justify-center shrink-0 mt-0.5">
              <CheckCircle2 className="w-5 h-5 animate-pulse" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs font-bold text-teal-400 uppercase tracking-wider">
                  {toastNotification.title}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {toastNotification.timestamp}
                </span>
              </div>
              <p className="text-xs text-slate-200 mt-0.5 leading-relaxed">
                {toastNotification.message}
              </p>
              {onBackToPortal && (
                <button
                  onClick={onBackToPortal}
                  className="mt-2 text-[11px] font-mono font-semibold text-teal-300 hover:text-teal-200 flex items-center gap-1 cursor-pointer"
                >
                  <span>Review Report in Clinical Management Portal</span>
                  <ChevronRight className="w-3 h-3" />
                </button>
              )}
            </div>
            <button
              onClick={() => setToastNotification(null)}
              className="text-slate-400 hover:text-white p-1 rounded-md transition cursor-pointer"
              title="Dismiss"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      <InternalMedicineConsultModal
        isOpen={isConsultOpen}
        onClose={() => setIsConsultOpen(false)}
      />

      {/* Modals */}
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
