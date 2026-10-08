import React, { useState, useEffect } from 'react';
import { CaseIntakeAdmissionSection } from './components/management/CaseIntakeAdmissionSection';
import { PatientDirectorySection } from './components/management/PatientDirectorySection';
import { StaffManagementSection } from './components/management/StaffManagementSection';
import { KnowledgeSearchSection } from './components/management/KnowledgeSearchSection';
import { KnowledgeSourcesSection } from './components/management/KnowledgeSourcesSection';
import { PhysicianReviewDashboard } from './components/dashboard/PhysicianReviewDashboard';
import { DoctorReviewSection } from './components/review/DoctorReviewSection';
import { InternalMedicineConsultModal } from './components/specialists/InternalMedicineConsultModal';
import { RLDatasetModal } from './components/rl/RLDatasetModal';
import { PolicyBenchmarkModal } from './components/rl/PolicyBenchmarkModal';
import { ReviewedReportsSection } from './components/reviewing/ReviewedReportsSection';
import { LeftNotificationDrawer } from './components/notifications/LeftNotificationDrawer';
import { ActiveEncounterProgressBar } from './components/simulation/ActiveEncounterProgressBar';
import { PatientJourneyFlowPage } from './components/diagram/PatientJourneyFlowPage';
import { DesignSystemShowcase } from './pages/DesignSystemShowcase';
import {
  Activity,
  BedDouble,
  FileText,
  FileCheck2,
  Globe,
  Radio,
  Scale,
  Search,
  Sparkles,
  Stethoscope,
  Users,
} from 'lucide-react';
import type {
  BenchmarkCase,
  ClinicalReport,
  PhysicianReviewPayload,
  PatientRecord,
  HospitalEvent,
} from './types';

type PortalTab = 'INTAKE' | 'PATIENTS' | 'STAFF' | 'REPORTS' | 'REVIEW' | 'REVIEWING' | 'KNOWLEDGE' | 'KNOWLEDGE_SOURCES' | 'BENCHMARK' | 'DESIGN_SYSTEM' | 'JOURNEY';



export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PortalTab>('INTAKE');

  // Shared Data State
  const [cases, setCases] = useState<BenchmarkCase[]>([]);
  const [reports, setReports] = useState<ClinicalReport[]>([]);
  const [reviewedCount, setReviewedCount] = useState<number>(0);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [patientRefreshCounter, setPatientRefreshCounter] = useState<number>(0);

  // Quick Action Modals
  const [isConsultOpen, setIsConsultOpen] = useState<boolean>(false);
  const [isRLModalOpen, setIsRLModalOpen] = useState<boolean>(false);
  const [isBenchmarkOpen, setIsBenchmarkOpen] = useState<boolean>(false);


  // Telemetry & Simulation States
  const [events, setEvents] = useState<HospitalEvent[]>([]);
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulatingPatientName, setSimulatingPatientName] = useState<string>('Active Encounter');

  // Hash Navigation listener
  useEffect(() => {
    const handleUrlRoute = () => {
      const path = window.location.pathname.toLowerCase();
      const hash = window.location.hash.toLowerCase();
      if (path === '/journey' || hash === '#journey') {
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
    <div className="w-screen h-screen flex flex-col bg-[var(--bg-page)] overflow-hidden font-sans select-none text-[var(--text-primary)]">
      <a href="#main-content" className="ak-skip-link">
        Skip to clinical content
      </a>
      {/* Asklevia Clinical App Bar */}
      {/* Header */}
      <header className="ak-appbar shrink-0">
        {/* Official Logo Lockup */}
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <a
            href="#"
            className="ak-appbar__logo"
            onClick={(e) => { e.preventDefault(); setActiveTab('INTAKE'); }}
            aria-label="Virtual Hospital - Home"
            style={{ display: 'inline-flex', alignItems: 'center' }}
          >
            <img
              src="/logos/vh-logo-compact.svg"
              alt="Virtual Hospital"
              style={{
                height: 28,
                width: 'auto',
                transform: 'translateY(2px)',
              }}
            />
          </a>
        </div>
      </header>

      {/* Sub-Header: Clinical Workspace Navigation Tabs */}
      <div
        style={{
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-default)',
          padding: '0 var(--space-6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <nav className="ak-nav" style={{ padding: 'var(--space-1) 0' }}>
          <button
            type="button"
            onClick={() => setActiveTab('INTAKE')}
            className="ak-nav__item"
            aria-current={activeTab === 'INTAKE' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >
            <Radio aria-hidden="true" style={{ width: 16, height: 16 }} />
            <span>Intake & Triage</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('PATIENTS')}
            className="ak-nav__item"
            aria-current={activeTab === 'PATIENTS' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >
            <BedDouble aria-hidden="true" style={{ width: 16, height: 16 }} />
            <span>Patient Directory</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('STAFF')}
            className="ak-nav__item"
            aria-current={activeTab === 'STAFF' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >
            <Users aria-hidden="true" style={{ width: 16, height: 16 }} />
            <span>Staff Roster</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('REPORTS')}
            className="ak-nav__item"
            aria-current={activeTab === 'REPORTS' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >
            <FileText aria-hidden="true" style={{ width: 16, height: 16 }} />
            <span>Clinical Reports</span>
            {reports.length > 0 && (
              <span className="ak-tab__count ak-num">({reports.length})</span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('REVIEW')}
            className="ak-nav__item"
            aria-current={activeTab === 'REVIEW' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >
            <Stethoscope aria-hidden="true" style={{ width: 16, height: 16 }} />
            <span>Doctor Review</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('REVIEWING')}
            className="ak-nav__item"
            aria-current={activeTab === 'REVIEWING' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >
            <FileCheck2 aria-hidden="true" style={{ width: 16, height: 16 }} />
            <span>Reviewing</span>
            {reviewedCount > 0 && (
              <span className="ak-tab__count ak-num">({reviewedCount})</span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('KNOWLEDGE')}
            className="ak-nav__item"
            aria-current={activeTab === 'KNOWLEDGE' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >
            <Search aria-hidden="true" style={{ width: 16, height: 16 }} />
            <span>Knowledge Books</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('KNOWLEDGE_SOURCES')}
            className="ak-nav__item"
            aria-current={activeTab === 'KNOWLEDGE_SOURCES' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >
            <Globe aria-hidden="true" style={{ width: 16, height: 16 }} />
            <span>Knowledge Sources</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('BENCHMARK')}
            className="ak-nav__item"
            aria-current={activeTab === 'BENCHMARK' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >

            <Scale aria-hidden="true" style={{ width: 16, height: 16 }} />
            <span>Policy Benchmark</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('DESIGN_SYSTEM')}
            className="ak-nav__item"
            aria-current={activeTab === 'DESIGN_SYSTEM' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >
            <Sparkles aria-hidden="true" style={{ width: 16, height: 16, color: 'var(--action-primary)' }} />
            <span>Design System</span>
          </button>
        </nav>

        {/* Right: Patient Journey Graph Trigger */}
        <div style={{ display: 'flex', alignItems: 'center', padding: 'var(--space-1) 0' }}>
          <button
            type="button"
            onClick={() => setActiveTab('JOURNEY')}
            className={`ak-btn ak-btn--sm ${activeTab === 'JOURNEY' ? 'ak-btn--primary' : 'ak-btn--secondary'}`}
            title="Open patient clinical journey graph"
            aria-current={activeTab === 'JOURNEY' ? 'page' : undefined}
          >
            <Activity aria-hidden="true" style={{ width: 14, height: 14, color: activeTab === 'JOURNEY' ? 'var(--text-inverse)' : 'var(--action-primary)' }} />
            <span>Trajectory graph</span>
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
      <div className="flex-1 overflow-hidden flex flex-col relative bg-[var(--ak-color-bg-app)]">
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

        {activeTab === 'KNOWLEDGE' && <KnowledgeSearchSection />}
        {activeTab === 'KNOWLEDGE_SOURCES' && <KnowledgeSourcesSection />}
        {activeTab === 'DESIGN_SYSTEM' && <DesignSystemShowcase />}
        {activeTab === 'JOURNEY' && (
          <div className="flex-1 w-full h-full overflow-hidden flex flex-col">
            <PatientJourneyFlowPage onBackToPortal={() => setActiveTab('INTAKE')} />
          </div>
        )}

        {activeTab === 'BENCHMARK' && (
          <div className="flex-1 p-6 overflow-y-auto max-w-5xl mx-auto flex flex-col justify-center items-center text-center">
            <div className="max-w-xl p-8 bg-white border border-[var(--ak-color-border-subtle)] rounded-xl shadow-md">
              <div className="w-12 h-12 rounded-lg bg-[var(--ak-color-primary-soft)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-primary)] mx-auto mb-4 shadow-xs">
                <Scale className="w-6 h-6 text-[var(--ak-color-primary)]" />
              </div>
              <h3 className="text-lg font-bold text-[var(--ak-color-text-primary)] font-mono tracking-wide mb-2 uppercase">
                Reinforcement Learning Policy Benchmark
              </h3>
              <p className="text-xs text-[var(--ak-color-text-secondary)] mb-6 leading-relaxed font-sans">
                Evaluate unaligned Base Foundation Model (v0.1) against Physician-Guided RL DPO (v0.3) across multi-case diagnostic accuracy, test appropriateness, and contraindication avoidance.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3 font-mono">
                <button
                  onClick={() => setIsBenchmarkOpen(true)}
                  className="px-4 py-2.5 bg-[var(--ak-color-primary)] hover:bg-[var(--ak-color-primary)] text-white font-bold text-xs rounded-md shadow-xs transition cursor-pointer"
                >
                  Launch Policy Benchmark Console
                </button>
                <button
                  onClick={() => setIsRLModalOpen(true)}
                  className="px-4 py-2.5 bg-[var(--ak-color-bg-subtle)] hover:border-[var(--ak-color-border-subtle)] text-[var(--ak-color-text-primary)] font-semibold text-xs rounded-md border border-[var(--ak-color-border-subtle)] transition cursor-pointer"
                >
                  Inspect DPO Preference Dataset
                </button>
              </div>
            </div>
          </div>
        )}

      </div>

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
    </div>
  );
};


export default App;
