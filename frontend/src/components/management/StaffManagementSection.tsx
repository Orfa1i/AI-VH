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
    if (!newName.trim() || !newCredentials.trim()) {
      alert('Please fill out all required fields.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        name: newName.trim(),
        role: newRole,
        specialty: newSpecialty.trim(),
        title: newTitle.trim(),
        department: newDepartment,
        credentials: newCredentials.trim(),
        bio: newBio.trim() || 'Credentialed hospital staff professional.',
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
    <div className="flex-1 p-6 bg-[#f8fafc] overflow-y-auto max-w-7xl mx-auto w-full text-slate-900 telemetry-grid">
      {/* Top Banner & Header */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-5">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-600 animate-pulse" />
            <h2 className="text-xl font-black text-slate-900 tracking-tight font-sans">
              Hospital Personnel &amp; Clinical Staff Directory
            </h2>
            <span className="px-3 py-1 text-xs font-bold uppercase tracking-wider bg-sky-50 text-sky-700 border border-sky-200 rounded-full shadow-2xs font-mono">
              Attending Registry
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1.5 leading-relaxed font-sans">
            Credentialed medical staff directory, shift statuses, clinical reasoning models, and Harrison's RAG specialists.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => setIsRegisterOpen(true)}
            className="group relative inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-xs transition-all active:scale-[0.98] cursor-pointer"
          >
            <span className="w-5 h-5 rounded-md bg-white/20 flex items-center justify-center text-sm font-black">
              +
            </span>
            <span>Register Healthcare Professional</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {/* KPI 1: Credentialed Staff */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            <span>Credentialed Staff</span>
            <span className="text-slate-400 font-mono text-xs">👥</span>
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2 font-mono tracking-tight">{staffList.length}</div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
            <span>Active in hospital database</span>
          </div>
        </div>

        {/* KPI 2: On Duty Status */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-[11px] font-bold text-emerald-700 uppercase tracking-wider">
            <span>On Duty Status</span>
            <span className="text-emerald-600 font-mono text-xs">🩺</span>
          </div>
          <div className="text-2xl font-black text-emerald-700 mt-2 font-mono tracking-tight">{onDutyCount}</div>
          <div className="text-[10px] text-emerald-700 mt-1 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Ready for patient encounters</span>
          </div>
        </div>

        {/* KPI 3: Active Consultations */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-[11px] font-bold text-amber-700 uppercase tracking-wider">
            <span>Active Consultations</span>
            <span className="text-amber-600 font-mono text-xs">📋</span>
          </div>
          <div className="text-2xl font-black text-amber-700 mt-2 font-mono tracking-tight">{inConsultCount}</div>
          <div className="text-[10px] text-amber-700 mt-1 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span>In-progress clinical reviews</span>
          </div>
        </div>

        {/* KPI 4: Internal Medicine Core */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-[11px] font-bold text-sky-700 uppercase tracking-wider">
            <span>Internal Medicine</span>
            <span className="text-sky-600 font-mono text-xs">📖</span>
          </div>
          <div className="text-2xl font-black text-sky-700 mt-2 font-mono tracking-tight">Active</div>
          <div className="text-[10px] text-sky-700 mt-1 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-500 animate-pulse" />
            <span>Harrison's 21st Edition RAG</span>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="px-5 py-3.5 rounded-xl bg-white border border-slate-200 shadow-xs mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 text-xs text-slate-700 font-medium">
            <span className="text-slate-500 font-mono text-[11px]">Role Filter:</span>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="bg-slate-50 text-slate-800 text-xs font-semibold rounded-lg px-3 py-1.5 border border-slate-300 focus:outline-none focus:border-sky-500 transition cursor-pointer"
            >
              <option value="ALL">All Roles</option>
              <option value="DOCTOR">Physicians (MD)</option>
              <option value="NURSE">Nurses (RN)</option>
              <option value="LAB_SCIENTIST">Lab Scientists (MLS)</option>
              <option value="RADIOLOGIST">Radiologists (MD)</option>
              <option value="RECEPTIONIST">Admissions</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-700 font-medium">
            <span className="text-slate-500 font-mono text-[11px]">Department:</span>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="bg-slate-50 text-slate-800 text-xs font-semibold rounded-lg px-3 py-1.5 border border-slate-300 focus:outline-none focus:border-sky-500 transition cursor-pointer"
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

        <div className="text-xs font-mono text-slate-500 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-sky-600" />
          <span>Showing {filteredStaff.length} of {staffList.length} staff member{filteredStaff.length === 1 ? '' : 's'}</span>
        </div>
      </div>

      {/* Staff Roster Cards Display */}
      {loading ? (
        <div className="py-20 text-center text-slate-500 text-xs flex flex-col items-center justify-center gap-3">
          <span className="w-7 h-7 border-2 border-sky-400 border-t-sky-600 rounded-full animate-spin" />
          <span className="font-semibold tracking-wide">Loading hospital staff directory...</span>
        </div>
      ) : filteredStaff.length === 0 ? (
        <div className="py-16 text-center p-8 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="text-4xl mb-3">👨‍⚕️</div>
          <h4 className="text-base font-bold text-slate-900">No Staff Members Found</h4>
          <p className="text-xs text-slate-500 mt-1.5 max-w-sm mx-auto leading-relaxed">
            No matching staff records were found for the selected filters. Use the register button above to add personnel.
          </p>
        </div>
      ) : (
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
                className={`p-6 rounded-2xl border transition-all duration-300 shadow-xs bg-white ${
                  isVance
                    ? 'border-2 border-sky-300 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div>
                  {/* Top Section: Photo & Identity Header */}
                  <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-5 mb-5 relative z-10">
                    {photoSrc ? (
                      <div className="relative shrink-0 group/photo">
                        <div
                          className={`p-0.5 rounded-2xl transition-all duration-300 ${
                            isVance
                              ? 'bg-gradient-to-b from-sky-400 to-blue-600 shadow-xs ring-4 ring-sky-100'
                              : 'bg-slate-200 shadow-2xs'
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

                        {/* Status Dot */}
                        <span
                          className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white shadow-xs ${
                            isOnDuty
                              ? 'bg-emerald-500 animate-pulse'
                              : isInConsult
                              ? 'bg-amber-500'
                              : 'bg-slate-400'
                          }`}
                          title={`Status: ${staff.status}`}
                        />
                      </div>
                    ) : (
                      <div className="w-20 h-20 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center text-3xl shadow-2xs shrink-0">
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
                        <h3 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2 font-sans">
                          <span>{staff.name}</span>
                        </h3>
                        <span className="px-2.5 py-0.5 text-xs font-mono font-bold bg-sky-50 text-sky-800 border border-sky-200 rounded-md">
                          {staff.credentials}
                        </span>
                        {isVance && (
                          <span className="px-3 py-1 text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full flex items-center gap-1.5 shadow-2xs">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            Chief Attending Physician
                          </span>
                        )}
                      </div>

                      <div className="text-xs sm:text-sm font-semibold text-sky-800 mt-1 font-sans">
                        {staff.title}
                      </div>

                      {/* Department & Specialty Pills */}
                      <div className="flex flex-wrap items-center gap-2 mt-2.5">
                        <span className="px-2.5 py-1 text-[10px] font-semibold bg-slate-100 text-sky-800 border border-slate-200 rounded-lg">
                          🏥 {staff.department.replace(/_/g, ' ')}
                        </span>
                        <span className="px-2.5 py-1 text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200 rounded-lg">
                          🔬 {staff.specialty.replace(/_/g, ' ')}
                        </span>
                        <span className="px-2.5 py-1 text-[10px] font-mono text-purple-800 bg-purple-50 border border-purple-200 rounded-lg flex items-center gap-1 font-medium">
                          📖 Harrison's RAG Guided
                        </span>
                        <span className="px-2.5 py-1 text-[10px] font-mono text-slate-600 bg-slate-100 border border-slate-200 rounded-lg">
                          📊 {staff.total_encounters} Encounters
                        </span>
                      </div>
                    </div>

                    {/* Right Side: Direct Actions for Dr. Marcus Vance */}
                    {isVance && (
                      <div className="sm:self-start shrink-0 flex items-center gap-2 mt-3 sm:mt-0">
                        {onOpenConsult && (
                          <button
                            onClick={onOpenConsult}
                            className="group relative inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-700 font-bold text-xs border border-purple-200 shadow-2xs transition-all active:scale-[0.98] cursor-pointer"
                            title="Open Internal Medicine Consult Order"
                          >
                            <span>📋</span>
                            <span>Consult Order</span>
                          </button>
                        )}
                        <button
                          onClick={() => setIsDoctorChatOpen(true)}
                          className="group relative inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs sm:text-sm shadow-xs transition-all active:scale-[0.98] cursor-pointer"
                          title="Open direct clinical chat with Dr. Marcus Vance"
                        >
                          <span className="w-5 h-5 rounded-md bg-white/20 flex items-center justify-center text-xs">
                            💬
                          </span>
                          <span>Chat with Dr. Vance</span>
                          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-0.5" />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Clinical Biography */}
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-3 shadow-2xs">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1 font-mono">
                      Clinical Biography &amp; Background
                    </span>
                    <p className="text-xs text-slate-700 leading-relaxed font-sans">
                      {staff.bio}
                    </p>
                  </div>

                  {/* System Prompt / Clinical Directive */}
                  {staff.system_prompt && (
                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 mb-4">
                      <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-1">
                        Clinical AI Reasoning Directive
                      </span>
                      <p className="text-[11px] text-slate-600 font-mono line-clamp-2 italic">
                        "{staff.system_prompt}"
                      </p>
                    </div>
                  )}
                </div>

                {/* Bottom Card Actions: Shift Management & Controls */}
                <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-slate-500 font-mono">Duty Shift:</span>
                    <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200 text-xs">
                      <button
                        onClick={() => handleUpdateStatus(staff.id, 'ON_DUTY')}
                        className={`px-3 py-1 rounded-md text-[11px] font-bold transition cursor-pointer ${
                          isOnDuty
                            ? 'bg-emerald-600 text-white shadow-2xs'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        ON DUTY
                      </button>
                      <button
                        onClick={() => handleUpdateStatus(staff.id, 'IN_CONSULT')}
                        className={`px-3 py-1 rounded-md text-[11px] font-bold transition cursor-pointer ${
                          isInConsult
                            ? 'bg-amber-600 text-white shadow-2xs'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        IN CONSULT
                      </button>
                      <button
                        onClick={() => handleUpdateStatus(staff.id, 'OFF_DUTY')}
                        className={`px-3 py-1 rounded-md text-[11px] font-bold transition cursor-pointer ${
                          staff.status === 'OFF_DUTY'
                            ? 'bg-slate-600 text-white shadow-2xs'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        OFF DUTY
                      </button>
                    </div>
                  </div>

                  {!isVance && (
                    <button
                      onClick={() => handleDeleteStaff(staff.id, staff.name)}
                      className="text-xs text-rose-600 hover:text-rose-800 font-semibold px-2 py-1 rounded transition cursor-pointer hover:bg-rose-50"
                    >
                      Remove Staff
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Full Portrait Modal */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={() => setSelectedPhoto(null)}
        >
          <div
            className="bg-white rounded-3xl border border-slate-200 max-w-lg w-full shadow-2xl p-6 text-center relative overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedPhoto(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-700 text-sm w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center transition cursor-pointer"
            >
              ✕
            </button>

            <div className="relative inline-block mb-4 p-0.5 rounded-2xl bg-gradient-to-b from-sky-400 to-blue-600 shadow-md ring-4 ring-sky-100">
              <img
                src={selectedPhoto.src}
                alt={selectedPhoto.name}
                className="w-72 h-72 sm:w-80 sm:h-80 object-cover object-top rounded-[calc(1rem-2px)] mx-auto"
              />
            </div>

            <h3 className="text-xl font-black text-slate-900 tracking-tight font-sans">{selectedPhoto.name}</h3>
            <p className="text-xs text-sky-800 font-semibold mt-1 font-sans">{selectedPhoto.title}</p>
            <p className="text-[11px] text-slate-500 mt-2 font-mono">
              Chief of Internal Medicine • AI Virtual Hospital
            </p>
          </div>
        </div>
      )}

      {/* Modal: Register New Staff */}
      {isRegisterOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-xl w-full shadow-2xl p-6 relative">
            <button
              onClick={() => setIsRegisterOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-700 text-sm w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center transition cursor-pointer"
            >
              ✕
            </button>

            <h3 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2 font-sans">
              <span>➕</span>
              <span>Register Healthcare Professional</span>
            </h3>
            <p className="text-xs text-slate-500 mb-4 font-sans">
              Add a specialist, attending physician, or medical officer to the directory.
            </p>

            <form onSubmit={handleRegisterStaff} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-600 mb-1 font-medium font-sans">Full Name *</label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="e.g., Dr. Sophia Lin"
                    className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-lg px-3 py-2 focus:bg-white focus:outline-none focus:border-sky-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-slate-600 mb-1 font-medium font-sans">Credentials *</label>
                  <input
                    type="text"
                    value={newCredentials}
                    onChange={(e) => setNewCredentials(e.target.value)}
                    placeholder="MD, FACP / PharmD / BSN, RN"
                    className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-lg px-3 py-2 focus:bg-white focus:outline-none focus:border-sky-500"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-600 mb-1 font-medium font-sans">Role *</label>
                  <select
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value as any)}
                    className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-lg px-3 py-2 focus:bg-white focus:outline-none focus:border-sky-500 cursor-pointer"
                  >
                    <option value="DOCTOR">DOCTOR (Physician)</option>
                    <option value="NURSE">NURSE (Triage / Floor RN)</option>
                    <option value="LAB_SCIENTIST">LAB_SCIENTIST (Pathology)</option>
                    <option value="RADIOLOGIST">RADIOLOGIST (Imaging)</option>
                    <option value="RECEPTIONIST">RECEPTIONIST (Admissions)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-600 mb-1 font-medium font-sans">Department *</label>
                  <select
                    value={newDepartment}
                    onChange={(e) => setNewDepartment(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-lg px-3 py-2 focus:bg-white focus:outline-none focus:border-sky-500 cursor-pointer"
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
                <label className="block text-slate-600 mb-1 font-medium font-sans">Title *</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g., Attending Vascular Neurologist"
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-lg px-3 py-2 focus:bg-white focus:outline-none focus:border-sky-500"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-600 mb-1 font-medium font-sans">Specialty *</label>
                <input
                  type="text"
                  value={newSpecialty}
                  onChange={(e) => setNewSpecialty(e.target.value)}
                  placeholder="e.g., NEUROLOGY or CRITICAL_CARE"
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-lg px-3 py-2 focus:bg-white focus:outline-none focus:border-sky-500"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-600 mb-1 font-medium font-sans">Clinical Biography</label>
                <textarea
                  value={newBio}
                  onChange={(e) => setNewBio(e.target.value)}
                  placeholder="Subspecialty focus, clinical experience, academic affiliations..."
                  rows={2}
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-lg px-3 py-2 focus:bg-white focus:outline-none focus:border-sky-500 resize-none font-sans"
                />
              </div>

              <div>
                <label className="block text-slate-600 mb-1 font-medium font-sans">System Prompt / Reasoning Directive</label>
                <textarea
                  value={newSystemPrompt}
                  onChange={(e) => setNewSystemPrompt(e.target.value)}
                  placeholder="Clinical guidelines, contraindication vigilance, diagnostic protocol..."
                  rows={2}
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-xs rounded-lg px-3 py-2 focus:bg-white focus:outline-none focus:border-sky-500 resize-none font-mono"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsRegisterOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-lg shadow-xs transition disabled:opacity-50 cursor-pointer"
                >
                  {isSubmitting ? 'Registering...' : 'Register Professional'}
                </button>
              </div>
            </form>
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
