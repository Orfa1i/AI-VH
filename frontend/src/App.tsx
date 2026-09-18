import React, { useState, useEffect } from 'react';
import { Hospital3DPage } from './components/hospital3d/Hospital3DPage';
import { CaseIntakeAdmissionSection } from './components/management/CaseIntakeAdmissionSection';
import { PatientDirectorySection } from './components/management/PatientDirectorySection';
import { StaffManagementSection } from './components/management/StaffManagementSection';
import { KnowledgeSearchSection } from './components/management/KnowledgeSearchSection';
import { PhysicianReviewDashboard } from './components/dashboard/PhysicianReviewDashboard';
import { InternalMedicineConsultModal } from './components/specialists/InternalMedicineConsultModal';
import { PharmacistModal } from './components/specialists/PharmacistModal';
import { InpatientTelemetryModal } from './components/dashboard/InpatientTelemetryModal';
import { RLDatasetModal } from './components/rl/RLDatasetModal';
import { PolicyBenchmarkModal } from './components/rl/PolicyBenchmarkModal';
import { toggleGlobalMute, isGlobalMuted } from './utils/speechSynthesis';
import type {
  BenchmarkCase,
  ClinicalReport,
  PhysicianReviewPayload,
  PatientRecord,
} from './types';

type PortalTab = 'INTAKE' | 'PATIENTS' | 'STAFF' | 'REPORTS' | 'KNOWLEDGE' | 'BENCHMARK';

export const App: React.FC = () => {
  // Determine if current URL or hash points to the 3D visualization page
  const checkIs3DRoute = (): boolean => {
    const path = window.location.pathname.toLowerCase();
    const hash = window.location.hash.toLowerCase();
    return (
      path === '/3d' ||
      path.startsWith('/3d/') ||
      path === '/simulation' ||
      path.startsWith('/simulation/') ||
      hash === '#3d' ||
      hash === '#simulation'
    );
  };

  const [is3DMode, setIs3DMode] = useState<boolean>(checkIs3DRoute());
  const [activeTab, setActiveTab] = useState<PortalTab>('INTAKE');

  // Shared Data State
  const [cases, setCases] = useState<BenchmarkCase[]>([]);
  const [reports, setReports] = useState<ClinicalReport[]>([]);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [patientRefreshCounter, setPatientRefreshCounter] = useState<number>(0);
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(isGlobalMuted());

  // Quick Action Modals
  const [isConsultOpen, setIsConsultOpen] = useState<boolean>(false);
  const [isPharmacyOpen, setIsPharmacyOpen] = useState<boolean>(false);
  const [isInpatientOpen, setIsInpatientOpen] = useState<boolean>(false);
  const [isRLModalOpen, setIsRLModalOpen] = useState<boolean>(false);
  const [isBenchmarkOpen, setIsBenchmarkOpen] = useState<boolean>(false);

  // URL Navigation listener (popstate and hashchange)
  useEffect(() => {
    const handleLocationChange = () => {
      setIs3DMode(checkIs3DRoute());
    };

    window.addEventListener('popstate', handleLocationChange);
    window.addEventListener('hashchange', handleLocationChange);
    return () => {
      window.removeEventListener('popstate', handleLocationChange);
      window.removeEventListener('hashchange', handleLocationChange);
    };
  }, []);

  const navigateTo = (path: string) => {
    window.history.pushState({}, '', path);
    setIs3DMode(checkIs3DRoute());
  };

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
      // Refresh reports list
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
    // Increment counter to trigger reload in patient directory
    setPatientRefreshCounter((prev) => prev + 1);
  };

  const handleAdmitAndSimulate = async (caseId: string) => {
    try {
      await fetch('/api/simulation/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: caseId }),
      });
      // Refresh reports
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

  // =========================================================================
  // View 1: Dedicated 3D Hospital Visualization Page (/3d)
  // =========================================================================
  if (is3DMode) {
    return <Hospital3DPage onBackToPortal={() => navigateTo('/')} />;
  }

  // =========================================================================
  // View 2: Hospital Operations & Clinical Management Portal (/)
  // =========================================================================
  return (
    <div className="w-screen h-screen flex flex-col bg-slate-950 overflow-hidden font-sans select-none text-slate-100">
      {/* Top Main Navigation Bar */}
      <header className="h-16 bg-slate-900/95 border-b border-slate-800 px-6 flex items-center justify-between z-20 shrink-0 shadow-lg">
        {/* Left: Branding & Subsystem Indicator */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white font-bold text-lg">
            🏥
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-black tracking-wider text-slate-100 uppercase">
                AI Virtual Hospital
              </span>
              <span className="px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 text-[10px] font-mono font-semibold">
                Clinical Operations Portal
              </span>
              <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                DB Connected
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Autonomous Inpatient Management, Admissions & Specialist Consultation System
            </p>
          </div>
        </div>

        {/* Center/Right: Quick Actions & 3D Launcher Button */}
        <div className="flex items-center gap-2.5">
          {/* Central Telemetry Modal Button */}
          <button
            onClick={() => setIsInpatientOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-rose-900/50 text-rose-300 text-xs font-semibold flex items-center gap-1.5 transition shadow"
            title="Open East Inpatient Wing 4-Bed Central Telemetry Console"
          >
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span>Telemetry</span>
          </button>

          {/* Internal Medicine Specialist Consult */}
          <button
            onClick={() => setIsConsultOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-cyan-300 text-xs font-medium transition"
          >
            🩺 Dr. Vance RAG
          </button>

          {/* Clinical Pharmacy Review */}
          <button
            onClick={() => setIsPharmacyOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-amber-300 text-xs font-medium transition"
          >
            💊 Pharmacy Safety
          </button>

          {/* Audio Voice Toggle */}
          <button
            onClick={() => setIsAudioMuted(toggleGlobalMute())}
            title={isAudioMuted ? 'Unmute Audio Voices' : 'Mute Audio Voices'}
            className={`p-1.5 rounded-lg border text-xs transition ${
              isAudioMuted
                ? 'bg-slate-800 text-slate-500 border-slate-700'
                : 'bg-cyan-950 text-cyan-300 border-cyan-800 shadow'
            }`}
          >
            {isAudioMuted ? '🔇' : '🔊'}
          </button>

          <div className="h-5 w-px bg-slate-800 mx-1" />

          {/* Prominent Hospital Flow Diagram & Simulation Launcher */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => navigateTo('/3d')}
              className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-cyan-500/25 flex items-center gap-1.5 transition cursor-pointer"
              title="Open Hospital Clinical Flow Diagram & Simulation (/3d)"
            >
              <span>📊</span>
              <span>Hospital Flow Diagram (/3d)</span>
            </button>

            <button
              onClick={() => window.open('/3d', '_blank')}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs border border-slate-700 transition"
              title="Open Flow Diagram in New Window / Monitor"
            >
              ↗
            </button>
          </div>
        </div>
      </header>

      {/* Sub-Header: Portal Tab Navigation */}
      <div className="bg-slate-900 border-b border-slate-800 px-6 flex items-center gap-1 overflow-x-auto shrink-0 shadow-inner">
        <button
          onClick={() => setActiveTab('INTAKE')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'INTAKE'
              ? 'border-cyan-500 text-cyan-400 bg-slate-800/50'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'
          }`}
        >
          <span>📥</span>
          <span>Case Intake & Admission</span>
        </button>

        <button
          onClick={() => setActiveTab('PATIENTS')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'PATIENTS'
              ? 'border-cyan-500 text-cyan-400 bg-slate-800/50'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'
          }`}
        >
          <span>🛏️</span>
          <span>Patient Directory & Bed Board</span>
        </button>

        <button
          onClick={() => setActiveTab('STAFF')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'STAFF'
              ? 'border-cyan-500 text-cyan-400 bg-slate-800/50'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'
          }`}
        >
          <span>👥</span>
          <span>Hospital Staff & Directory</span>
        </button>

        <button
          onClick={() => setActiveTab('REPORTS')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'REPORTS'
              ? 'border-cyan-500 text-cyan-400 bg-slate-800/50'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'
          }`}
        >
          <span>📋</span>
          <span>Clinical Reports & Reviews</span>
          {reports.length > 0 && (
            <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800">
              {reports.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('KNOWLEDGE')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'KNOWLEDGE'
              ? 'border-cyan-500 text-cyan-400 bg-slate-800/50'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'
          }`}
        >
          <span>📚</span>
          <span>Harrison's RAG Search</span>
        </button>

        <button
          onClick={() => setActiveTab('BENCHMARK')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition whitespace-nowrap cursor-pointer ${
            activeTab === 'BENCHMARK'
              ? 'border-cyan-500 text-cyan-400 bg-slate-800/50'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'
          }`}
        >
          <span>⚖️</span>
          <span>Policy Benchmarks & RL</span>
        </button>
      </div>

      {/* Main Portal Viewport */}
      <main className="flex-1 overflow-hidden flex flex-col relative">
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

        {activeTab === 'KNOWLEDGE' && <KnowledgeSearchSection />}

        {activeTab === 'BENCHMARK' && (
          <div className="flex-1 p-6 bg-slate-900/60 overflow-y-auto max-w-6xl mx-auto flex flex-col justify-center items-center text-center">
            <div className="max-w-xl p-8 bg-slate-800/50 border border-slate-800 rounded-2xl shadow-xl">
              <div className="text-4xl mb-3">⚖️</div>
              <h3 className="text-xl font-bold text-slate-100 mb-2">
                RL Policy Benchmark & DPO Corpus
              </h3>
              <p className="text-xs text-slate-400 mb-6 leading-relaxed">
                Compare unaligned MedGemma v0.1 against physician-guided RL DPO v0.3 across multi-case diagnostic accuracy, test appropriateness, and contraindication avoidance.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <button
                  onClick={() => setIsBenchmarkOpen(true)}
                  className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow transition"
                >
                  Launch Policy Benchmark Console
                </button>
                <button
                  onClick={() => setIsRLModalOpen(true)}
                  className="px-5 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-200 font-semibold text-xs rounded-xl border border-slate-600 transition"
                >
                  Inspect DPO Preference Dataset
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Global Modals */}
      <InternalMedicineConsultModal
        isOpen={isConsultOpen}
        onClose={() => setIsConsultOpen(false)}
      />

      <PharmacistModal
        isOpen={isPharmacyOpen}
        onClose={() => setIsPharmacyOpen(false)}
        cases={cases}
      />

      <InpatientTelemetryModal
        isOpen={isInpatientOpen}
        onClose={() => setIsInpatientOpen(false)}
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
