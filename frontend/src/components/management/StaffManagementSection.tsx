import React, { useState, useEffect } from 'react';
import type { HospitalStaffRecord } from '../../types';

export const StaffManagementSection: React.FC = () => {
  const [staffList, setStaffList] = useState<HospitalStaffRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [departmentFilter, setDepartmentFilter] = useState<string>('ALL');
  const [isRegisterOpen, setIsRegisterOpen] = useState<boolean>(false);

  // New staff form state
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState<'DOCTOR' | 'NURSE' | 'PHARMACIST' | 'RADIOLOGIST' | 'LAB_SCIENTIST' | 'RECEPTIONIST'>('DOCTOR');
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
    // Optimistic UI update
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
      fetchStaff(); // Revert on failure
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
      // Reset form
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
    <div className="flex-1 p-6 bg-slate-900/60 overflow-y-auto max-w-7xl mx-auto">
      {/* Top Banner & Header */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-slate-100">Hospital Personnel & Clinical Staff</span>
            <span className="px-2.5 py-0.5 text-xs font-semibold bg-blue-950 text-blue-400 border border-blue-800 rounded-full">
              Active Roster
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Manage multi-disciplinary clinical team: attending physicians, emergency triage nurses, clinical pharmacists, lab scientists, and radiologists.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsRegisterOpen(true)}
            className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-2"
          >
            <span>+</span> Register New Healthcare Professional
          </button>
        </div>
      </div>

      {/* Summary KPI Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-800/60 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Staff Roster</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">{staffList.length}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Credentialed personnel</div>
        </div>

        <div className="bg-slate-800/60 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">On Duty</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{onDutyCount}</div>
          <div className="text-[10px] text-emerald-500/80 mt-0.5">Available for encounters</div>
        </div>

        <div className="bg-slate-800/60 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider">In Active Consult</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">{inConsultCount}</div>
          <div className="text-[10px] text-amber-500/80 mt-0.5">Patient interaction</div>
        </div>

        <div className="bg-slate-800/60 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider">Clinical Disciplines</div>
          <div className="text-2xl font-bold text-cyan-400 mt-1">6</div>
          <div className="text-[10px] text-cyan-500/80 mt-0.5">IM, Triage, Pharm, Lab, Rad, Admin</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-800/40 border border-slate-800 p-3.5 rounded-xl mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Filter Role:</span>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="bg-slate-900 text-slate-200 text-xs rounded px-2.5 py-1.5 border border-slate-700 focus:outline-none"
            >
              <option value="ALL">All Roles</option>
              <option value="DOCTOR">Physicians (MD)</option>
              <option value="NURSE">Nurses (RN)</option>
              <option value="PHARMACIST">Pharmacists (PharmD)</option>
              <option value="LAB_SCIENTIST">Lab Scientists (MLS)</option>
              <option value="RADIOLOGIST">Radiologists (MD)</option>
              <option value="RECEPTIONIST">Admissions Coordinators</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Department:</span>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="bg-slate-900 text-slate-200 text-xs rounded px-2.5 py-1.5 border border-slate-700 focus:outline-none"
            >
              <option value="ALL">All Departments</option>
              <option value="INTERNAL_MEDICINE">Internal Medicine</option>
              <option value="EMERGENCY">Emergency</option>
              <option value="PHARMACY">Pharmacy</option>
              <option value="LABORATORY">Laboratory</option>
              <option value="RADIOLOGY">Radiology</option>
              <option value="RECEPTION">Reception</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-slate-500">
          Showing {filteredStaff.length} of {staffList.length} staff
        </div>
      </div>

      {/* Staff Roster Cards Grid */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-2">
          <span className="w-5 h-5 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <span>Loading hospital staff roster...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredStaff.map((staff) => {
            const isOnDuty = staff.status === 'ON_DUTY';
            const isInConsult = staff.status === 'IN_CONSULT';

            return (
              <div
                key={staff.id}
                className="bg-slate-800/50 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition shadow-sm flex flex-col justify-between"
              >
                <div>
                  {/* Top: Avatar/Badge + Name & Title */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-700 to-slate-800 border border-slate-600 flex items-center justify-center text-lg shadow-inner">
                        {staff.role === 'DOCTOR' && '👨‍⚕️'}
                        {staff.role === 'NURSE' && '👩‍⚕️'}
                        {staff.role === 'PHARMACIST' && '💊'}
                        {staff.role === 'LAB_SCIENTIST' && '🔬'}
                        {staff.role === 'RADIOLOGIST' && '🩻'}
                        {staff.role === 'RECEPTIONIST' && '📋'}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                          <span>{staff.name}</span>
                          <span className="text-xs font-semibold text-cyan-400">{staff.credentials}</span>
                        </h4>
                        <div className="text-xs text-slate-400 line-clamp-1">{staff.title}</div>
                      </div>
                    </div>
                  </div>

                  {/* Department & Specialty Pills */}
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <span className="px-2 py-0.5 text-[10px] font-semibold bg-slate-900 text-cyan-300 border border-slate-700 rounded">
                      {staff.department.replace(/_/g, ' ')}
                    </span>
                    <span className="px-2 py-0.5 text-[10px] font-medium bg-slate-900 text-slate-400 border border-slate-800 rounded">
                      {staff.specialty.replace(/_/g, ' ')}
                    </span>
                    <span className="px-2 py-0.5 text-[10px] font-mono bg-slate-900 text-slate-400 border border-slate-800 rounded">
                      {staff.total_encounters} Encounters
                    </span>
                  </div>

                  {/* Bio */}
                  <p className="text-xs text-slate-300 bg-slate-900/60 p-3 rounded-lg border border-slate-800/80 mb-3 leading-relaxed">
                    {staff.bio}
                  </p>

                  {/* System Prompt / Guideline Persona */}
                  {staff.system_prompt && (
                    <div className="text-[11px] text-slate-400/90 font-mono bg-slate-950/40 p-2 rounded border border-slate-900">
                      <span className="text-cyan-400 font-semibold block text-[10px] uppercase">Clinical Prompt / Standard:</span>
                      {staff.system_prompt}
                    </div>
                  )}
                </div>

                {/* Duty Status Selector */}
                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 font-medium">Duty Status:</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleUpdateStatus(staff.id, 'ON_DUTY')}
                      className={`px-2 py-1 text-[10px] font-bold rounded transition border ${
                        isOnDuty
                          ? 'bg-emerald-950 text-emerald-400 border-emerald-700 shadow-sm'
                          : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
                      }`}
                    >
                      ON DUTY
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(staff.id, 'IN_CONSULT')}
                      className={`px-2 py-1 text-[10px] font-bold rounded transition border ${
                        isInConsult
                          ? 'bg-amber-950 text-amber-400 border-amber-700 shadow-sm'
                          : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
                      }`}
                    >
                      CONSULT
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(staff.id, 'OFF_DUTY')}
                      className={`px-2 py-1 text-[10px] font-bold rounded transition border ${
                        staff.status === 'OFF_DUTY'
                          ? 'bg-slate-800 text-slate-300 border-slate-600 shadow-sm'
                          : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
                      }`}
                    >
                      OFF DUTY
                    </button>
                    {staff.id !== 'STAFF-VANCE' && (
                      <button
                        onClick={() => handleDeleteStaff(staff.id, staff.name)}
                        className="p-1 text-slate-500 hover:text-rose-400 text-xs transition ml-1"
                        title="Delete staff member from directory"
                      >
                        🗑️
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal: Register New Staff */}
      {isRegisterOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setIsRegisterOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 text-lg p-1"
            >
              ✕
            </button>

            <h3 className="text-lg font-bold text-slate-100 mb-1">Register New Healthcare Professional</h3>
            <p className="text-xs text-slate-400 mb-4">
              Add an attending physician, triage nurse, clinical pharmacist, or pathologist to the AI-VH directory.
            </p>

            <form onSubmit={handleRegisterStaff} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Full Name *</label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="e.g., Dr. Miriam O'Connor"
                    className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
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
                    className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
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
                    className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="DOCTOR">DOCTOR (Physician)</option>
                    <option value="NURSE">NURSE (Triage / Floor RN)</option>
                    <option value="PHARMACIST">PHARMACIST (PharmD)</option>
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
                    className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="INTERNAL_MEDICINE">Internal Medicine</option>
                    <option value="EMERGENCY">Emergency Department</option>
                    <option value="PHARMACY">Pharmacy</option>
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
                  className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
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
                  className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
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
                  className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500 resize-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">System Prompt / Reasoning Directive</label>
                <textarea
                  value={newSystemPrompt}
                  onChange={(e) => setNewSystemPrompt(e.target.value)}
                  placeholder="Clinical guidelines, contraindication vigilance, diagnostic protocol..."
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsRegisterOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs rounded-lg shadow transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Registering...' : 'Register Professional'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default StaffManagementSection;
