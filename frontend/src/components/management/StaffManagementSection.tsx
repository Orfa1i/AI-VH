import React, { useState, useEffect } from 'react';
import type { HospitalStaffRecord } from '../../types';
import drMarcusPhoto from '../../assets/dr_marcus_vance.jpg';
import { DoctorChatModal } from '../specialists/DoctorChatModal';

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
        throw new Error('Failed to update status');
      }
    } catch (err) {
      console.error('Error updating staff status:', err);
      fetchStaff();
    }
  };

  const handleDeleteStaff = async (staffId: string, name: string) => {
    if (!confirm(`Are you sure you want to remove ${name} from the hospital staff directory?`)) return;
    try {
      const res = await fetch(`/api/staff/${staffId}`, { method: 'DELETE' });
      if (res.ok) {
        setStaffList((prev) => prev.filter((s) => s.id !== staffId));
      } else {
        alert('Failed to delete staff member.');
      }
    } catch (err) {
      console.error('Error deleting staff member:', err);
    }
  };

  const handleRegisterStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newTitle.trim()) {
      alert('Please provide name and title.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        name: newName.trim(),
        role: newRole,
        specialty: newSpecialty,
        title: newTitle.trim(),
        department: newDepartment,
        credentials: newCredentials.trim(),
        bio: newBio.trim() || `${newTitle} at AI-VH.`,
        system_prompt: newSystemPrompt.trim() || undefined,
        status: 'ON_DUTY',
      };

      const res = await fetch('/api/staff', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error('Failed to register staff member');
      }

      setIsRegisterOpen(false);
      setNewName('');
      setNewBio('');
      setNewSystemPrompt('');
      fetchStaff();
    } catch (err: any) {
      alert(err.message || 'Error creating staff');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredStaff = staffList.filter((s) => {
    const matchesRole = roleFilter === 'ALL' || s.role === roleFilter;
    const matchesDept = departmentFilter === 'ALL' || s.department === departmentFilter;
    return matchesRole && matchesDept;
  });

  const onDutyCount = staffList.filter((s) => s.status === 'ON_DUTY').length;
  const inConsultCount = staffList.filter((s) => s.status === 'IN_CONSULT').length;

  return (
    <div className="flex-1 p-6 bg-slate-900/60 overflow-y-auto max-w-7xl mx-auto w-full">
      {/* Top Banner & Header with Double-Bezel Concentric Frame */}
      <div className="relative rounded-2xl p-0.5 bg-gradient-to-r from-cyan-500/30 via-slate-800/50 to-teal-500/30 border border-slate-700/60 shadow-xl mb-6">
        <div className="p-6 rounded-[calc(1rem-2px)] bg-slate-950/95 backdrop-blur-md flex flex-col md:flex-row md:items-center md:justify-between gap-5">
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
              <h2 className="text-2xl font-black text-slate-100 tracking-tight">
                Hospital Personnel & Clinical Staff Directory
              </h2>
              <span className="px-3 py-1 text-xs font-bold uppercase tracking-wider bg-cyan-950/90 text-cyan-300 border border-cyan-700/80 rounded-full shadow-sm">
                Attending Registry
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Credentialed medical staff directory, shift statuses, clinical reasoning models, and Harrison's RAG specialists.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {/* Button-in-Button Registration CTA */}
            <button
              onClick={() => setIsRegisterOpen(true)}
              className="group relative inline-flex items-center gap-3 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 via-teal-600 to-cyan-600 hover:from-cyan-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-cyan-950/80 border border-cyan-400/50 transition-all duration-300 active:scale-[0.98] cursor-pointer"
            >
              <span className="w-5 h-5 rounded-lg bg-white/20 flex items-center justify-center text-sm font-black transition-transform duration-300 group-hover:scale-110">
                +
              </span>
              <span>Register Healthcare Professional</span>
            </button>
          </div>
        </div>
      </div>

      {/* Summary KPI Counters in Concentric Double-Bezel Grids */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {/* KPI 1: Credentialed Staff */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-slate-700/40 via-slate-800/40 to-slate-900/60 border border-slate-700/50 shadow-lg">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              <span>Credentialed Staff</span>
              <span className="text-slate-500 font-mono text-xs">👥</span>
            </div>
            <div className="text-2xl font-black text-slate-100 mt-2 font-mono tracking-tight">{staffList.length}</div>
            <div className="text-[10px] text-slate-400 mt-1 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
              <span>Active in hospital database</span>
            </div>
          </div>
        </div>

        {/* KPI 2: On Duty Status */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-emerald-500/30 via-slate-800/40 to-slate-900/60 border border-emerald-500/30 shadow-lg">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="flex items-center justify-between text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
              <span>On Duty Status</span>
              <span className="text-emerald-400 font-mono text-xs">🩺</span>
            </div>
            <div className="text-2xl font-black text-emerald-300 mt-2 font-mono tracking-tight">{onDutyCount}</div>
            <div className="text-[10px] text-emerald-400/90 mt-1 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Ready for patient encounters</span>
            </div>
          </div>
        </div>

        {/* KPI 3: Active Consultations */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-amber-500/30 via-slate-800/40 to-slate-900/60 border border-amber-500/30 shadow-lg">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="flex items-center justify-between text-[11px] font-bold text-amber-400 uppercase tracking-wider">
              <span>Active Consultations</span>
              <span className="text-amber-400 font-mono text-xs">📋</span>
            </div>
            <div className="text-2xl font-black text-amber-300 mt-2 font-mono tracking-tight">{inConsultCount}</div>
            <div className="text-[10px] text-amber-400/90 mt-1 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              <span>In-progress clinical reviews</span>
            </div>
          </div>
        </div>

        {/* KPI 4: Internal Medicine Core */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-cyan-500/30 via-purple-500/20 to-slate-900/60 border border-cyan-500/30 shadow-lg">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="flex items-center justify-between text-[11px] font-bold text-cyan-400 uppercase tracking-wider">
              <span>Internal Medicine</span>
              <span className="text-purple-400 font-mono text-xs">📖</span>
            </div>
            <div className="text-2xl font-black text-cyan-300 mt-2 font-mono tracking-tight">Active</div>
            <div className="text-[10px] text-purple-300/90 mt-1 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
              <span>Harrison's 21st Edition RAG</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Bar with Double-Bezel Glass Framing */}
      <div className="relative rounded-2xl p-0.5 bg-gradient-to-r from-slate-700/40 via-slate-800/40 to-slate-700/40 border border-slate-700/60 shadow-md mb-6">
        <div className="px-5 py-3.5 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 text-xs text-slate-300 font-medium">
              <span className="text-slate-400">Role Filter:</span>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="bg-slate-900 text-slate-200 text-xs font-semibold rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-cyan-500 transition shadow-inner cursor-pointer"
              >
                <option value="ALL">All Roles</option>
                <option value="DOCTOR">Physicians (MD)</option>
                <option value="NURSE">Nurses (RN)</option>
                <option value="LAB_SCIENTIST">Lab Scientists (MLS)</option>
                <option value="RADIOLOGIST">Radiologists (MD)</option>
                <option value="RECEPTIONIST">Admissions</option>
              </select>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-300 font-medium">
              <span className="text-slate-400">Department:</span>
              <select
                value={departmentFilter}
                onChange={(e) => setDepartmentFilter(e.target.value)}
                className="bg-slate-900 text-slate-200 text-xs font-semibold rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-cyan-500 transition shadow-inner cursor-pointer"
              >
                <option value="ALL">All Departments</option>
                <option value="INTERNAL_MEDICINE">Internal Medicine</option>
                <option value="EMERGENCY">Emergency</option>
                <option value="LABORATORY">Laboratory</option>
                <option value="RADIOLOGY">Radiology</option>
                <option value="RECEPTION">Reception</option>
              </select>
            </div>
          </div>

          <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>Showing {filteredStaff.length} of {staffList.length} staff member{filteredStaff.length === 1 ? '' : 's'}</span>
          </div>
        </div>
      </div>

      {/* Staff Roster Cards Display */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-3">
          <span className="w-7 h-7 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin" />
          <span className="font-semibold tracking-wide">Loading hospital staff directory...</span>
        </div>
      ) : filteredStaff.length === 0 ? (
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-slate-700/40 via-slate-800/40 to-slate-900/60 border border-slate-800 shadow-xl">
          <div className="py-16 text-center p-8 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="text-4xl mb-3">👨‍⚕️</div>
            <h4 className="text-base font-bold text-slate-200">No Staff Members Found</h4>
            <p className="text-xs text-slate-400 mt-1.5 max-w-sm mx-auto leading-relaxed">
              No matching staff records were found for the selected filters. Use the register button above to add personnel.
            </p>
          </div>
        </div>
      ) : (
        /* Render Grid / Executive Featured Card */
        <div
          className={
            filteredStaff.length === 1
              ? 'max-w-4xl mx-auto w-full'
              : 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
          }
        >
          {filteredStaff.map((staff) => {
            const isVance = staff.id === 'STAFF-VANCE' || staff.name.includes('Marcus Vance');
            const isOnDuty = staff.status === 'ON_DUTY';
            const isInConsult = staff.status === 'IN_CONSULT';
            const photoSrc = isVance ? (staff.avatar_url || drMarcusPhoto) : staff.avatar_url;

            return (
              <div
                key={staff.id}
                className={`relative rounded-3xl p-0.5 transition-all duration-300 shadow-xl group ${
                  isVance
                    ? 'bg-gradient-to-b from-cyan-400/50 via-teal-500/30 to-slate-900/80 border border-cyan-400/40 shadow-cyan-950/60'
                    : 'bg-gradient-to-b from-slate-700/40 via-slate-800/40 to-slate-900/60 border border-slate-800 hover:border-slate-700'
                }`}
              >
                <div
                  className={`p-6 rounded-[calc(1.5rem-2px)] backdrop-blur-md flex flex-col justify-between h-full relative overflow-hidden ${
                    isVance ? 'bg-slate-950/95' : 'bg-slate-950/90'
                  }`}
                >
                  {/* Subtle decorative glow for Attending Physician */}
                  {isVance && (
                    <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none -mr-24 -mt-24" />
                  )}

                  <div>
                    {/* Top Section: Photo & Identity Header */}
                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-5 mb-5 relative z-10">
                      {/* Portrait Photo Container with Double-Bezel Framing */}
                      {photoSrc ? (
                        <div className="relative shrink-0 group/photo">
                          <div
                            className={`p-0.5 rounded-2xl transition-all duration-300 ${
                              isVance
                                ? 'bg-gradient-to-b from-cyan-400 via-teal-400 to-cyan-600 shadow-lg shadow-cyan-950/80 ring-4 ring-cyan-500/20'
                                : 'bg-gradient-to-b from-slate-600 to-slate-700 shadow-md'
                            }`}
                          >
                            <img
                              src={photoSrc}
                              alt={staff.name}
                              onClick={() =>
                                setSelectedPhoto({
                                  src: photoSrc,
                                  name: staff.name,
                                  title: staff.title,
                                })
                              }
                              className={`rounded-[calc(1rem-2px)] object-cover object-top cursor-pointer transition-transform duration-300 group-hover/photo:scale-[1.03] ${
                                isVance
                                  ? 'w-28 h-28 sm:w-32 sm:h-32'
                                  : 'w-20 h-20 sm:w-24 sm:h-24'
                              }`}
                              title="Click to view full portrait"
                            />
                          </div>

                          {/* Status Dot with Double Border */}
                          <span
                            className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-slate-950 shadow-md ${
                              isOnDuty
                                ? 'bg-emerald-400 animate-pulse'
                                : isInConsult
                                ? 'bg-amber-400'
                                : 'bg-slate-500'
                            }`}
                            title={`Status: ${staff.status}`}
                          />
                          {/* Hover Zoom Hint */}
                          <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover/photo:opacity-100 rounded-2xl flex items-center justify-center text-xs font-semibold text-white transition-opacity pointer-events-none">
                            🔍 Zoom
                          </div>
                        </div>
                      ) : (
                        /* Fallback Role Icon with Double-Bezel Style */
                        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 flex items-center justify-center text-3xl shadow-inner shrink-0">
                          {staff.role === 'DOCTOR' && '👨‍⚕️'}
                          {staff.role === 'NURSE' && '👩‍⚕️'}
                          {staff.role === 'LAB_SCIENTIST' && '🔬'}
                          {staff.role === 'RADIOLOGIST' && '🩻'}
                          {staff.role === 'RECEPTIONIST' && '📋'}
                        </div>
                      )}

                      {/* Name, Title, and Medical Badges */}
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-xl sm:text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2">
                            <span>{staff.name}</span>
                          </h3>
                          <span className="px-2.5 py-0.5 text-xs font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-700/80 rounded-md">
                            {staff.credentials}
                          </span>
                          {isVance && (
                            <span className="px-3 py-1 text-[11px] font-bold bg-emerald-950/90 text-emerald-300 border border-emerald-700/80 rounded-full flex items-center gap-1.5 shadow-sm">
                              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                              Chief Attending Physician
                            </span>
                          )}
                        </div>

                        <div className="text-xs sm:text-sm font-semibold text-cyan-300/90 mt-1">
                          {staff.title}
                        </div>

                        {/* Department & Specialty Pills */}
                        <div className="flex flex-wrap items-center gap-2 mt-2.5">
                          <span className="px-2.5 py-1 text-[10px] font-semibold bg-slate-900/90 text-cyan-400 border border-cyan-800/70 rounded-lg">
                            🏥 {staff.department.replace(/_/g, ' ')}
                          </span>
                          <span className="px-2.5 py-1 text-[10px] font-medium bg-slate-900/90 text-slate-300 border border-slate-700 rounded-lg">
                            🔬 {staff.specialty.replace(/_/g, ' ')}
                          </span>
                          <span className="px-2.5 py-1 text-[10px] font-mono text-purple-300 bg-purple-950/60 border border-purple-800/60 rounded-lg flex items-center gap-1">
                            📖 Harrison's RAG Guided
                          </span>
                          <span className="px-2.5 py-1 text-[10px] font-mono text-slate-300 bg-slate-900/90 border border-slate-700 rounded-lg">
                            📊 {staff.total_encounters} Encounters
                          </span>
                        </div>
                      </div>

                      {/* Right Side: Direct Chat Button for Dr. Marcus Vance */}
                      {isVance && (
                        <div className="sm:self-start shrink-0 flex items-center gap-2 mt-3 sm:mt-0">
                          {/* Button-in-Button Attending Chat Trigger */}
                          <button
                            onClick={() => setIsDoctorChatOpen(true)}
                            className="group relative inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 via-teal-600 to-cyan-600 hover:from-cyan-500 hover:to-teal-500 text-white font-bold text-xs sm:text-sm shadow-lg shadow-cyan-950/80 border border-cyan-400/60 transition-all duration-300 active:scale-[0.98] cursor-pointer"
                            title="Open direct clinical chat with Dr. Marcus Vance"
                          >
                            <span className="w-5 h-5 rounded-md bg-white/20 flex items-center justify-center text-xs transition-transform duration-300 group-hover:scale-110">
                              💬
                            </span>
                            <span>Chat with Dr. Vance</span>
                            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-0.5" />
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Clinical Biography */}
                    <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/90 mb-3 shadow-inner">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                        Clinical Biography & Background
                      </span>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {staff.bio}
                      </p>
                    </div>

                    {/* System Prompt & Diagnostic Protocol */}
                    {staff.system_prompt && (
                      <div className="text-[11px] text-slate-300 font-mono bg-slate-950/90 p-3.5 rounded-xl border border-slate-800/90 mb-4 shadow-inner">
                        <span className="text-cyan-400 font-bold block text-[10px] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                          <span>⚡</span>
                          <span>Clinical Reasoning Protocol & Guideline Directive</span>
                        </span>
                        <p className="text-slate-300 leading-relaxed">
                          {staff.system_prompt}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Footer Controls & Duty Switcher */}
                  <div className="mt-3 pt-4 border-t border-slate-800/90 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-400 font-medium">Shift Status:</span>
                      <div className="flex items-center gap-1 bg-slate-950/90 p-1 rounded-xl border border-slate-800">
                        <button
                          onClick={() => handleUpdateStatus(staff.id, 'ON_DUTY')}
                          className={`px-3 py-1 text-[10px] font-bold rounded-lg transition border cursor-pointer ${
                            isOnDuty
                              ? 'bg-emerald-950 text-emerald-300 border-emerald-600 shadow-md shadow-emerald-950/80'
                              : 'bg-transparent text-slate-500 border-transparent hover:text-slate-300'
                          }`}
                        >
                          ● ON DUTY
                        </button>
                        <button
                          onClick={() => handleUpdateStatus(staff.id, 'IN_CONSULT')}
                          className={`px-3 py-1 text-[10px] font-bold rounded-lg transition border cursor-pointer ${
                            isInConsult
                              ? 'bg-amber-950 text-amber-300 border-amber-600 shadow-md shadow-amber-950/80'
                              : 'bg-transparent text-slate-500 border-transparent hover:text-slate-300'
                          }`}
                        >
                          ● IN CONSULT
                        </button>
                        <button
                          onClick={() => handleUpdateStatus(staff.id, 'OFF_DUTY')}
                          className={`px-3 py-1 text-[10px] font-bold rounded-lg transition border cursor-pointer ${
                            staff.status === 'OFF_DUTY'
                              ? 'bg-slate-800 text-slate-300 border-slate-600 shadow-md'
                              : 'bg-transparent text-slate-500 border-transparent hover:text-slate-300'
                          }`}
                        >
                          ● OFF DUTY
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Direct Chat Shortcut */}
                      {isVance && (
                        <button
                          onClick={() => setIsDoctorChatOpen(true)}
                          className="group px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 text-white text-xs font-bold shadow-md shadow-cyan-950/70 border border-cyan-400/60 transition flex items-center gap-1.5 cursor-pointer active:scale-[0.98]"
                        >
                          <span className="transition-transform group-hover:scale-110">💬</span>
                          <span>Direct Chat</span>
                        </button>
                      )}

                      {/* Launch Consult shortcut with Button-in-Button Styling */}
                      {onOpenConsult && (
                        <button
                          onClick={onOpenConsult}
                          className="group px-3.5 py-1.5 rounded-xl bg-cyan-950 hover:bg-cyan-900 border border-cyan-700/80 text-cyan-300 text-xs font-bold shadow transition flex items-center gap-1.5 cursor-pointer active:scale-[0.98]"
                        >
                          <span className="transition-transform group-hover:scale-110">🩺</span>
                          <span>Consult Dr. Vance</span>
                        </button>
                      )}

                      {/* Delete button (only for non-Vance staff) */}
                      {!isVance && (
                        <button
                          onClick={() => handleDeleteStaff(staff.id, staff.name)}
                          className="p-1.5 text-slate-400 hover:text-rose-400 text-xs rounded-lg border border-slate-700 hover:border-rose-700 transition cursor-pointer"
                          title="Remove staff member from directory"
                        >
                          🗑️ Remove
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Lightbox Modal for High-Resolution Photo Zoom with Double-Bezel Framing */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={() => setSelectedPhoto(null)}
        >
          <div
            className="relative rounded-3xl p-0.5 bg-gradient-to-b from-cyan-500/40 via-slate-800 to-cyan-500/40 border border-cyan-500/30 max-w-lg w-full shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-slate-950 rounded-[calc(1.5rem-2px)] p-6 text-center relative overflow-hidden">
              <button
                onClick={() => setSelectedPhoto(null)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 text-sm w-8 h-8 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center transition cursor-pointer"
              >
                ✕
              </button>

              <div className="relative inline-block mb-4 p-0.5 rounded-2xl bg-gradient-to-b from-cyan-400 to-teal-500 shadow-2xl shadow-cyan-950 ring-4 ring-cyan-500/20">
                <img
                  src={selectedPhoto.src}
                  alt={selectedPhoto.name}
                  className="w-72 h-72 sm:w-80 sm:h-80 object-cover object-top rounded-[calc(1rem-2px)] mx-auto"
                />
              </div>

              <h3 className="text-xl font-black text-slate-100 tracking-tight">{selectedPhoto.name}</h3>
              <p className="text-xs text-cyan-300 font-semibold mt-1">{selectedPhoto.title}</p>
              <p className="text-[11px] text-slate-400 mt-2 font-mono">
                Chief of Internal Medicine • AI Virtual Hospital
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Register New Staff with Double-Bezel Architecture */}
      {isRegisterOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative rounded-3xl p-0.5 bg-gradient-to-b from-cyan-500/40 via-slate-800 to-slate-900 border border-cyan-500/30 max-w-xl w-full shadow-2xl">
            <div className="bg-slate-950 rounded-[calc(1.5rem-2px)] p-6 relative">
              <button
                onClick={() => setIsRegisterOpen(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 text-sm w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center transition cursor-pointer"
              >
                ✕
              </button>

              <h3 className="text-lg font-bold text-slate-100 mb-1 flex items-center gap-2">
                <span>➕</span>
                <span>Register Healthcare Professional</span>
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Add a specialist, attending physician, or medical officer to the directory.
              </p>

              <form onSubmit={handleRegisterStaff} className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 mb-1 font-medium">Full Name *</label>
                    <input
                      type="text"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      placeholder="e.g., Dr. Sophia Lin"
                      className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1 font-medium">Credentials *</label>
                    <input
                      type="text"
                      value={newCredentials}
                      onChange={(e) => setNewCredentials(e.target.value)}
                      placeholder="MD, FACP / PharmD / BSN, RN"
                      className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 mb-1 font-medium">Role *</label>
                    <select
                      value={newRole}
                      onChange={(e) => setNewRole(e.target.value as any)}
                      className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="DOCTOR">DOCTOR (Physician)</option>
                      <option value="NURSE">NURSE (Triage / Floor RN)</option>
                      <option value="LAB_SCIENTIST">LAB_SCIENTIST (Pathology)</option>
                      <option value="RADIOLOGIST">RADIOLOGIST (Imaging)</option>
                      <option value="RECEPTIONIST">RECEPTIONIST (Admissions)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1 font-medium">Department *</label>
                    <select
                      value={newDepartment}
                      onChange={(e) => setNewDepartment(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="INTERNAL_MEDICINE">Internal Medicine</option>
                      <option value="EMERGENCY">Emergency Department</option>
                      <option value="LABORATORY">Laboratory</option>
                      <option value="RADIOLOGY">Radiology</option>
                      <option value="CARDIOLOGY">Cardiology</option>
                      <option value="ICU">Intensive Care (ICU)</option>
                      <option value="RECEPTION">Admissions / Reception</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Title *</label>
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g., Attending Vascular Neurologist"
                    className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Specialty *</label>
                  <input
                    type="text"
                    value={newSpecialty}
                    onChange={(e) => setNewSpecialty(e.target.value)}
                    placeholder="e.g., NEUROLOGY or CRITICAL_CARE"
                    className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Clinical Biography</label>
                  <textarea
                    value={newBio}
                    onChange={(e) => setNewBio(e.target.value)}
                    placeholder="Subspecialty focus, clinical experience, academic affiliations..."
                    rows={2}
                    className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500 resize-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-medium">System Prompt / Reasoning Directive</label>
                  <textarea
                    value={newSystemPrompt}
                    onChange={(e) => setNewSystemPrompt(e.target.value)}
                    placeholder="Clinical guidelines, contraindication vigilance, diagnostic protocol..."
                    rows={2}
                    className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500 resize-none"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsRegisterOpen(false)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-5 py-2 bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 text-white font-bold text-xs rounded-lg shadow-lg shadow-cyan-950/70 border border-cyan-400/50 transition disabled:opacity-50 cursor-pointer"
                  >
                    {isSubmitting ? 'Registering...' : 'Register Professional'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Direct Clinical Chat with Dr. Marcus Vance */}
      <DoctorChatModal
        isOpen={isDoctorChatOpen}
        onClose={() => setIsDoctorChatOpen(false)}
      />
    </div>
  );
};

export default StaffManagementSection;
