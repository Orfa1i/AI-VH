import React, { useState, useEffect } from 'react';
import type { HospitalStaffRecord } from '../../types';
import drMarcusPhoto from '../../assets/dr_marcus_vance.jpg';
import { DoctorChatModal } from '../specialists/DoctorChatModal';
import {
  Stethoscope,
  HeartPulse,
  FlaskConical,
  FileScan,
  ClipboardList,
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

interface StaffManagementSectionProps {
  onOpenConsult?: () => void;
}

export const StaffManagementSection: React.FC<StaffManagementSectionProps> = ({ onOpenConsult }) => {
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
            const photoSrc = isVance ? (staff.avatar_url || drMarcusPhoto) : staff.avatar_url;

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
                      {onOpenConsult && (
                        <Button size="sm" variant="secondary" onClick={onOpenConsult}>
                          Consult
                        </Button>
                      )}
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
