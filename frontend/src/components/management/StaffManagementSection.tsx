import React, { useState, useEffect } from 'react';
import type { HospitalStaffRecord } from '../../types';
import agentInternalMed from '../../assets/vh-agent-internal-medicine-512.png';
import agentCardiology from '../../assets/vh-agent-cardiology-512.png';
import agentNeurology from '../../assets/vh-agent-neurology-512.png';
import agentSurgery from '../../assets/vh-agent-surgery-512.png';
import agentEmergency from '../../assets/vh-agent-emergency-512.png';
import agentObstetrics from '../../assets/vh-agent-obstetrics-512.png';
import agentGynecology from '../../assets/vh-agent-gynecology-512.png';
import { DoctorChatModal } from '../specialists/DoctorChatModal';
import {
  Stethoscope,
  HeartPulse,
  FlaskConical,
  FileScan,
  ClipboardList,
  Bot,
  Brain,
} from 'lucide-react';
import {
  Button,
  Badge,
  Card,
  CardHead,
  CardTitle,
  CardMeta,
  TextField,
  TextArea,
  Select,
  Dialog,
  Stat,
  EmptyState,
} from '../ui';
import { AppPage } from '../layout/Templates';

const AI_SPECIALIST_AGENTS = [
  {
    name: 'Dr. Marcus Vance, MD',
    specialty: 'Internal Medicine',
    avatar: agentInternalMed,
    evidence: "Harrison's 21st Ed.",
    status: 'ACTIVE_CHIEF',
    roleTag: 'Chief Attending',
  },
  {
    name: 'Dr. Elena Rostova, MD',
    specialty: 'Cardiology',
    avatar: agentCardiology,
    evidence: "Braunwald's Heart Dis.",
    status: 'ON_DUTY',
    roleTag: 'Cardiologist',
  },
  {
    name: 'Dr. Julian Thorne, MD',
    specialty: 'Neurology',
    avatar: agentNeurology,
    evidence: "Adams & Victor's Neuro",
    status: 'ON_DUTY',
    roleTag: 'Neurologist',
  },
  {
    name: 'Dr. Sarah Lin, MD',
    specialty: 'General Surgery',
    avatar: agentSurgery,
    evidence: "Schwartz's Surgery",
    status: 'STANDBY',
    roleTag: 'Lead Surgeon',
  },
  {
    name: 'Dr. Malik Sterling, MD',
    specialty: 'Emergency Medicine',
    avatar: agentEmergency,
    evidence: "Tintinalli's EM",
    status: 'ON_DUTY',
    roleTag: 'Trauma & Triage',
  },
  {
    name: 'Dr. Claire Laurent, MD',
    specialty: 'Obstetrics',
    avatar: agentObstetrics,
    evidence: 'Williams Obstetrics',
    status: 'ON_DUTY',
    roleTag: 'Perinatal Care',
  },
  {
    name: 'Dr. Maya Patel, MD',
    specialty: 'Gynecology',
    avatar: agentGynecology,
    evidence: 'Williams Gynecology',
    status: 'ON_DUTY',
    roleTag: 'Gynecology',
  },
];

const SPECIALTY_AVATARS: Record<string, string> = {
  INTERNAL_MEDICINE: agentInternalMed,
  CARDIOLOGY: agentCardiology,
  NEUROLOGY: agentNeurology,
  SURGERY: agentSurgery,
  EMERGENCY: agentEmergency,
  OBSTETRICS: agentObstetrics,
  GYNECOLOGY: agentGynecology,
};

const getStaffAvatar = (staff: HospitalStaffRecord): string | undefined => {
  if (staff.id === 'STAFF-VANCE' || staff.name.includes('Marcus Vance')) {
    return agentInternalMed;
  }
  if (staff.avatar_url && staff.avatar_url.trim()) {
    if (staff.avatar_url.includes('internal-medicine') || staff.avatar_url.includes('dr_marcus_vance')) return agentInternalMed;
    if (staff.avatar_url.includes('cardiology')) return agentCardiology;
    if (staff.avatar_url.includes('neurology')) return agentNeurology;
    if (staff.avatar_url.includes('surgery')) return agentSurgery;
    if (staff.avatar_url.includes('emergency')) return agentEmergency;
    if (staff.avatar_url.includes('obstetrics')) return agentObstetrics;
    if (staff.avatar_url.includes('gynecology')) return agentGynecology;
    return staff.avatar_url;
  }
  const specKey = (staff.specialty || staff.department || '').toUpperCase().replace(/\s+/g, '_');
  return SPECIALTY_AVATARS[specKey];
};

interface StaffManagementSectionProps {}

export const StaffManagementSection: React.FC<StaffManagementSectionProps> = () => {
  const [staffList, setStaffList] = useState<HospitalStaffRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [departmentFilter, setDepartmentFilter] = useState<string>('ALL');
  const [isRegisterOpen, setIsRegisterOpen] = useState<boolean>(false);
  const [isDoctorChatOpen, setIsDoctorChatOpen] = useState<boolean>(false);
  const [selectedPhoto, setSelectedPhoto] = useState<{ src: string; name: string; title: string } | null>(null);

  // New staff form state
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState<'DOCTOR' | 'NURSE' | 'RADIOLOGIST' | 'LAB_SCIENTIST' | 'RECEPTIONIST'>('DOCTOR');
  const [newSpecialty, setNewSpecialty] = useState('INTERNAL_MEDICINE');
  const [newTitle, setNewTitle] = useState('Attending Specialist Physician');
  const [newDepartment, setNewDepartment] = useState('INTERNAL_MEDICINE');
  const [newCredentials, setNewCredentials] = useState('MD, FACP');
  const [newBio, setNewBio] = useState('');
  const [newSystemPrompt, setNewSystemPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const fetchStaff = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/staff');
      if (res.ok) {
        const data = await res.json();
        setStaffList(data.staff || []);
      }
    } catch (err) {
      console.error('Failed to load staff roster:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStaff();
  }, []);

  const handleUpdateStatus = async (staffId: string, status: 'ON_DUTY' | 'IN_CONSULT' | 'OFF_DUTY') => {
    setStaffList((prev) =>
      prev.map((s) => (s.id === staffId ? { ...s, status } : s))
    );

    try {
      const res = await fetch(`/api/staff/${staffId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        fetchStaff();
      }
    } catch {
      fetchStaff();
    }
  };

  const handleDeleteStaff = async (staffId: string, staffName: string) => {
    if (!window.confirm(`Remove ${staffName} from active hospital medical staff?`)) return;

    try {
      const res = await fetch(`/api/staff/${staffId}`, { method: 'DELETE' });
      if (res.ok) {
        setStaffList((prev) => prev.filter((s) => s.id !== staffId));
      }
    } catch (err) {
      console.error('Failed to remove staff record:', err);
    }
  };

  const handleRegisterStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    setIsSubmitting(true);
    try {
      const payload = {
        name: newName.trim(),
        role: newRole,
        specialty: newSpecialty.trim(),
        title: newTitle.trim(),
        department: newDepartment,
        credentials: newCredentials.trim(),
        bio: newBio.trim(),
        system_prompt: newSystemPrompt.trim(),
      };

      const res = await fetch('/api/staff', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setIsRegisterOpen(false);
        setNewName('');
        setNewBio('');
        setNewSystemPrompt('');
        fetchStaff();
      }
    } catch (err) {
      console.error('Failed to register healthcare professional:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredStaff = staffList.filter((s) => {
    if (roleFilter !== 'ALL' && s.role !== roleFilter) return false;
    if (departmentFilter !== 'ALL' && s.department !== departmentFilter) return false;
    return true;
  });

  const onDutyCount = staffList.filter((s) => s.status === 'ON_DUTY').length;
  const inConsultCount = staffList.filter((s) => s.status === 'IN_CONSULT').length;

  return (
    <AppPage
      title="Hospital Staff Roster"
      description="Credentialed medical staff directory, shift statuses, clinical reasoning models, and Harrison's RAG specialists."
      actions={
        <Button variant="primary" size="sm" onClick={() => setIsRegisterOpen(true)}>
          <span>Register professional</span>
        </Button>
      }
    >
      {/* KPI Stats Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <Card>
          <Stat label="Credentialed Staff" value={staffList.length} delta="Active in hospital roster" />
        </Card>
        <Card>
          <Stat label="On Duty Status" value={onDutyCount} delta="Ready for encounters" />
        </Card>
        <Card>
          <Stat label="Active Consultations" value={inConsultCount} delta="In-progress evaluations" />
        </Card>
        <Card>
          <Stat label="Chief Specialty" value="Internal Med" delta="Harrison's RAG active" />
        </Card>
      </div>

      {/* AI Specialist Agent Roster Showcase */}
      <Card style={{ marginBottom: 'var(--space-6)', overflow: 'hidden' }}>
        <div style={{ padding: 'var(--space-5)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <div style={{ padding: '4px 8px', borderRadius: 'var(--radius-sm)', background: 'var(--action-primary-subtle)', color: 'var(--action-primary)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600 }}>
                  <Bot style={{ width: 14, height: 14 }} />
                  <span>AI CLINICAL AGENTS</span>
                </div>
                <Badge variant="primary">7 Specialty Departments</Badge>
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 700, margin: '6px 0 2px', color: 'var(--text-primary)' }}>
                Asklevia Autonomous Specialist Agents
              </h3>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0 }}>
                High-fidelity medical intelligence agents grounded in gold-standard reference textbooks and peer-reviewed clinical knowledge bases.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Button
                variant="secondary"
                size="sm"
                leadingIcon={<Brain style={{ width: 14, height: 14 }} />}
                onClick={() => setIsDoctorChatOpen(true)}
              >
                <span>Consult Dr. Vance (Harrison's RAG)</span>
              </Button>
            </div>
          </div>

          {/* 7 Agent Doctor Cards Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: 'var(--space-3)',
              marginTop: 'var(--space-3)',
            }}
          >
            {AI_SPECIALIST_AGENTS.map((agent) => (
              <div
                key={agent.specialty}
                onClick={() => {
                  setSelectedPhoto({
                    src: agent.avatar,
                    name: agent.name,
                    title: `${agent.specialty} Specialist`,
                  });
                }}
                style={{
                  background: 'var(--bg-subtle)',
                  borderRadius: 'var(--radius-lg)',
                  border: '1px solid var(--border-subtle)',
                  padding: 'var(--space-3)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--action-primary)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div style={{ position: 'relative', width: 64, height: 64, marginBottom: 'var(--space-2)' }}>
                  <img
                    src={agent.avatar}
                    alt={agent.name}
                    style={{
                      width: '100%',
                      height: '100%',
                      borderRadius: 'var(--radius-md)',
                      objectFit: 'cover',
                      border: '1px solid var(--border-default)',
                    }}
                  />
                  <span
                    style={{
                      position: 'absolute',
                      bottom: -2,
                      right: -2,
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      backgroundColor: 'var(--status-success)',
                      border: '2px solid white',
                    }}
                  />
                </div>
                <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                  {agent.specialty}
                </span>
                <span style={{ fontSize: 10, color: 'var(--action-primary)', marginTop: 2, fontWeight: 600 }}>
                  {agent.roleTag}
                </span>
                <span style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 4, fontFamily: 'monospace' }}>
                  {agent.evidence}
                </span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Filter Row */}
      <Card style={{ marginBottom: 'var(--space-6)' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-4)' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 'var(--space-4)' }}>
            <div style={{ width: 200 }}>
              <Select
                label="Role"
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
              >
                <option value="ALL">All Roles</option>
                <option value="DOCTOR">Physicians (MD)</option>
                <option value="NURSE">Nurses (RN)</option>
                <option value="LAB_SCIENTIST">Lab Scientists (MLS)</option>
                <option value="RADIOLOGIST">Radiologists (MD)</option>
                <option value="RECEPTIONIST">Admissions</option>
              </Select>
            </div>

            <div style={{ width: 220 }}>
              <Select
                label="Department"
                value={departmentFilter}
                onChange={(e) => setDepartmentFilter(e.target.value)}
              >
                <option value="ALL">All Departments</option>
                <option value="INTERNAL_MEDICINE">Internal Medicine</option>
                <option value="EMERGENCY">Emergency</option>
                <option value="LABORATORY">Laboratory</option>
                <option value="RADIOLOGY">Radiology</option>
                <option value="RECEPTION">Reception</option>
              </Select>
            </div>
          </div>

          <span className="caption ak-num" style={{ color: 'var(--text-secondary)' }}>
            Showing {filteredStaff.length} of {staffList.length} staff members
          </span>
        </div>
      </Card>

      {/* Staff Grid */}
      {loading ? (
        <Card style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <div className="ak-spinner ak-spinner--lg" style={{ margin: '0 auto var(--space-4)' }} />
          <p className="heading-3">Loading staff directory</p>
        </Card>
      ) : filteredStaff.length === 0 ? (
        <Card>
          <EmptyState
            title="No Staff Members Found"
            description="No matching staff records were found for the selected filters."
            action={<Button variant="secondary" onClick={() => setIsRegisterOpen(true)}>Register professional</Button>}
          />
        </Card>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
            gap: 'var(--space-6)',
          }}
        >
          {filteredStaff.map((staff) => {
            const isVance = staff.id === 'STAFF-VANCE' || staff.name.includes('Marcus Vance');
            const isOnDuty = staff.status === 'ON_DUTY';
            const isInConsult = staff.status === 'IN_CONSULT';
            const photoSrc = getStaffAvatar(staff);

            return (
              <Card key={staff.id}>
                <CardHead>
                  <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'center' }}>
                    {photoSrc ? (
                      <div
                        style={{
                          width: 64,
                          height: 64,
                          borderRadius: 'var(--radius-md)',
                          overflow: 'hidden',
                          flexShrink: 0,
                          cursor: 'pointer',
                          boxShadow: 'var(--shadow-xs)',
                          border: '1px solid var(--border-default)',
                        }}
                        onClick={() =>
                          setSelectedPhoto({
                            src: photoSrc,
                            name: staff.name,
                            title: staff.title,
                          })
                        }
                      >
                        <img
                          src={photoSrc}
                          alt={staff.name}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      </div>
                    ) : (
                      <div
                        style={{
                          width: 64,
                          height: 64,
                          borderRadius: 'var(--radius-md)',
                          background: 'var(--bg-subtle)',
                          display: 'grid',
                          placeItems: 'center',
                          flexShrink: 0,
                          color: 'var(--action-primary)',
                        }}
                      >
                        {staff.role === 'DOCTOR' && <Stethoscope style={{ width: 24, height: 24 }} />}
                        {staff.role === 'NURSE' && <HeartPulse style={{ width: 24, height: 24 }} />}
                        {staff.role === 'LAB_SCIENTIST' && <FlaskConical style={{ width: 24, height: 24 }} />}
                        {staff.role === 'RADIOLOGIST' && <FileScan style={{ width: 24, height: 24 }} />}
                        {staff.role === 'RECEPTIONIST' && <ClipboardList style={{ width: 24, height: 24 }} />}
                      </div>
                    )}

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <CardTitle style={{ fontSize: 18 }}>{staff.name}</CardTitle>
                        <Badge variant="outline">{staff.credentials}</Badge>
                      </div>
                      <CardMeta style={{ color: 'var(--action-primary)', fontWeight: 500 }}>
                        {staff.title}
                      </CardMeta>
                    </div>
                  </div>

                  <Badge variant={isOnDuty ? 'success' : isInConsult ? 'warning' : 'neutral'} hasDot>
                    {isOnDuty ? 'On duty' : isInConsult ? 'In consult' : 'Off duty'}
                  </Badge>
                </CardHead>

                {/* Subspecialty badges */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  <Badge variant="neutral">{staff.department.replace(/_/g, ' ')}</Badge>
                  <Badge variant="neutral">{staff.specialty.replace(/_/g, ' ')}</Badge>
                  {isVance && <Badge variant="ai">Harrison's RAG Guided</Badge>}
                  <Badge variant="outline"><span className="ak-num">{staff.total_encounters}</span> encounters</Badge>
                </div>

                {/* Bio */}
                <p className="body-sm" style={{ color: 'var(--text-secondary)', lineHeight: '20px' }}>
                  {staff.bio}
                </p>

                {/* Actions & Shift Buttons */}
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 8,
                    marginTop: 'auto',
                    paddingTop: 'var(--space-3)',
                    borderTop: '1px solid var(--border-default)',
                  }}
                >
                  <div className="ak-seg">
                    <button
                      type="button"
                      aria-pressed={isOnDuty}
                      className="ak-seg__item"
                      style={{ fontSize: 11, height: 26, padding: '0 8px' }}
                      onClick={() => handleUpdateStatus(staff.id, 'ON_DUTY')}
                    >
                      On duty
                    </button>
                    <button
                      type="button"
                      aria-pressed={isInConsult}
                      className="ak-seg__item"
                      style={{ fontSize: 11, height: 26, padding: '0 8px' }}
                      onClick={() => handleUpdateStatus(staff.id, 'IN_CONSULT')}
                    >
                      In consult
                    </button>
                    <button
                      type="button"
                      aria-pressed={staff.status === 'OFF_DUTY'}
                      className="ak-seg__item"
                      style={{ fontSize: 11, height: 26, padding: '0 8px' }}
                      onClick={() => handleUpdateStatus(staff.id, 'OFF_DUTY')}
                    >
                      Off duty
                    </button>
                  </div>

                  {isVance ? (
                    <div style={{ display: 'flex', gap: 6 }}>
                      <Button size="sm" variant="primary" onClick={() => setIsDoctorChatOpen(true)}>
                        Chat
                      </Button>
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      variant="ghost"
                      style={{ color: 'var(--danger-600)' }}
                      onClick={() => handleDeleteStaff(staff.id, staff.name)}
                    >
                      Remove
                    </Button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Registration Modal Dialog */}
      <Dialog
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        title="Register Healthcare Professional"
        description="Add a specialist, attending physician, or medical officer to the hospital directory."
        actions={
          <>
            <Button variant="secondary" onClick={() => setIsRegisterOpen(false)}>
              Dismiss
            </Button>
            <Button
              variant="primary"
              onClick={handleRegisterStaff}
              disabled={isSubmitting || !newName.trim()}
              isLoading={isSubmitting}
            >
              Register professional
            </Button>
          </>
        }
      >
        <form onSubmit={handleRegisterStaff} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <TextField
              label="Full Name"
              placeholder="e.g. Dr. Eleanor Vance"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              required
            />
            <TextField
              label="Credentials"
              placeholder="MD, FACP / PharmD"
              value={newCredentials}
              onChange={(e) => setNewCredentials(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Select
              label="Role"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as any)}
            >
              <option value="DOCTOR">DOCTOR (Physician)</option>
              <option value="NURSE">NURSE (Triage / Floor RN)</option>
              <option value="LAB_SCIENTIST">LAB_SCIENTIST (Pathology)</option>
              <option value="RADIOLOGIST">RADIOLOGIST (Imaging)</option>
              <option value="RECEPTIONIST">RECEPTIONIST (Admissions)</option>
            </Select>

            <Select
              label="Department"
              value={newDepartment}
              onChange={(e) => setNewDepartment(e.target.value)}
            >
              <option value="INTERNAL_MEDICINE">Internal Medicine</option>
              <option value="EMERGENCY">Emergency Department</option>
              <option value="LABORATORY">Laboratory</option>
              <option value="RADIOLOGY">Radiology</option>
              <option value="CARDIOLOGY">Cardiology</option>
              <option value="ICU">Intensive Care (ICU)</option>
              <option value="RECEPTION">Admissions / Reception</option>
            </Select>
          </div>

          <TextField
            label="Title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="e.g. Attending Specialist Physician"
            required
          />

          <TextField
            label="Specialty"
            value={newSpecialty}
            onChange={(e) => setNewSpecialty(e.target.value)}
            placeholder="e.g. NEUROLOGY or CRITICAL_CARE"
            required
          />

          <TextArea
            label="Clinical Biography"
            value={newBio}
            onChange={(e) => setNewBio(e.target.value)}
            placeholder="Subspecialty focus, clinical background, academic affiliations..."
            rows={2}
          />
        </form>
      </Dialog>

      {/* Full Portrait Modal Dialog */}
      {selectedPhoto && (
        <Dialog
          isOpen={Boolean(selectedPhoto)}
          onClose={() => setSelectedPhoto(null)}
          title={selectedPhoto.name}
          description={selectedPhoto.title}
          actions={
            <Button variant="secondary" onClick={() => setSelectedPhoto(null)}>
              Close
            </Button>
          }
        >
          <div style={{ textAlign: 'center' }}>
            <img
              src={selectedPhoto.src}
              alt={selectedPhoto.name}
              style={{
                width: 240,
                height: 240,
                objectFit: 'cover',
                borderRadius: 'var(--radius-lg)',
                margin: '0 auto var(--space-4)',
                boxShadow: 'var(--shadow-md)',
              }}
            />
          </div>
        </Dialog>
      )}

      {/* Doctor Chat Modal */}
      <DoctorChatModal
        isOpen={isDoctorChatOpen}
        onClose={() => setIsDoctorChatOpen(false)}
      />
    </AppPage>
  );
};

export default StaffManagementSection;
