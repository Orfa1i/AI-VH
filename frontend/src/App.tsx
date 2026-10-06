import React, { useState, useEffect } from 'react';
import { CaseIntakeAdmissionSection } from './components/management/CaseIntakeAdmissionSection';
import { PatientDirectorySection } from './components/management/PatientDirectorySection';
import { StaffManagementSection } from './components/management/StaffManagementSection';
import { KnowledgeSearchSection } from './components/management/KnowledgeSearchSection';
import { PhysicianReviewDashboard } from './components/dashboard/PhysicianReviewDashboard';
import { DoctorReviewSection } from './components/review/DoctorReviewSection';
import { DepartmentBoardSection } from './components/hospital/DepartmentBoardSection';
import { DepartmentBoard3DSection } from './components/hospital3d/DepartmentBoard3DSection';
import { InternalMedicineConsultModal } from './components/specialists/InternalMedicineConsultModal';
import { RLDatasetModal } from './components/rl/RLDatasetModal';
import { PolicyBenchmarkModal } from './components/rl/PolicyBenchmarkModal';
import { ReviewedReportsSection } from './components/reviewing/ReviewedReportsSection';
import { LeftNotificationDrawer } from './components/notifications/LeftNotificationDrawer';
import { ActiveEncounterProgressBar } from './components/simulation/ActiveEncounterProgressBar';
import { PatientJourneyFlowPage } from './components/diagram/PatientJourneyFlowPage';
import { DesignSystemShowcase } from './pages/DesignSystemShowcase';
import { toggleGlobalMute, isGlobalMuted } from './utils/speechSynthesis';
import {
  Activity,
  BedDouble,
  Box,
  Building2,
  Clock,
  FileText,
  FileCheck2,
  Radio,
  Scale,
  Search,
  Sparkles,
  Stethoscope,
  Terminal,
  Users,
  Volume2,
  VolumeX,
} from 'lucide-react';
import type {
  BenchmarkCase,
  ClinicalReport,
  PhysicianReviewPayload,
  PatientRecord,
  HospitalEvent,
} from './types';

type PortalTab = 'INTAKE' | 'PATIENTS' | 'STAFF' | 'REPORTS' | 'REVIEW' | 'REVIEWING' | 'WARDS' | 'HOSPITAL3D' | 'KNOWLEDGE' | 'BENCHMARK' | 'DESIGN_SYSTEM';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PortalTab>('INTAKE');

  // Shared Data State
  const [cases, setCases] = useState<BenchmarkCase[]>([]);
  const [reports, setReports] = useState<ClinicalReport[]>([]);
  const [reviewedCount, setReviewedCount] = useState<number>(0);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [patientRefreshCounter, setPatientRefreshCounter] = useState<number>(0);
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(isGlobalMuted());
  const [currentTime, setCurrentTime] = useState<string>('');


  // Quick Action Modals
  const [isConsultOpen, setIsConsultOpen] = useState<boolean>(false);
  const [isRLModalOpen, setIsRLModalOpen] = useState<boolean>(false);
  const [isBenchmarkOpen, setIsBenchmarkOpen] = useState<boolean>(false);
  const [isJourneyOpen, setIsJourneyOpen] = useState<boolean>(false);

  // Telemetry & Simulation States
  const [events, setEvents] = useState<HospitalEvent[]>([]);
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulatingPatientName, setSimulatingPatientName] = useState<string>('Active Encounter');

  // Live Clock Ticker
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // Hash Navigation listener
  useEffect(() => {
    const handleUrlRoute = () => {
      const path = window.location.pathname.toLowerCase();
      const hash = window.location.hash.toLowerCase();
      if (path === '/3d' || hash === '#3d') {
        setActiveTab('HOSPITAL3D');
      }
      if (path === '/journey' || hash === '#journey') {
        setIsJourneyOpen(true);
      }
    };
    handleUrlRoute();
    window.addEventListener('popstate', handleUrlRoute);
    window.addEventListener('hashchange', handleUrlRoute);
    return () => {
      window.removeEventListener('popstate', handleUrlRoute);
      window.removeEventListener('hashchange', handleUrlRoute);
    };
  }, []);

  // Real-time Event Telemetry Listener for Left Notification Drawer
  useEffect(() => {
    fetch('/api/simulation/events')
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setEvents(data);
      })
      .catch((err) => console.error('Failed to load initial events:', err));

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/simulation`;
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setIsWsConnected(true);
      ws.onclose = () => setIsWsConnected(false);
      ws.onerror = () => setIsWsConnected(false);
      ws.onmessage = (event) => {
        try {
          const parsed: HospitalEvent = JSON.parse(event.data);
          setEvents((prev) => [...prev.slice(-99), parsed]);
        } catch (e) {
          console.error('Failed to parse WS event:', e);
        }
      };
    } catch (err) {
      console.warn('WS connection error:', err);
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Fetch initial cases, pending reports, and reviewed count
  const refreshData = async () => {
    try {
      const [cRes, rRes, revRes] = await Promise.all([
        fetch('/api/cases'),
        fetch('/api/reports/pending'),
        fetch('/api/reports/reviewed'),
      ]);
      if (cRes.ok) setCases(await cRes.json());
      if (rRes.ok) setReports(await rRes.json());
      if (revRes.ok) {
        const revData = await revRes.json();
        setReviewedCount(Array.isArray(revData) ? revData.length : 0);
      }
    } catch (err) {
      console.error('Failed to load portal data:', err);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  // Submit physician review
  const handleSubmitReview = async (reviewPayload: PhysicianReviewPayload) => {
    setIsSubmittingReview(true);
    try {
      const res = await fetch('/api/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reviewPayload),
      });
      if (!res.ok) {
        throw new Error('Failed to submit physician review');
      }
      await refreshData();
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handlePatientAdmitted = (_patient: PatientRecord) => {
    setPatientRefreshCounter((prev) => prev + 1);
    refreshData();
  };

  const handleAdmitAndSimulate = async (caseId: string, patientName?: string) => {
    setIsSimulating(true);
    const targetCase = cases.find((c) => c.id === caseId);
    setSimulatingPatientName(patientName || targetCase?.name || 'Active Patient');
    try {
      await fetch('/api/simulation/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: caseId }),
      });
      await refreshData();
      setActiveTab('REPORTS');
    } catch (err) {
      console.error('Error simulating encounter:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="w-screen h-screen flex flex-col bg-[#f8fafc] overflow-hidden font-sans select-none text-slate-900 telemetry-grid">
      {/* Top Clinical Command Horizon Header */}
      <header className="h-16 px-5 border-b border-slate-200 bg-white/95 backdrop-blur-md flex items-center justify-between z-30 shrink-0 shadow-xs">
        {/* Left: Branding & Real-Time System Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 shadow-xs">
              <Terminal className="w-4 h-4 text-sky-600 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold tracking-wider text-slate-900 uppercase font-mono">
                  METROPOLITAN GENERAL
                </span>
                <span className="text-[10px] text-sky-700 font-mono tracking-widest font-bold">
                  // CLINICAL COMMAND HORIZON
                </span>
              </div>
              <p className="text-[10px] text-slate-500 font-mono tracking-tight flex items-center gap-2">
                <span>Autonomous Multi-Agent Clinical Operating System</span>
                <span className="text-slate-300">•</span>
                <span className="text-sky-700">Harrison's 21st Ed & Braunwald's (47.8k Chunks)</span>
              </p>
            </div>
          </div>

        </div>

        {/* Right: Live Ticker & Voice Toggle */}
        <div className="flex items-center gap-3">
          {/* Live UTC Clock */}
          <div className="hidden 2xl:flex items-center gap-1.5 font-mono text-xs text-slate-600 px-2.5 py-1 bg-slate-100/90 border border-slate-200 rounded">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-800 font-semibold">{currentTime || '12:00:00'}</span>
            <span className="text-[10px] text-slate-400">UTC</span>
          </div>

          {/* Audio Voice Synthesizer Toggle */}
          <button
            onClick={() => setIsAudioMuted(toggleGlobalMute())}
            title={isAudioMuted ? 'Unmute Clinical Voice Audio' : 'Mute Clinical Voice Audio'}
            className={`p-1.5 rounded-lg border text-xs transition cursor-pointer ${
              isAudioMuted
                ? 'text-slate-400 hover:text-slate-600 bg-slate-100 border-slate-200'
                : 'text-sky-700 bg-sky-50 border border-sky-300 shadow-xs'
            }`}
          >
            {isAudioMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </header>

      {/* Sub-Header: Clinical Workspace Navigation Tabs */}
      <div className="bg-white/80 border-b border-slate-200 px-5 flex items-center justify-between shrink-0">
        <nav className="flex items-center gap-1 overflow-x-auto py-1">
          <button
            onClick={() => setActiveTab('INTAKE')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'INTAKE'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>Case Intake & Triage</span>
          </button>

          <button
            onClick={() => setActiveTab('PATIENTS')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'PATIENTS'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <BedDouble className="w-3.5 h-3.5" />
            <span>Patient Directory</span>
          </button>

          <button
            onClick={() => setActiveTab('STAFF')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'STAFF'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>Hospital Staff</span>
          </button>

          <button
            onClick={() => setActiveTab('REPORTS')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'REPORTS'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Clinical Reports & Reviews</span>
            {reports.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-sky-100 text-sky-800 border border-sky-300">
                {reports.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('REVIEW')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'REVIEW'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <Stethoscope className="w-3.5 h-3.5" />
            <span>Doctor Review</span>
          </button>

          <button
            onClick={() => setActiveTab('REVIEWING')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'REVIEWING'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <FileCheck2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Reviewing</span>
            {reviewedCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-300">
                {reviewedCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('WARDS')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'WARDS'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Department Board</span>
          </button>

          <button
            onClick={() => setActiveTab('HOSPITAL3D')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'HOSPITAL3D'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <Box className="w-3.5 h-3.5" />
            <span>3D Hospital</span>
          </button>

          <button
            onClick={() => setActiveTab('KNOWLEDGE')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'KNOWLEDGE'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>Harrison's Vector RAG</span>
          </button>

          <button
            onClick={() => setActiveTab('BENCHMARK')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'BENCHMARK'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>RL Policy Benchmark</span>
          </button>

          <button
            onClick={() => setActiveTab('DESIGN_SYSTEM')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'DESIGN_SYSTEM'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Design System</span>
          </button>
        </nav>

        {/* Right: Relocated Patient Journey Graph Action */}
        <div className="flex items-center gap-2 py-1">
          <button
            onClick={() => setIsJourneyOpen(true)}
            className="px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-2 bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-300 shadow-2xs transition-all cursor-pointer active:scale-95 group"
            title="Open Patient Journey Graph & Clinical Flow Architecture"
          >
            <Activity className="w-3.5 h-3.5 text-sky-600 group-hover:scale-110 transition-transform animate-pulse" />
            <span>Patient Journey Graph</span>
          </button>
        </div>
      </div>

      {/* Active Trajectory Progress Bar (100% Live Updates without stalls) */}
      <ActiveEncounterProgressBar
        isRunning={isSimulating}
        patientName={simulatingPatientName}
        onViewReport={() => setActiveTab('REPORTS')}
      />

      {/* Main Portal Viewport */}
      <main className="flex-1 overflow-hidden flex flex-col relative bg-[#f8fafc]">
        {activeTab === 'INTAKE' && (
          <CaseIntakeAdmissionSection
            cases={cases}
            onPatientAdmitted={handlePatientAdmitted}
            onAdmitAndSimulate={handleAdmitAndSimulate}
          />
        )}

        {activeTab === 'PATIENTS' && (
          <PatientDirectorySection
            onOpenConsult={() => setIsConsultOpen(true)}
            refreshTrigger={patientRefreshCounter}
          />
        )}

        {activeTab === 'STAFF' && (
          <StaffManagementSection onOpenConsult={() => setIsConsultOpen(true)} />
        )}

        {activeTab === 'REPORTS' && (
          <PhysicianReviewDashboard
            reports={reports}
            onSubmitReview={handleSubmitReview}
            isSubmitting={isSubmittingReview}
            onResetData={refreshData}
          />
        )}

        {activeTab === 'REVIEW' && <DoctorReviewSection />}

        {activeTab === 'REVIEWING' && (
          <ReviewedReportsSection onTriggerTrainingSuccess={refreshData} />
        )}

        {activeTab === 'WARDS' && <DepartmentBoardSection />}

        {activeTab === 'HOSPITAL3D' && <DepartmentBoard3DSection />}

        {activeTab === 'KNOWLEDGE' && <KnowledgeSearchSection />}
        {activeTab === 'DESIGN_SYSTEM' && <DesignSystemShowcase />}

        {activeTab === 'BENCHMARK' && (
          <div className="flex-1 p-6 overflow-y-auto max-w-5xl mx-auto flex flex-col justify-center items-center text-center">
            <div className="max-w-xl p-8 bg-white border border-slate-200 rounded-xl shadow-md hud-bracket">
              <div className="w-12 h-12 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 mx-auto mb-4 shadow-xs">
                <Scale className="w-6 h-6 text-sky-600" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 font-mono tracking-wide mb-2 uppercase">
                Reinforcement Learning Policy Benchmark
              </h3>
              <p className="text-xs text-slate-600 mb-6 leading-relaxed font-sans">
                Evaluate unaligned Base Foundation Model (v0.1) against Physician-Guided RL DPO (v0.3) across multi-case diagnostic accuracy, test appropriateness, and contraindication avoidance.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3 font-mono">
                <button
                  onClick={() => setIsBenchmarkOpen(true)}
                  className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-md shadow-xs transition cursor-pointer"
                >
                  Launch Policy Benchmark Console
                </button>
                <button
                  onClick={() => setIsRLModalOpen(true)}
                  className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs rounded-md border border-slate-300 transition cursor-pointer"
                >
                  Inspect DPO Preference Dataset
                </button>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Hospital Notification System (Slide-In/Out Drawer & Live Event Toasts) */}
      <LeftNotificationDrawer
        events={events}
        isConnected={isWsConnected}
        onNavigateToTab={(tab) => setActiveTab(tab as any)}
        onClearEvents={() => setEvents([])}
      />

      {/* Global Clinical Specialist Modals */}
      <InternalMedicineConsultModal
        isOpen={isConsultOpen}
        onClose={() => setIsConsultOpen(false)}
      />

      <PolicyBenchmarkModal
        isOpen={isBenchmarkOpen}
        onClose={() => setIsBenchmarkOpen(false)}
      />

      <RLDatasetModal
        isOpen={isRLModalOpen}
        onClose={() => setIsRLModalOpen(false)}
      />

      {/* Relocated Patient Journey Graph & Clinical Flow Viewport */}
      {isJourneyOpen && (
        <div className="fixed inset-0 z-50 bg-white flex flex-col animate-in fade-in duration-200">
          <PatientJourneyFlowPage onBackToPortal={() => setIsJourneyOpen(false)} />
        </div>
      )}
    </div>
  );
};

export default App;
