import React, { useState, useEffect, useRef } from 'react';
import { DoctorChatModal } from '../specialists/DoctorChatModal';
import {
  Button,
  TextField,
  TextArea,
  Select,
  Dialog,
} from '../ui';

export interface StaffManagementSectionProps {
  onNavigateTab?: (tab: string) => void;
}

export const StaffManagementSection: React.FC<StaffManagementSectionProps> = ({
  onNavigateTab,
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isRegisterOpen, setIsRegisterOpen] = useState<boolean>(false);
  const [isDoctorChatOpen, setIsDoctorChatOpen] = useState<boolean>(false);
  const [activeDoctorContext, setActiveDoctorContext] = useState<{ key?: string; name?: string }>({});

  // New staff registration form state
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState<'DOCTOR' | 'NURSE' | 'RADIOLOGIST' | 'LAB_SCIENTIST' | 'RECEPTIONIST'>('DOCTOR');
  const [newSpecialty, setNewSpecialty] = useState('INTERNAL_MEDICINE');
  const [newTitle, setNewTitle] = useState('Attending Specialist Physician');
  const [newDepartment, setNewDepartment] = useState('INTERNAL_MEDICINE');
  const [newCredentials, setNewCredentials] = useState('MD, FACP');
  const [newBio, setNewBio] = useState('');
  const [newSystemPrompt, setNewSystemPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    const handleMessage = (e: MessageEvent) => {
      if (!e.data || typeof e.data !== 'object') return;

      if (e.data.type === 'NAVIGATE' && e.data.tab) {
        onNavigateTab?.(e.data.tab);
      } else if (e.data.type === 'OPEN_CHAT') {
        setActiveDoctorContext({ key: e.data.agentKey, name: e.data.agentName });
        setIsDoctorChatOpen(true);
      } else if (e.data.type === 'OPEN_REGISTER') {
        setIsRegisterOpen(true);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onNavigateTab]);

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
        // Reload iframe if needed
        if (iframeRef.current) {
          iframeRef.current.src = '/staff-roster.html';
        }
      }
    } catch (err) {
      console.error('Failed to register healthcare professional:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full flex-1 flex flex-col h-full min-h-[920px] bg-[#F7F8FB] relative isolate overflow-hidden">
      <iframe
        ref={iframeRef}
        src="/staff-roster.html"
        title="Virtual Hospital Staff Roster"
        className="w-full flex-1 border-0"
        style={{
          width: '100%',
          minHeight: 'calc(100vh - 60px)',
          height: '100%',
          border: 'none',
          display: 'block',
          background: '#F7F8FB',
        }}
      />

      {/* Registration Dialog */}
      <Dialog
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        title="Register Healthcare Professional"
        description="Add a new clinician or specialist agent to the Virtual Hospital registry."
        actions={
          <>
            <Button variant="secondary" onClick={() => setIsRegisterOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleRegisterStaff}
              disabled={isSubmitting || !newName.trim()}
            >
              {isSubmitting ? 'Registering...' : 'Register Professional'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleRegisterStaff} className="space-y-4">
          <TextField
            label="Full Name & Post-nominals"
            placeholder="e.g. Dr. Jennifer Hayes, MD, MPH"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Professional Role"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as any)}
            >
              <option value="DOCTOR">Doctor / Physician</option>
              <option value="NURSE">Triage / Floor Nurse</option>
              <option value="RADIOLOGIST">Diagnostic Radiologist</option>
              <option value="LAB_SCIENTIST">Laboratory Scientist</option>
              <option value="RECEPTIONIST">Intake Receptionist</option>
            </Select>

            <Select
              label="Department"
              value={newDepartment}
              onChange={(e) => {
                setNewDepartment(e.target.value);
                setNewSpecialty(e.target.value);
              }}
            >
              <option value="INTERNAL_MEDICINE">Internal Medicine</option>
              <option value="CARDIOLOGY">Cardiology</option>
              <option value="NEUROLOGY">Neurology</option>
              <option value="SURGERY">General Surgery</option>
              <option value="EMERGENCY">Emergency Medicine</option>
              <option value="OBSTETRICS">Obstetrics</option>
              <option value="GYNECOLOGY">Gynecology</option>
              <option value="INTENSIVE_CARE">Intensive Care (ICU)</option>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <TextField
              label="Professional Title"
              placeholder="e.g. Attending Cardiologist"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
            />

            <TextField
              label="Credentials"
              placeholder="e.g. MD, FACC, FSCAI"
              value={newCredentials}
              onChange={(e) => setNewCredentials(e.target.value)}
            />
          </div>

          <TextArea
            label="Specialty Focus & Clinical Bio"
            placeholder="Clinical scope, diagnostic focuses, and guideline references..."
            value={newBio}
            onChange={(e) => setNewBio(e.target.value)}
            rows={2}
          />

          <TextArea
            label="Agent Clinical Guidance / System Prompt"
            placeholder="Directive instructions for AI reasoning and clinical tone..."
            value={newSystemPrompt}
            onChange={(e) => setNewSystemPrompt(e.target.value)}
            rows={2}
          />
        </form>
      </Dialog>

      {/* Doctor Chat Modal */}
      <DoctorChatModal
        isOpen={isDoctorChatOpen}
        onClose={() => setIsDoctorChatOpen(false)}
        agentKey={activeDoctorContext.key}
        specialty={
          activeDoctorContext.key === 'su'
            ? 'SURGERY'
            : activeDoctorContext.key === 'ca'
            ? 'CARDIOLOGY'
            : 'INTERNAL_MEDICINE'
        }
        doctorName={
          activeDoctorContext.key === 'su'
            ? 'Dr. Sarah Lin, MD, FACS'
            : activeDoctorContext.key === 'ca'
            ? 'Dr. Rachel Vance, MD, FACC'
            : 'Dr. Marcus Vance, MD, FACP'
        }
        patientContext={activeDoctorContext.name ? { attendingDoctor: activeDoctorContext.name } : undefined}
      />
    </div>
  );
};

export default StaffManagementSection;
