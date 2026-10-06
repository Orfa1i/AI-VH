import React, { useState, useEffect } from 'react';
import type { PatientRecord } from '../../types';
import {
  Search,
  RefreshCw,
  Stethoscope,
  HeartPulse,
  Activity,
  Thermometer,
  ShieldAlert,
  FileText,
  Bed,
} from 'lucide-react';
import {
  Button,
  Badge,
  Card,
  Dialog,
  TextField,
  Select,
  Stat,
  EmptyState,
  Chip,
} from '../ui';

import { AppPage } from '../layout/Templates';

interface PatientDirectorySectionProps {
  onOpenConsult?: (patientName: string) => void;
  refreshTrigger?: number;
}

export const PatientDirectorySection: React.FC<PatientDirectorySectionProps> = ({
  onOpenConsult,
  refreshTrigger = 0,
}) => {
  const [patients, setPatients] = useState<PatientRecord[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [departmentFilter, setDepartmentFilter] = useState<string>('ALL');
  const [selectedPatient, setSelectedPatient] = useState<PatientRecord | null>(null);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const url = statusFilter === 'ALL' ? '/api/patients' : `/api/patients?status=${statusFilter}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setPatients(data.patients || []);
        setTotalCount(data.total || 0);
      }
    } catch (err) {
      console.error('Failed to load patients:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, [statusFilter, refreshTrigger]);

  const handleDischarge = async (patientId: string) => {
    if (!confirm('Are you sure you want to discharge this patient?')) return;
    try {
      const res = await fetch(`/api/patients/${patientId}/discharge`, {
        method: 'POST',
      });
      if (res.ok) {
        fetchPatients();
        if (selectedPatient && selectedPatient.id === patientId) {
          setSelectedPatient((prev) => (prev ? { ...prev, admission_status: 'DISCHARGED' } : null));
        }
      }
    } catch (err) {
      console.error('Error discharging patient:', err);
    }
  };

  // Filtered patients
  const filteredPatients = patients.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.mrn.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.chief_complaint.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDept = departmentFilter === 'ALL' || p.assigned_department === departmentFilter;
    return matchesSearch && matchesDept;
  });

  // Calculate stats
  const admittedCount = patients.filter((p) => p.admission_status === 'ADMITTED').length;
  const dischargedCount = patients.filter((p) => p.admission_status === 'DISCHARGED').length;
  const criticalCount = patients.filter(
    (p) => p.triage_acuity === 'RESUSCITATION' || p.triage_acuity === 'EMERGENT'
  ).length;

  const getAcuityVariant = (acuity: string): 'danger' | 'warning' | 'info' | 'success' | 'neutral' => {
    switch (acuity) {
      case 'RESUSCITATION':
      case 'EMERGENT':
        return 'danger';
      case 'URGENT':
        return 'warning';
      case 'LESS_URGENT':
        return 'info';
      case 'NON_URGENT':
        return 'success';
      default:
        return 'neutral';
    }
  };

  return (
    <AppPage
      title="Inpatient Census & Bed Board"
      description="Active inpatient status, bed assignments, longitudinal vitals telemetry, and discharge workflow."
      breadcrumbs={[
        { label: 'Clinical Ops', href: '#' },
        { label: 'Census & Bed Board', isCurrent: true },
      ]}
      actions={
        <Button
          variant="secondary"
          size="md"
          onClick={fetchPatients}
          disabled={loading}
          leadingIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
        >
          Refresh Census
        </Button>
      }
    >
      {/* KPI METRIC CARDS */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <Stat label="Total Registered Census" value={totalCount} delta="All records" />
        <Stat label="Active Admitted" value={admittedCount} delta="Bed occupancy" />
        <Stat label="High Acuity (ESI 1-2)" value={criticalCount} delta="Critical surveillance" />
        <Stat label="Discharged" value={dischargedCount} delta="Completed stays" />
      </div>

      {/* FILTER & SEARCH BAR */}
      <Card style={{ marginBottom: 'var(--space-6)' }}>
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--space-4)',
          }}
        >
          {/* Search Field */}
          <div style={{ flex: '1 1 300px', maxWidth: 440 }}>
            <TextField
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by patient name, MRN, or complaint..."
              leadingIcon={<Search className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />}
            />
          </div>

          {/* Filter Chips & Select */}
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 'var(--space-2)' }}>
            <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
              {['ALL', 'ADMITTED', 'DISCHARGED'].map((st) => (
                <Chip
                  key={st}
                  isSelected={statusFilter === st}
                  onClick={() => setStatusFilter(st)}
                >
                  {st === 'ALL' ? 'All Patients' : st === 'ADMITTED' ? 'Admitted' : 'Discharged'}
                </Chip>
              ))}
            </div>

            <div style={{ minWidth: 180 }}>
              <Select
                value={departmentFilter}
                onChange={(e) => setDepartmentFilter(e.target.value)}
              >
                <option value="ALL">All Departments</option>
                <option value="EMERGENCY">Emergency</option>
                <option value="CARDIOLOGY">Cardiology / CCU</option>
                <option value="ICU">Medical ICU</option>
                <option value="INTERNAL_MEDICINE">Internal Medicine</option>
                <option value="STEP_DOWN">Step-Down Wing</option>
              </Select>
            </div>
          </div>
        </div>
      </Card>

      {/* PATIENT DIRECTORY GRID */}
      {loading ? (
        <Card style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <div
            style={{
              width: 32,
              height: 32,
              margin: '0 auto var(--space-3)',
              borderRadius: '50%',
              border: '2px solid var(--border-subtle)',
              borderTopColor: 'var(--color-primary)',
              animation: 'spin 1s linear infinite',
            }}
          />
          <p className="caption" style={{ color: 'var(--text-secondary)' }}>
            Synchronizing inpatient census records...
          </p>
        </Card>
      ) : filteredPatients.length === 0 ? (
        <EmptyState
          icon={<FileText className="w-8 h-8" />}
          title="No patient records found"
          description={
            searchTerm || departmentFilter !== 'ALL' || statusFilter !== 'ALL'
              ? 'No patients match your current filter criteria. Try clearing filters or search query.'
              : 'The inpatient census is currently empty. Use Case Intake & Triage to admit patients.'
          }
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: 'var(--space-4)',
          }}
        >
          {filteredPatients.map((p) => {
            const isAdmitted = p.admission_status === 'ADMITTED';
            const vitals = p.baseline_vitals || {};

            return (
              <Card
                key={p.id}
                variant="interactive"
                onClick={() => setSelectedPatient(p)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  height: '100%',
                }}
              >
                <div>
                  {/* Top Bar: Name, Demographics, Status Badge */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      justifyContent: 'space-between',
                      gap: 'var(--space-2)',
                      marginBottom: 'var(--space-2)',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <h3 className="heading-3" style={{ margin: 0 }}>
                          {p.name}
                        </h3>
                        <span className="caption ak-num" style={{ color: 'var(--text-tertiary)' }}>
                          {p.age}y {p.sex}
                        </span>
                      </div>
                      <div
                        className="caption ak-num"
                        style={{
                          color: 'var(--text-secondary)',
                          marginTop: 2,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        <span>MRN: <strong>{p.mrn}</strong></span>
                        <span>•</span>
                        <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>{p.id}</span>
                      </div>
                    </div>

                    <Badge
                      variant={isAdmitted ? 'success' : 'neutral'}
                      hasDot={isAdmitted}
                    >
                      {p.admission_status}
                    </Badge>
                  </div>

                  {/* Bed & Acuity Badges */}
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: 'var(--space-2)',
                      margin: 'var(--space-3) 0',
                    }}
                  >
                    <Badge variant="outline">
                      <Bed className="w-3 h-3" style={{ marginRight: 4, display: 'inline-block' }} />
                      {p.assigned_department} • Bed {p.bed_number || 'TBD'}
                    </Badge>
                    <Badge variant={getAcuityVariant(p.triage_acuity)}>
                      {p.triage_acuity}
                    </Badge>
                  </div>

                  {/* Presenting Problem */}
                  <div
                    style={{
                      backgroundColor: 'var(--bg-app)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: 'var(--space-2) var(--space-3)',
                      margin: 'var(--space-2) 0',
                    }}
                  >
                    <div
                      className="caption"
                      style={{
                        color: 'var(--text-tertiary)',
                        textTransform: 'uppercase',
                        fontWeight: 600,
                        fontSize: '0.6875rem',
                        letterSpacing: '0.04em',
                        marginBottom: 2,
                      }}
                    >
                      Presenting Problem
                    </div>
                    <p
                      className="body-sm"
                      style={{
                        margin: 0,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {p.chief_complaint}
                    </p>
                  </div>

                  {/* Vitals Telemetry Ribbon */}
                  {vitals.heart_rate && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        backgroundColor: 'var(--bg-app)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        padding: 'var(--space-2) var(--space-3)',
                        marginTop: 'var(--space-2)',
                        fontSize: '0.75rem',
                      }}
                    >
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <HeartPulse className="w-3 h-3" style={{ color: 'var(--color-success)' }} />
                        <span className="ak-num" style={{ fontWeight: 600 }}>{vitals.heart_rate}</span> BPM
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Activity className="w-3 h-3" style={{ color: 'var(--color-primary)' }} />
                        <span className="ak-num" style={{ fontWeight: 600 }}>{vitals.systolic_bp}/{vitals.diastolic_bp}</span>
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Thermometer className="w-3 h-3" style={{ color: 'var(--color-primary)' }} />
                        <span className="ak-num" style={{ fontWeight: 600 }}>{vitals.spo2}%</span>
                      </span>
                    </div>
                  )}
                </div>

                {/* Card Footer Actions */}
                <div
                  style={{
                    marginTop: 'var(--space-4)',
                    paddingTop: 'var(--space-3)',
                    borderTop: '1px solid var(--border-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span className="caption ak-num" style={{ color: 'var(--text-tertiary)' }}>
                    Admitted {new Date(p.admitted_at).toLocaleDateString()}
                  </span>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    {onOpenConsult && isAdmitted && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenConsult(p.name);
                        }}
                        leadingIcon={<Stethoscope className="w-3 h-3" />}
                      >
                        Consult
                      </Button>
                    )}

                    {isAdmitted && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDischarge(p.id);
                        }}
                        style={{ color: 'var(--color-danger)' }}
                      >
                        Discharge
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* PATIENT DETAIL MODAL DIALOG */}
      {selectedPatient && (
        <Dialog
          isOpen={Boolean(selectedPatient)}
          onClose={() => setSelectedPatient(null)}
          title={selectedPatient.name}
          description={`MRN ${selectedPatient.mrn} • ${selectedPatient.age}y ${selectedPatient.sex} • ${selectedPatient.assigned_department} (Bed: ${selectedPatient.bed_number || 'TBD'})`}
          actions={
            <>
              <Button variant="secondary" onClick={() => setSelectedPatient(null)}>
                Close Chart
              </Button>
              {onOpenConsult && selectedPatient.admission_status === 'ADMITTED' && (
                <Button
                  variant="primary"
                  onClick={() => {
                    onOpenConsult(selectedPatient.name);
                    setSelectedPatient(null);
                  }}
                  leadingIcon={<Stethoscope className="w-4 h-4" />}
                >
                  Consult Specialist
                </Button>
              )}
              {selectedPatient.admission_status === 'ADMITTED' && (
                <Button
                  variant="danger"
                  onClick={() => handleDischarge(selectedPatient.id)}
                >
                  Discharge Patient
                </Button>
              )}
            </>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div>
              <span className="ak-label" style={{ display: 'block', marginBottom: 4 }}>
                Chief Complaint (Presenting Problem)
              </span>
              <div
                style={{
                  backgroundColor: 'var(--bg-app)',
                  padding: 'var(--space-3)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <p className="body" style={{ margin: 0, fontWeight: 500 }}>
                  {selectedPatient.chief_complaint}
                </p>
              </div>
            </div>

            {selectedPatient.history_of_present_illness && (
              <div>
                <span className="ak-label" style={{ display: 'block', marginBottom: 4 }}>
                  History of Present Illness (HPI)
                </span>
                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <p className="body-sm" style={{ margin: 0, color: 'var(--text-secondary)' }}>
                    {selectedPatient.history_of_present_illness}
                  </p>
                </div>
              </div>
            )}

            {selectedPatient.baseline_vitals && (
              <div>
                <span className="ak-label" style={{ display: 'block', marginBottom: 6 }}>
                  Admission Baseline Vitals Telemetry
                </span>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
                    gap: 'var(--space-2)',
                  }}
                >
                  <div
                    style={{
                      backgroundColor: 'var(--bg-app)',
                      padding: 'var(--space-2)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      textAlign: 'center',
                    }}
                  >
                    <div className="caption" style={{ color: 'var(--text-tertiary)' }}>Heart Rate</div>
                    <div className="ak-num" style={{ fontWeight: 700, marginTop: 2 }}>
                      {selectedPatient.baseline_vitals.heart_rate} BPM
                    </div>
                  </div>
                  <div
                    style={{
                      backgroundColor: 'var(--bg-app)',
                      padding: 'var(--space-2)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      textAlign: 'center',
                    }}
                  >
                    <div className="caption" style={{ color: 'var(--text-tertiary)' }}>BP</div>
                    <div className="ak-num" style={{ fontWeight: 700, marginTop: 2 }}>
                      {selectedPatient.baseline_vitals.systolic_bp}/{selectedPatient.baseline_vitals.diastolic_bp}
                    </div>
                  </div>
                  <div
                    style={{
                      backgroundColor: 'var(--bg-app)',
                      padding: 'var(--space-2)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      textAlign: 'center',
                    }}
                  >
                    <div className="caption" style={{ color: 'var(--text-tertiary)' }}>Resp Rate</div>
                    <div className="ak-num" style={{ fontWeight: 700, marginTop: 2 }}>
                      {selectedPatient.baseline_vitals.respiratory_rate} /min
                    </div>
                  </div>
                  <div
                    style={{
                      backgroundColor: 'var(--bg-app)',
                      padding: 'var(--space-2)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      textAlign: 'center',
                    }}
                  >
                    <div className="caption" style={{ color: 'var(--text-tertiary)' }}>SpO2</div>
                    <div className="ak-num" style={{ fontWeight: 700, marginTop: 2 }}>
                      {selectedPatient.baseline_vitals.spo2}%
                    </div>
                  </div>
                  <div
                    style={{
                      backgroundColor: 'var(--bg-app)',
                      padding: 'var(--space-2)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      textAlign: 'center',
                    }}
                  >
                    <div className="caption" style={{ color: 'var(--text-tertiary)' }}>Core Temp</div>
                    <div className="ak-num" style={{ fontWeight: 700, marginTop: 2 }}>
                      {selectedPatient.baseline_vitals.temperature_c}°C
                    </div>
                  </div>
                  <div
                    style={{
                      backgroundColor: 'var(--bg-app)',
                      padding: 'var(--space-2)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      textAlign: 'center',
                    }}
                  >
                    <div className="caption" style={{ color: 'var(--text-tertiary)' }}>Acuity</div>
                    <Badge variant={getAcuityVariant(selectedPatient.triage_acuity)} style={{ marginTop: 2 }}>
                      {selectedPatient.triage_acuity}
                    </Badge>
                  </div>
                </div>
              </div>
            )}

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: 'var(--space-3)',
              }}
            >
              <div>
                <span className="ak-label" style={{ display: 'block', marginBottom: 4 }}>
                  Past Medical History
                </span>
                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    minHeight: 52,
                  }}
                >
                  <p className="body-sm" style={{ margin: 0 }}>
                    {selectedPatient.past_medical_history?.join(', ') || 'None recorded'}
                  </p>
                </div>
              </div>

              <div>
                <span className="ak-label" style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
                  <ShieldAlert className="w-3.5 h-3.5" style={{ color: 'var(--color-danger)' }} />
                  <span>Allergies & Adverse Reactions</span>
                </span>
                <div
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    minHeight: 52,
                  }}
                >
                  <p className="body-sm" style={{ margin: 0, color: selectedPatient.allergies?.length ? 'var(--color-danger)' : 'inherit' }}>
                    {selectedPatient.allergies?.join(', ') || 'No known drug allergies (NKDA)'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Dialog>
      )}
    </AppPage>
  );
};

export default PatientDirectorySection;
