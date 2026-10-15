import React, { useState, useEffect, useCallback } from 'react';
import { CaseIntakeAdmissionSection } from './components/management/CaseIntakeAdmissionSection';
import { PatientDirectorySection } from './components/management/PatientDirectorySection';
import { StaffManagementSection } from './components/management/StaffManagementSection';
import { KnowledgeSearchSection } from './components/management/KnowledgeSearchSection';
import { KnowledgeSourcesSection } from './components/management/KnowledgeSourcesSection';
import { PhysicianReviewDashboard } from './components/dashboard/PhysicianReviewDashboard';
import { RLDatasetModal } from './components/rl/RLDatasetModal';
import { PolicyBenchmarkModal } from './components/rl/PolicyBenchmarkModal';
import { PolicyBenchmarkPage } from './components/rl/PolicyBenchmarkPage';
import { ReviewedReportsSection } from './components/reviewing/ReviewedReportsSection';
import { LeftNotificationDrawer } from './components/notifications/LeftNotificationDrawer';
import { ActiveEncounterProgressBar } from './components/simulation/ActiveEncounterProgressBar';
import { PatientJourneyFlowPage } from './components/diagram/PatientJourneyFlowPage';
import {
  Activity,
  BedDouble,
  FileText,
  FileCheck2,
  Globe,
  Radio,
  Scale,
  Search,
  Users,
} from 'lucide-react';
import type {
  BenchmarkCase,
  ClinicalReport,
  PhysicianReviewPayload,
  PatientRecord,
  HospitalEvent,
} from './types';

type PortalTab = 'INTAKE' | 'PATIENTS' | 'STAFF' | 'REPORTS' | 'REVIEWING' | 'KNOWLEDGE' | 'KNOWLEDGE_SOURCES' | 'BENCHMARK' | 'JOURNEY';

const CANONICAL_BENCHMARK_CASES: BenchmarkCase[] = [
  {
    id: 'case-001',
    name: 'Elena Vance',
    age: 29,
    sex: 'Female',
    chief_complaint: 'Severe throbbing headache, scotoma (flashing lights), and acute bilateral ankle edema at 34 weeks gestation.',
    acuity: 'CRITICAL (ESI Level 2)',
  },
  {
    id: 'case-002',
    name: 'Arthur Pendelton',
    age: 68,
    sex: 'Male',
    chief_complaint: 'Substernal chest pressure radiating to left mandible, diaphoresis, dyspnea on minimal exertion for 45 minutes.',
    acuity: 'CRITICAL (ESI Level 1)',
  },
  {
    id: 'case-003',
    name: 'Marcus Holloway',
    age: 42,
    sex: 'Male',
    chief_complaint: 'Right lower quadrant abdominal pain with rebound tenderness, low-grade fever, nausea, and anorexia for 18 hours.',
    acuity: 'URGENT (ESI Level 3)',
  },
  {
    id: 'case-004',
    name: 'Diana Reyes',
    age: 35,
    sex: 'Female',
    chief_complaint: 'Acute onset left-sided facial droop and right upper extremity pronator drift starting 75 minutes ago.',
    acuity: 'EMERGENT (ESI Level 1)',
  },
  {
    id: 'case-005',
    name: 'Liam Chen',
    age: 51,
    sex: 'Male',
    chief_complaint: 'Progressive exertional dyspnea, orthopnea requiring 3 pillows, and bilateral lower extremity pitting edema.',
    acuity: 'URGENT (ESI Level 3)',
  },
];

const CANONICAL_DEMO_REPORTS: ClinicalReport[] = [
  {
    id: 'rep-demo-001',
    encounter_id: 'enc-demo-001',
    patient_id: 'pat-demo-001',
    patient_name: 'Elena Vance',
    patient_age: 29,
    patient_sex: 'Female',
    created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    chief_complaint: 'Severe throbbing headache, scotoma (flashing lights), and acute bilateral ankle edema at 34 weeks gestation.',
    history_of_present_illness: 'Patient is a 29-year-old G1P0 female at 34+2 weeks gestation presenting to triage with a 6-hour history of severe frontal headache unresponsive to acetaminophen. Reports new-onset visual disturbances described as glittering scotomata in peripheral fields. Vitals show severe-range hypertension (168/108 mmHg). Denies vaginal bleeding, fluid leakage, or regular uterine contractions.',
    past_medical_history: ['Nulliparous', 'Gestational diabetes (diet-controlled, A1GDM)', 'Mild asthma (albuterol PRN)'],
    medications: ['Prenatal multivitamin 1 tab daily', 'Albuterol MDI PRN'],
    allergies: ['Penicillin (mild maculopapular rash)'],
    vital_signs: {
      timestamp: new Date().toISOString(),
      heart_rate: 88,
      systolic_bp: 168,
      diastolic_bp: 108,
      respiratory_rate: 18,
      temperature_c: 36.8,
      spo2_percent: 98,
      pain_score: 7,
    },
    physical_exam_findings: {
      HEENT: 'Pupils equal, round, reactive to light. Fundoscopy unremarkable, no papilledema.',
      Cardiovascular: 'Regular rate and rhythm, normal S1/S2, no murmurs.',
      Pulmonary: 'Clear to auscultation bilaterally, no crackles, rales, or wheezing.',
      Abdomen: 'Gravid uterus consistent with 34 weeks dates, non-tender, no epigastric or RUQ tenderness.',
      Extremities: '3+ bilateral pitting pretibial edema extending to mid-calf. Brisk patellar reflexes (3+) with 1 beat of unsustained clonus.',
    },
    investigations_ordered: [
      'Complete Blood Count (CBC) with Platelets',
      'Comprehensive Metabolic Panel (CMP with Liver Enzymes AST/ALT)',
      'Serum Creatinine & Uric Acid',
      'Urine Protein-to-Creatinine Ratio (UPCR)',
      'Fetal Non-Stress Test (NST) & Biophysical Profile (BPP)',
    ],
    investigation_results: [
      {
        test_type: 'Complete Blood Count (CBC)',
        values: { Platelets: '142,000 /mcL', Hemoglobin: '12.4 g/dL', Hematocrit: '37.1%' },
        abnormal_flags: { Platelets: true },
        interpretation: 'Mild thrombocytopenia without microangiopathic hemolytic anemia.',
      },
      {
        test_type: 'Hepatic Function Panel',
        values: { AST: '48 U/L', ALT: '52 U/L', Total_Bilirubin: '0.8 mg/dL' },
        abnormal_flags: { AST: true, ALT: true },
        interpretation: 'Mild transaminitis (approaching 2x upper limit of normal).',
      },
      {
        test_type: 'Urinalysis & UPCR',
        values: { Protein_Creatinine_Ratio: '0.68 mg/mg', Urine_Dipstick_Protein: '3+' },
        abnormal_flags: { Protein_Creatinine_Ratio: true, Urine_Dipstick_Protein: true },
        interpretation: 'Significant proteinuria confirming glomerular capillary endotheliosis.',
      },
    ],
    differential_diagnosis: [
      {
        condition: 'Preeclampsia with Severe Features',
        likelihood: 0.92,
        supporting_points: [
          'Gestational age > 20 weeks with new-onset systolic BP ≥ 160 mmHg and diastolic BP ≥ 110 mmHg',
          'Proteinuria with UPCR > 0.3 mg/mg',
          'Persistent cerebral/visual disturbance (severe throbbing frontal headache and photopsia)',
          'Hyperreflexia with patellar clonus',
        ],
        opposing_points: ['No epigastric pain', 'Platelets > 100,000 /mcL'],
      },
      {
        condition: 'Gestational Hypertension',
        likelihood: 0.08,
        supporting_points: ['Hypertension diagnosed after 20 weeks gestation without prior chronic HTN'],
        opposing_points: ['Marked proteinuria (UPCR 0.68)', 'Presence of severe neurological features'],
      },
      {
        condition: 'Chronic Hypertension with Superimposed Preeclampsia',
        likelihood: 0.05,
        supporting_points: ['Severe-range blood pressure elevation'],
        opposing_points: ['Documented normal blood pressures in first and second trimesters'],
      },
    ],
    primary_diagnosis: 'Preeclampsia with Severe Features (ACOG Criteria Met: Severe-range BP + Neurological Symptoms + Proteinuria)',
    diagnostic_confidence: 0.94,
    clinical_reasoning: 'The patient meets definitive criteria for preeclampsia with severe features based on systolic BP ≥ 160 mmHg, accompanied by persistent central nervous system symptoms (severe headache, scotoma) and proteinuria. Prompt seizure prophylaxis with magnesium sulfate and acute antihypertensive control with IV labetalol are urgently indicated to prevent maternal intracranial hemorrhage and eclamptic seizures.',
    treatment_plan: [
      'Immediate IV access (18G x 2) and continuous maternal-fetal telemetry monitoring.',
      'Seizure prophylaxis: Magnesium sulfate 4g IV loading dose over 20 minutes, followed by continuous infusion at 2g/hr.',
      'Acute antihypertensive therapy: Labetalol 20mg IV bolus over 2 minutes; repeat 40mg IV in 10 minutes if systolic BP remains ≥ 160 or diastolic BP ≥ 110.',
      'Antenatal corticosteroids for fetal lung maturity: Betamethasone 12mg IM q24h x 2 doses given gestational age < 37 weeks.',
      'Admission to Labor & Delivery High-Risk Obstetric Care Unit with maternal-fetal medicine consultation.',
    ],
    recommended_disposition: 'ADMIT_LABOR_AND_DELIVERY_HIGH_RISK',
    recommended_next_steps: [
      'Maintain strict intake and output (Foley catheter with urometer, target > 30 mL/hr).',
      'Assess deep tendon reflexes and respiratory rate hourly while on magnesium sulfate infusion.',
      'Serial laboratory monitoring of CBC, platelets, AST/ALT, and creatinine every 6 hours.',
      'Continuous electronic fetal heart rate monitoring.',
    ],
    medical_knowledge_citations: [
      {
        book: "Williams Obstetrics (26th Edition)",
        chapter: "Chapter 40: Hypertensive Disorders in Pregnancy",
        topic: "Management of Severe-Range Hypertension and Seizure Prophylaxis",
        source: "Williams Obstetrics, 26e, Chapter 40",
        excerpt: "Magnesium sulfate is the drug of choice for eclampsia prevention in preeclampsia with severe features. Recommended regimen is 4g to 6g IV loading dose over 15 to 20 minutes, followed by a continuous infusion of 1g to 2g per hour. Antihypertensive therapy must be initiated within 30-60 minutes for sustained severe-range blood pressures (systolic ≥ 160 mmHg or diastolic ≥ 110 mmHg).",
        relevance_score: 0.98,
      },
      {
        book: "ACOG Practice Bulletin No. 222",
        chapter: "Gestational Hypertension and Preeclampsia",
        topic: "Clinical Diagnosis and Delivery Timing Guidelines",
        source: "Obstet Gynecol 2020; 135:e237-e260",
        excerpt: "Preeclampsia with severe features can be diagnosed in the presence of new-onset hypertension with severe-range values or in the presence of new-onset hypertension with thrombocytopenia, impaired liver function, renal insufficiency, pulmonary edema, or new-onset headache unresponsive to medication and not accounted for by alternative diagnoses.",
        relevance_score: 0.95,
      },
      {
        book: "Harrison's Principles of Internal Medicine (21st Edition)",
        chapter: "Chapter 271: Vascular Disorders and Pregnancy",
        topic: "Endothelial Dysfunction in Gestational Hypertension",
        source: "Harrison's IM, 21e, Chapter 271",
        excerpt: "Preeclampsia is characterized by widespread endothelial dysfunction, impaired spiral artery remodeling, elevated soluble fms-like tyrosine kinase-1 (sFlt-1), and decreased placental growth factor (PlGF), leading to systemic vasoconstriction and capillary leakage.",
        relevance_score: 0.89,
      },
    ],
  },
];

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PortalTab>('INTAKE');

  // Shared Data State
  const [cases, setCases] = useState<BenchmarkCase[]>(CANONICAL_BENCHMARK_CASES);
  const [reports, setReports] = useState<ClinicalReport[]>(CANONICAL_DEMO_REPORTS);
  const [reviewedCount, setReviewedCount] = useState<number>(2);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [patientRefreshCounter, setPatientRefreshCounter] = useState<number>(0);

  // Quick Action Modals
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


  // Fetch initial cases, pending reports, and reviewed count
  const refreshData = useCallback(async () => {
    try {
      const [cRes, rRes, revRes] = await Promise.all([
        fetch('/api/cases').catch(() => null),
        fetch('/api/reports/pending').catch(() => null),
        fetch('/api/reports/reviewed').catch(() => null),
      ]);
      if (cRes && cRes.ok) {
        const cData = await cRes.json();
        setCases(Array.isArray(cData) && cData.length > 0 ? cData : CANONICAL_BENCHMARK_CASES);
      } else {
        setCases(CANONICAL_BENCHMARK_CASES);
      }
      if (rRes && rRes.ok) {
        const rData = await rRes.json();
        setReports(Array.isArray(rData) && rData.length > 0 ? rData : CANONICAL_DEMO_REPORTS);
      } else {
        setReports(CANONICAL_DEMO_REPORTS);
      }
      if (revRes && revRes.ok) {
        const revData = await revRes.json();
        setReviewedCount(Array.isArray(revData) && revData.length > 0 ? revData.length : 2);
      } else {
        setReviewedCount(2);
      }
    } catch {
      setCases(CANONICAL_BENCHMARK_CASES);
      setReports(CANONICAL_DEMO_REPORTS);
      setReviewedCount(2);
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  // Real-time Event Telemetry Listener for Left Notification Drawer & Live Report Sync
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
          if (
            parsed.event_type === 'CLINICAL_REPORT_GENERATED' ||
            parsed.event_type === 'PHYSICIAN_REVIEWED' ||
            parsed.event_type === 'ENCOUNTER_CLOSED'
          ) {
            refreshData();
          }
        } catch (e) {
          console.error('Failed to parse WS event:', e);
        }
      };
    } catch (err) {
      console.warn('WS connection error:', err);
    }

    // Cross-frame and BroadcastChannel synchronization for real-time report updates
    const handleWindowMessage = (e: MessageEvent) => {
      if (e.data) {
        if (e.data.type === 'REPORT_GENERATED' || e.data.type === 'REPORT_REVIEWED') {
          refreshData();
        } else if (e.data.type === 'NAVIGATE' && e.data.tab) {
          const target = e.data.tab === 'CASE_ROOM' ? 'JOURNEY' : e.data.tab;
          setActiveTab(target as PortalTab);
        }
      }
    };

    window.addEventListener('message', handleWindowMessage);

    let channel: BroadcastChannel | null = null;
    if (typeof BroadcastChannel !== 'undefined') {
      channel = new BroadcastChannel('vh_patient_channel');
      channel.addEventListener('message', (e) => {
        if (e.data && (e.data.type === 'REPORT_GENERATED' || e.data.type === 'REPORT_REVIEWED')) {
          refreshData();
        }
      });
    }

    return () => {
      if (ws) ws.close();
      window.removeEventListener('message', handleWindowMessage);
      if (channel) channel.close();
    };
  }, [refreshData]);

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
        // Fallback for static GitHub Pages demo: simulate local review completion
        setReports((prev) => prev.filter((r) => r.id !== reviewPayload.report_id));
        setReviewedCount((prev) => prev + 1);
        return;
      }
      await refreshData();
    } catch {
      // Offline fallback: simulate local review completion
      setReports((prev) => prev.filter((r) => r.id !== reviewPayload.report_id));
      setReviewedCount((prev) => prev + 1);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const navigateToTab = (tab: string) => {
    const target = tab === 'CASE_ROOM' ? 'JOURNEY' : tab;
    setActiveTab(target as PortalTab);
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
      <header className="ak-appbar shrink-0" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Official Logo Lockup */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <a
            href="#"
            className="ak-appbar__logo"
            onClick={(e) => { e.preventDefault(); setActiveTab('INTAKE'); }}
            aria-label="Virtual Hospital - Home"
            style={{ display: 'inline-flex', alignItems: 'center' }}
          >
            <img
              src="./logos/vh-logo-compact.svg"
              alt="Virtual Hospital"
              style={{
                height: 28,
                width: 'auto',
                transform: 'translateY(2px)',
              }}
            />
          </a>
          <button
            type="button"
            onClick={() => {
              window.location.hash = '';
              const landing = document.getElementById('landing-view');
              const root = document.getElementById('root');
              if (landing && root) {
                root.style.display = 'none';
                landing.style.display = 'block';
                window.scrollTo(0, 0);
              }
            }}
            className="ak-button ak-button--subtle"
            style={{
              fontSize: 12,
              padding: '3px 10px',
              height: 24,
              borderRadius: 6,
              border: '1px solid var(--border-default)',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4
            }}
            title="Return to Landing Page"
          >
            ← Landing Page
          </button>
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
            onClick={() => setActiveTab('JOURNEY')}
            className="ak-nav__item"
            aria-current={activeTab === 'JOURNEY' ? 'page' : undefined}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', border: 0 }}
          >
            <Activity aria-hidden="true" style={{ width: 16, height: 16 }} />
            <span>Trajectory graph</span>
          </button>
        </nav>
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
            onNavigateTab={navigateToTab}
            initialMode="SYNTHETIC"
          />
        )}

        {activeTab === 'PATIENTS' && (
          <PatientDirectorySection
            refreshTrigger={patientRefreshCounter}
          />
        )}

        {activeTab === 'STAFF' && (
          <StaffManagementSection onNavigateTab={navigateToTab} />
        )}

        {activeTab === 'REPORTS' && (
          <PhysicianReviewDashboard
            reports={reports}
            onSubmitReview={handleSubmitReview}
            isSubmitting={isSubmittingReview}
            onResetData={refreshData}
          />
        )}

        {activeTab === 'REVIEWING' && (
          <ReviewedReportsSection onTriggerTrainingSuccess={refreshData} />
        )}

        {activeTab === 'KNOWLEDGE' && <KnowledgeSearchSection />}
        {activeTab === 'KNOWLEDGE_SOURCES' && <KnowledgeSourcesSection />}
        {activeTab === 'JOURNEY' && (
          <div className="flex-1 w-full h-full overflow-hidden flex flex-col">
            <PatientJourneyFlowPage
              onBackToPortal={() => setActiveTab('INTAKE')}
              onNavigateTab={navigateToTab}
            />
          </div>
        )}

        {activeTab === 'BENCHMARK' && (
          <div className="flex-1 w-full h-full overflow-hidden flex flex-col">
            <PolicyBenchmarkPage onNavigateTab={navigateToTab} />
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
