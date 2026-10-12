import React, { useState, useEffect, useRef } from 'react';
import type { BenchmarkCase, PatientRecord } from '../../types';
import {
  RotateCcw,
  ArrowRight,
  Activity,
  HeartPulse,
  Thermometer,
  Layers,
  FileSpreadsheet,
} from 'lucide-react';


import {
  Button,
  Badge,
  Card,
  CardHead,
  CardTitle,
  TextField,
  TextArea,
  Select,
  Alert,
  Tabs,
} from '../ui';
import { AppPage } from '../layout/Templates';

export interface CaseIntakeAdmissionSectionProps {
  cases?: BenchmarkCase[];
  onPatientAdmitted: (patient: PatientRecord) => void;
  onAdmitAndSimulate?: (caseId: string, patientName?: string) => void;
  onNavigateTab?: (tab: string) => void;
  initialMode?: 'MANUAL' | 'SYNTHETIC';
}

export const CaseIntakeAdmissionSection: React.FC<CaseIntakeAdmissionSectionProps> = ({
  cases: _cases,
  onPatientAdmitted,
  onAdmitAndSimulate,
  onNavigateTab,
  initialMode = 'MANUAL',
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  // Mode switcher: Manual admission form vs. Synthetic Synthea patient library
  const [intakeMode, setIntakeMode] = useState<string>(initialMode);

  useEffect(() => {
    const handleMessage = (e: MessageEvent) => {
      // Ignore messages dispatched by host window to prevent recursive loops
      if (e.source === window) return;
      if (!e.data || typeof e.data !== 'object') return;

      if (e.data.type === 'NAVIGATE' && e.data.tab) {
        onNavigateTab?.(e.data.tab);
      } else if (e.data.type === 'SET_INTAKE_MODE' && e.data.mode) {
        if (initialMode !== 'SYNTHETIC') {
          setIntakeMode(e.data.mode);
        }
      } else if (e.data.type === 'PATIENT_ADMITTED' && e.data.patient) {
        onPatientAdmitted(e.data.patient);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onNavigateTab, onPatientAdmitted, initialMode]);

  // Form fields
  const [name, setName] = useState('');
  const [age, setAge] = useState<number | ''>('');
  const [sex, setSex] = useState<'Male' | 'Female' | 'Other'>('Male');
  const [triageAcuity, setTriageAcuity] = useState<string>('EMERGENT');
  const [assignedDepartment, setAssignedDepartment] = useState<string>('EMERGENCY');
  const [bedNumber, setBedNumber] = useState<string>('');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [hpi, setHpi] = useState('');
  const [pastMedicalHistory, setPastMedicalHistory] = useState('');
  const [medications, setMedications] = useState('');
  const [allergies, setAllergies] = useState('');

  // Vitals
  const [heartRate, setHeartRate] = useState<number>(75);
  const [systolicBp, setSystolicBp] = useState<number>(120);
  const [diastolicBp, setDiastolicBp] = useState<number>(80);
  const [respiratoryRate, setRespiratoryRate] = useState<number>(16);
  const [spo2, setSpo2] = useState<number>(98.0);
  const [temperature, setTemperature] = useState<number>(37.0);

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [lastAdmitted, setLastAdmitted] = useState<PatientRecord | null>(null);

  const handleResetForm = () => {
    setName('');
    setAge('');
    setSex('Male');
    setTriageAcuity('EMERGENT');
    setAssignedDepartment('EMERGENCY');
    setBedNumber('');
    setChiefComplaint('');
    setHpi('');
    setPastMedicalHistory('');
    setMedications('');
    setAllergies('');
    setHeartRate(75);
    setSystolicBp(120);
    setDiastolicBp(80);
    setRespiratoryRate(16);
    setSpo2(98.0);
    setTemperature(37.0);
    setSuccessMessage(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !chiefComplaint.trim()) {
      alert('Please provide patient name and chief complaint.');
      return;
    }

    setIsSubmitting(true);
    setSuccessMessage(null);

    const payload = {
      name: name.trim(),
      age: Number(age) || 0,
      sex,
      triage_acuity: triageAcuity,
      assigned_department: assignedDepartment,
      bed_number: bedNumber.trim() || `${assignedDepartment.substring(0, 3)}-01`,
      chief_complaint: chiefComplaint.trim(),
      history_of_present_illness: hpi.trim(),
      past_medical_history: pastMedicalHistory.split(',').map((s) => s.trim()).filter(Boolean),
      medications: medications.split(',').map((s) => s.trim()).filter(Boolean),
      allergies: allergies.split(',').map((s) => s.trim()).filter(Boolean),
      baseline_vitals: {
        heart_rate: Number(heartRate),
        systolic_bp: Number(systolicBp),
        diastolic_bp: Number(diastolicBp),
        respiratory_rate: Number(respiratoryRate),
        spo2: Number(spo2),
        temperature_c: Number(temperature),
      },
    };

    try {
      const res = await fetch('/api/patients/admit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || 'Failed to admit patient');
      }

      const admittedPatient: PatientRecord = await res.json();
      setLastAdmitted(admittedPatient);
      setSuccessMessage(
        `Patient ${admittedPatient.name} successfully admitted with MRN ${admittedPatient.mrn}. Bed assigned: ${admittedPatient.bed_number}.`
      );
      onPatientAdmitted(admittedPatient);
    } catch (err: any) {
      console.error('Admission failed:', err);
      alert(`Admission Error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickEncounter = () => {
    if (!lastAdmitted) return;
    if (onAdmitAndSimulate) {
      onAdmitAndSimulate(lastAdmitted.id, lastAdmitted.name);
    }
  };

  const acuityOptions = [
    {
      id: 'RESUSCITATION',
      label: 'ESI 1',
      title: 'Resuscitation',
      desc: 'Immediate life threat',
      variant: 'danger' as const,
      color: 'var(--color-emergency-dark, var(--danger-700))',
      bgTint: 'var(--emergency-subtle, var(--danger-50))',
      badgeStyle: { backgroundColor: 'var(--danger-50)', color: 'var(--danger-700)' },
    },
    {
      id: 'EMERGENT',
      label: 'ESI 2',
      title: 'Emergent',
      desc: 'High-risk / Severe vitals',
      variant: 'danger' as const,
      color: 'var(--color-emergency, var(--danger-600))',
      bgTint: 'var(--emergency-subtle, var(--danger-50))',
      badgeStyle: { backgroundColor: 'var(--danger-50)', color: 'var(--danger-600)' },
    },
    {
      id: 'URGENT',
      label: 'ESI 3',
      title: 'Urgent',
      desc: 'Multiple resources needed',
      variant: 'warning' as const,
      color: 'var(--warning-600)',
      bgTint: 'var(--warning-50)',
    },
    {
      id: 'LESS_URGENT',
      label: 'ESI 4',
      title: 'Less Urgent',
      desc: 'One resource needed',
      variant: 'info' as const,
      color: 'var(--info-600)',
      bgTint: 'var(--info-50)',
    },
    {
      id: 'NON_URGENT',
      label: 'ESI 5',
      title: 'Non-Urgent',
      desc: 'Clinical evaluation only',
      variant: 'success' as const,
      color: 'var(--success-600)',
      bgTint: 'var(--success-50)',
    },
  ];

  if (initialMode === 'SYNTHETIC' || intakeMode === 'SYNTHETIC') {
    return (
      <div className="w-full h-full flex flex-1 flex-col relative overflow-hidden" style={{ minHeight: 'calc(100vh - 120px)' }}>
        <iframe
          ref={iframeRef}
          src="/case-intake.html"
          title="Virtual Hospital Case Intake"
          className="w-full flex-1 border-0"
          style={{
            width: '100%',
            height: '100%',
            minHeight: 'calc(100vh - 120px)',
            border: 'none',
            display: 'block',
            background: '#F7F8FB',
          }}
        />
      </div>
    );
  }

  return (
    <AppPage
      title="Case Intake & Triage Admission"
      breadcrumbs={[
        { label: 'Clinical Ops', href: '#' },
        { label: 'Case Intake & Triage', isCurrent: true },
      ]}
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Button
            variant="ghost"
            size="md"
            onClick={handleResetForm}
            leadingIcon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Reset form
          </Button>
        </div>
      }
    >
      {/* MODE TABS SWITCHER */}
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <Tabs
          tabs={[
            { id: 'MANUAL', label: 'Manual Case Intake & Bed Allocation' },
            { id: 'SYNTHETIC', label: 'Synthetic Patients & Cohort Generator' },
          ]}
          activeId={intakeMode}
          onChange={(id) => setIntakeMode(id)}
        />
      </div>

      <>
          {/* SUCCESS NOTIFICATION */}
          {successMessage && lastAdmitted && (
            <div style={{ marginBottom: 'var(--space-6)' }}>
              <Alert
                variant="success"
                title="Patient Admitted to Hospital Ledger"
                actions={
                  onAdmitAndSimulate && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleQuickEncounter}
                      leadingIcon={<ArrowRight className="w-3.5 h-3.5" />}
                    >
                      Dispatch to Pathway
                    </Button>
                  )
                }
              >
                <div>{successMessage}</div>
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 'var(--space-2)',
                    marginTop: 'var(--space-2)',
                  }}
                >
                  <Badge variant="neutral">MRN: <strong className="ak-num">{lastAdmitted.mrn}</strong></Badge>
                  <Badge variant="neutral">Acuity: <strong>{lastAdmitted.triage_acuity}</strong></Badge>
                  <Badge variant="neutral">Bed: <strong>{lastAdmitted.bed_number}</strong></Badge>
                </div>
              </Alert>
            </div>
          )}

          {/* MAIN INTAKE FORM */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
            {/* Section 1: Demographics & ESI Acuity */}
            <Card>
              <CardHead>
                <div>
                  <CardTitle>1. Patient Demographics & Bed Allocation</CardTitle>
                  <span className="caption" style={{ color: 'var(--text-secondary)' }}>
                    Mandatory admission credentials and initial unit placement
                  </span>
                </div>
              </CardHead>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: 'var(--space-4)',
                  marginBottom: 'var(--space-6)',
                }}
              >
                <TextField
                  label="Patient Full Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Jane Smith"
                  required
                />

                <TextField
                  label="Age"
                  type="number"
                  value={age}
                  onChange={(e) => setAge(e.target.value === '' ? '' : Number(e.target.value))}
                  min={1}
                  max={120}
                  placeholder="Years"
                  required
                />

                <Select
                  label="Biological Sex"
                  value={sex}
                  onChange={(e) => setSex(e.target.value as any)}
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </Select>

                <Select
                  label="Assigned Department"
                  value={assignedDepartment}
                  onChange={(e) => setAssignedDepartment(e.target.value)}
                >
                  <option value="EMERGENCY">Emergency Department</option>
                  <option value="CARDIOLOGY">Cardiology / CCU</option>
                  <option value="ICU">Medical ICU (MICU)</option>
                  <option value="INTERNAL_MEDICINE">Internal Medicine</option>
                  <option value="STEP_DOWN">Inpatient Step-Down Wing</option>
                </Select>
              </div>

              {/* Triage Acuity Options */}
              <div>
                <label className="ak-label" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>
                  Emergency Severity Index (ESI) Triage Rating
                </label>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: 'var(--space-3)',
                  }}
                >
                  {acuityOptions.map((lvl) => {
                    const isSelected = triageAcuity === lvl.id;
                    const activeColor = lvl.color || 'var(--color-emergency, var(--danger-600))';
                    const activeBg = lvl.bgTint || 'var(--emergency-subtle, var(--color-emergency-tint, var(--danger-50)))';
                    return (
                      <div
                        key={lvl.id}
                        role="button"
                        tabIndex={0}
                        aria-pressed={isSelected}
                        onClick={() => setTriageAcuity(lvl.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setTriageAcuity(lvl.id);
                          }
                        }}
                        style={{
                          padding: 'var(--space-3)',
                          borderRadius: 'var(--radius-md)',
                          border: isSelected
                            ? `2px solid ${activeColor}`
                            : '1px solid var(--border-default)',
                          backgroundColor: isSelected
                            ? activeBg
                            : 'var(--bg-surface)',
                          boxShadow: isSelected
                            ? `0 0 0 1px ${activeColor}`
                            : 'none',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                          outline: 'none',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Badge variant={lvl.variant} style={lvl.badgeStyle}>{lvl.label}</Badge>
                          {isSelected && (
                            <span
                              style={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                backgroundColor: activeColor,
                              }}
                            />
                          )}
                        </div>
                        <div className="heading-3" style={{ fontSize: '0.875rem', marginTop: 6, marginBottom: 2 }}>
                          {lvl.title}
                        </div>
                        <div className="caption" style={{ color: 'var(--text-secondary)' }}>
                          {lvl.desc}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </Card>

            {/* Section 2: Clinical Presentation & Medical History */}
            <Card>
              <CardHead>
                <div>
                  <CardTitle>2. Clinical Presentation & Medical History</CardTitle>
                  <span className="caption" style={{ color: 'var(--text-secondary)' }}>
                    Diagnostic evidence baseline and patient history profile
                  </span>
                </div>
              </CardHead>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                <TextField
                  label="Chief Complaint (Presenting Problem)"
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  placeholder="e.g. Acute substernal crushing chest pressure radiating to jaw and left arm"
                  required
                />

                <TextArea
                  label="History of Present Illness (HPI)"
                  value={hpi}
                  onChange={(e) => setHpi(e.target.value)}
                  placeholder="Onset, character, severity, radiation, aggravating or alleviating factors, associated symptoms..."
                  rows={2}
                />

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr)))',
                    gap: 'var(--space-4)',
                  }}
                >
                  <TextField
                    label="Past Medical History (comma-separated)"
                    value={pastMedicalHistory}
                    onChange={(e) => setPastMedicalHistory(e.target.value)}
                    placeholder="e.g. Hypertension, Type 2 DM, Hyperlipidemia"
                  />

                  <TextField
                    label="Active Medications (comma-separated)"
                    value={medications}
                    onChange={(e) => setMedications(e.target.value)}
                    placeholder="e.g. Metformin 1000mg BID, Atorvastatin 40mg QHS"
                  />
                </div>

                <TextField
                  label="Drug Allergies & Adverse Reactions"
                  value={allergies}
                  onChange={(e) => setAllergies(e.target.value)}
                  placeholder="e.g. Penicillin (Anaphylaxis), Sulfa (Rash), or NKDA"
                  helpText="Critical patient safety profile. Enter NKDA if no known allergies."
                />
              </div>
            </Card>

            {/* Section 3: Baseline Intake Vitals */}
            <Card>
              <CardHead>
                <div>
                  <CardTitle>3. Baseline Triage Vitals</CardTitle>
                  <span className="caption" style={{ color: 'var(--text-secondary)' }}>
                    Initial telemetry measurements recorded upon presentation
                  </span>
                </div>
              </CardHead>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                  gap: 'var(--space-3)',
                }}
              >
                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <label className="caption" style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-secondary)' }}>
                    <HeartPulse className="w-3.5 h-3.5" style={{ color: 'var(--color-success)' }} />
                    Heart Rate
                  </label>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginTop: 4 }}>
                    <input
                      type="number"
                      value={heartRate}
                      onChange={(e) => setHeartRate(Number(e.target.value))}
                      className="ak-num"
                      style={{
                        width: '100%',
                        fontSize: '1.125rem',
                        fontWeight: 700,
                        border: 'none',
                        background: 'transparent',
                        outline: 'none',
                      }}
                    />
                    <span className="caption" style={{ color: 'var(--text-tertiary)' }}>BPM</span>
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <label className="caption" style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-secondary)' }}>
                    <Activity className="w-3.5 h-3.5" style={{ color: 'var(--color-primary)' }} />
                    Systolic BP
                  </label>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginTop: 4 }}>
                    <input
                      type="number"
                      value={systolicBp}
                      onChange={(e) => setSystolicBp(Number(e.target.value))}
                      className="ak-num"
                      style={{
                        width: '100%',
                        fontSize: '1.125rem',
                        fontWeight: 700,
                        border: 'none',
                        background: 'transparent',
                        outline: 'none',
                      }}
                    />
                    <span className="caption" style={{ color: 'var(--text-tertiary)' }}>mmHg</span>
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <label className="caption" style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-secondary)' }}>
                    <Activity className="w-3.5 h-3.5" style={{ color: 'var(--color-primary)' }} />
                    Diastolic BP
                  </label>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginTop: 4 }}>
                    <input
                      type="number"
                      value={diastolicBp}
                      onChange={(e) => setDiastolicBp(Number(e.target.value))}
                      className="ak-num"
                      style={{
                        width: '100%',
                        fontSize: '1.125rem',
                        fontWeight: 700,
                        border: 'none',
                        background: 'transparent',
                        outline: 'none',
                      }}
                    />
                    <span className="caption" style={{ color: 'var(--text-tertiary)' }}>mmHg</span>
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <label className="caption" style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-secondary)' }}>
                    <Layers className="w-3.5 h-3.5" style={{ color: 'var(--text-tertiary)' }} />
                    Resp Rate
                  </label>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginTop: 4 }}>
                    <input
                      type="number"
                      value={respiratoryRate}
                      onChange={(e) => setRespiratoryRate(Number(e.target.value))}
                      className="ak-num"
                      style={{
                        width: '100%',
                        fontSize: '1.125rem',
                        fontWeight: 700,
                        border: 'none',
                        background: 'transparent',
                        outline: 'none',
                      }}
                    />
                    <span className="caption" style={{ color: 'var(--text-tertiary)' }}>bpm</span>
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <label className="caption" style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-secondary)' }}>
                    <Thermometer className="w-3.5 h-3.5" style={{ color: 'var(--color-primary)' }} />
                    SpO2
                  </label>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginTop: 4 }}>
                    <input
                      type="number"
                      step="0.1"
                      value={spo2}
                      onChange={(e) => setSpo2(Number(e.target.value))}
                      className="ak-num"
                      style={{
                        width: '100%',
                        fontSize: '1.125rem',
                        fontWeight: 700,
                        border: 'none',
                        background: 'transparent',
                        outline: 'none',
                      }}
                    />
                    <span className="caption" style={{ color: 'var(--text-tertiary)' }}>%</span>
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <label className="caption" style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-secondary)' }}>
                    <Thermometer className="w-3.5 h-3.5" style={{ color: 'var(--text-tertiary)' }} />
                    Core Temp
                  </label>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginTop: 4 }}>
                    <input
                      type="number"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(Number(e.target.value))}
                      className="ak-num"
                      style={{
                        width: '100%',
                        fontSize: '1.125rem',
                        fontWeight: 700,
                        border: 'none',
                        background: 'transparent',
                        outline: 'none',
                      }}
                    />
                    <span className="caption" style={{ color: 'var(--text-tertiary)' }}>°C</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* ACTION BUTTONS */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 'var(--space-4)',
                paddingTop: 'var(--space-2)',
              }}
            >
              <Button variant="secondary" size="md" onClick={handleResetForm}>
                Reset fields
              </Button>

              <Button
                variant="primary"
                size="lg"
                type="submit"
                disabled={isSubmitting}
                isLoading={isSubmitting}
                leadingIcon={<FileSpreadsheet className="w-4 h-4" />}
              >
                {isSubmitting ? 'Admitting patient...' : 'Admit patient to record system'}
              </Button>
            </div>
          </form>
        </>
    </AppPage>
  );
};

export default CaseIntakeAdmissionSection;
