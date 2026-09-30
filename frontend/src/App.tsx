import React, { useState, useEffect } from 'react';
import { PatientJourneyFlowPage } from './components/diagram/PatientJourneyFlowPage';
import { CaseIntakeAdmissionSection } from './components/management/CaseIntakeAdmissionSection';
import { PatientDirectorySection } from './components/management/PatientDirectorySection';
import { StaffManagementSection } from './components/management/StaffManagementSection';
import { KnowledgeSearchSection } from './components/management/KnowledgeSearchSection';
import { PhysicianReviewDashboard } from './components/dashboard/PhysicianReviewDashboard';
import { DoctorReviewSection } from './components/review/DoctorReviewSection';
import { InternalMedicineConsultModal } from './components/specialists/InternalMedicineConsultModal';
import { RLDatasetModal } from './components/rl/RLDatasetModal';
import { PolicyBenchmarkModal } from './components/rl/PolicyBenchmarkModal';
import { toggleGlobalMute, isGlobalMuted } from './utils/speechSynthesis';
import {
  Activity,
  BedDouble,
  Clock,
  Cpu,
  FileText,
  Radio,
  Scale,
  Search,
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
} from './types';

type PortalTab = 'INTAKE' | 'PATIENTS' | 'STAFF' | 'REPORTS' | 'REVIEW' | 'KNOWLEDGE' | 'BENCHMARK' | 
'JOURNEY';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PortalTab>('INTAKE');

  // Shared Data State
  const [cases, setCases] = useState<BenchmarkCase[]>([]);
  const [reports, setReports] = useState<ClinicalReport[]>([]);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [patientRefreshCounter, setPatientRefreshCounter] = useState<number>(0);
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(isGlobalMuted());
  const [currentTime, setCurrentTime] = useState<string>('');

  // Quick Action Modals
  const [isConsultOpen, setIsConsultOpen] = useState<boolean>(false);
  const [isRLModalOpen, setIsRLModalOpen] = useState<boolean>(false);
  const [isBenchmarkOpen, setIsBenchmarkOpen] = useState<boolean>(false);

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

  // URL / Hash Navigation listener for Clinical Flow & Patient Journey
  useEffect(() => {
    const handleUrlRoute = () => {
      const path = window.location.pathname.toLowerCase();
      const hash = window.location.hash.toLowerCase();
      if (
        path === '/journey' ||
        path === '/flow' ||
        path === '/3d' ||
        hash === '#journey' ||
        hash === '#flow' ||
        hash === '#3d'
      ) {
        setActiveTab('JOURNEY');
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

  // Fetch initial cases and reports
  useEffect(() => {
    fetch('/api/cases')
      .then((res) => res.json())
      .then((data) => setCases(data))
      .catch((err) => console.error('Failed to load cases:', err));

    fetch('/api/reports')
      .then((res) => res.json())
      .then((data) => setReports(data))
      .catch((err) => console.error('Failed to load reports:', err));
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
      const rRes = await fetch('/api/reports');
      if (rRes.ok) {
        const updated = await rRes.json();
        setReports(updated);
      }
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handlePatientAdmitted = (_patient: PatientRecord) => {
    setPatientRefreshCounter((prev) => prev + 1);
  };

  const handleAdmitAndSimulate = async (caseId: string) => {
    try {
      await fetch('/api/simulation/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: caseId }),
      });
      const rRes = await fetch('/api/reports');
      if (rRes.ok) {
        const updated = await rRes.json();
        setReports(updated);
      }
      setActiveTab('REPORTS');
    } catch (err) {
      console.error('Error simulating encounter:', err);
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

          <div className="h-4 w-px bg-slate-200 hidden md:block" />

          {/* Real-time Telemetry Sync Beacon */}
          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 bg-slate-100/90 border border-slate-200 rounded font-mono text-[11px]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-emerald-700 font-medium tracking-wide">
              SYSTEM SYNC LIVE
            </span>
            <span className="text-slate-500 text-[10px]">99.98% SYNC</span>
          </div>

          {/* GPU Model Status */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 bg-slate-100/90 border border-slate-200 rounded font-mono text-[11px] text-slate-700">
            <Cpu className="w-3.5 h-3.5 text-sky-600" />
            <span>Clinical AI 4B</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-sky-50 text-sky-700 border border-sky-200 font-medium">
              NF4 LoRA Aligned
            </span>
          </div>
        </div>

        {/* Right: Live Ticker, Quick Action Specialists Dock & Viewport Switcher */}
        <div className="flex items-center gap-3">
          {/* Live UTC Clock */}
          <div className="hidden 2xl:flex items-center gap-1.5 font-mono text-xs text-slate-600 px-2.5 py-1 bg-slate-100/90 border border-slate-200 rounded">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-800 font-semibold">{currentTime || '12:00:00'}</span>
            <span className="text-[10px] text-slate-400">UTC</span>
          </div>

          {/* Quick Action Specialist Dock */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-100 border border-slate-200 rounded-md">
            {/* Dr. Marcus Vance Live Consult */}
            <button
              onClick={() => setIsConsultOpen(true)}
              className="px-2.5 py-1 rounded text-xs font-mono font-medium flex items-center gap-1.5 transition text-sky-700 hover:text-sky-900 hover:bg-sky-50 border border-transparent hover:border-sky-200 cursor-pointer"
              title="Consult Chief Attending Physician Dr. Marcus Vance, MD, FACP"
            >
              <Stethoscope className="w-3.5 h-3.5 text-sky-600" />
              <span className="hidden sm:inline">Dr. Vance RAG</span>
            </button>

            {/* Audio Voice Synthesizer Toggle */}
            <button
              onClick={() => setIsAudioMuted(toggleGlobalMute())}
              title={isAudioMuted ? 'Unmute Clinical Voice Audio' : 'Mute Clinical Voice Audio'}
              className={`p-1.5 rounded transition cursor-pointer ${
                isAudioMuted
                  ? 'text-slate-400 hover:text-slate-600 hover:bg-slate-200/60'
                  : 'text-sky-700 bg-sky-50 border border-sky-300 shadow-xs'
              }`}
            >
              {isAudioMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
            </button>
          </div>

          <div className="h-5 w-px bg-slate-200" />

          {/* Primary Viewport Launcher: Patient Journey & Clinical Flow Architecture */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setActiveTab('JOURNEY')}
              className={`px-3.5 py-1.5 rounded-md text-xs font-mono font-bold flex items-center gap-1.5 transition cursor-pointer ${
                activeTab === 'JOURNEY'
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white shadow-xs'
              }`}
              title="Open Patient Journey Graph & Clinical Flow Architecture"
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Patient Journey Graph</span>
            </button>
          </div>

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
            onClick={() => setActiveTab('JOURNEY')}
            className={`px-3.5 py-2 text-xs font-mono font-medium flex items-center gap-2 rounded transition cursor-pointer ${
              activeTab === 'JOURNEY'
                ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Patient Journey Graph</span>
          </button>
        </nav>

        {/* Right: Hospital Census Quick Stats */}
        <div className="hidden lg:flex items-center gap-3 font-mono text-[11px] text-slate-500 py-1">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">Admitted Patients:</span>
            <span className="font-semibold text-slate-900">{cases.length}</span>
          </div>
          <span className="text-slate-300">•</span>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">Pending Reviews:</span>
            <span className="font-semibold text-amber-700">{reports.length}</span>
          </div>
        </div>
      </div>

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
          />
        )}

        {activeTab === 'REVIEW' && <DoctorReviewSection />}

        {activeTab === 'KNOWLEDGE' && <KnowledgeSearchSection />}

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

        {activeTab === 'JOURNEY' && (
          <PatientJourneyFlowPage onBackToPortal={() => setActiveTab('INTAKE')} />
        )}
      </main>

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
    </div>
  );
};

export default App;
