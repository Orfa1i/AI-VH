import React, { useState, useEffect } from 'react';
import type { PatientRecord } from '../../types';

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

  return (
    <div className="flex-1 p-6 bg-slate-900/60 overflow-y-auto max-w-7xl mx-auto">
      {/* Top Banner & Analytics Cards */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-slate-100">Patient Directory & Bed Board</span>
            <span className="px-2.5 py-0.5 text-xs font-semibold bg-cyan-950 text-cyan-400 border border-cyan-800 rounded-full">
              PostgreSQL / SQLite EHR Store
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Centralized electronic health records (EHR), bed allocation tracking, and clinical life-cycle management.
          </p>
        </div>

        <button
          onClick={fetchPatients}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 flex items-center gap-1.5 transition self-start"
        >
          <span>↻</span> Refresh Records
        </button>
      </div>

      {/* KPI Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-800/60 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Patients</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">{totalCount}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Recorded in database</div>
        </div>

        <div className="bg-slate-800/60 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Active Inpatients</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{admittedCount}</div>
          <div className="text-[10px] text-emerald-500/80 mt-0.5">Occupying hospital beds</div>
        </div>

        <div className="bg-slate-800/60 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider">High Acuity (Level 1-2)</div>
          <div className="text-2xl font-bold text-rose-400 mt-1">{criticalCount}</div>
          <div className="text-[10px] text-rose-500/80 mt-0.5">Immediate / Critical care</div>
        </div>

        <div className="bg-slate-800/60 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Discharged</div>
          <div className="text-2xl font-bold text-slate-300 mt-1">{dischargedCount}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Resolved encounters</div>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="bg-slate-800/40 border border-slate-800 p-3.5 rounded-xl mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <span className="text-slate-400 text-sm">🔍</span>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by patient name, MRN, or complaint..."
            className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 text-slate-200 text-xs rounded px-2.5 py-1.5 border border-slate-700 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="ADMITTED">Admitted Only</option>
              <option value="DISCHARGED">Discharged Only</option>
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
              <option value="EMERGENCY">Emergency</option>
              <option value="INTERNAL_MEDICINE">Internal Medicine</option>
              <option value="CARDIOLOGY">Cardiology</option>
              <option value="ICU">ICU</option>
              <option value="STEP_DOWN">Step-Down</option>
            </select>
          </div>
        </div>
      </div>

      {/* Patient Bed Board Grid */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-2">
          <span className="w-5 h-5 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
          <span>Loading patient registry from database...</span>
        </div>
      ) : filteredPatients.length === 0 ? (
        <div className="py-16 text-center bg-slate-800/20 border border-slate-800 rounded-2xl p-8">
          <div className="text-3xl mb-2">🏥</div>
          <h4 className="text-sm font-semibold text-slate-300">No Patients Found</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            No matching patient records were found in the database. Use the "Case Intake & Admission" tab to admit a patient.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPatients.map((p) => {
            const isAdmitted = p.admission_status === 'ADMITTED';
            const vitals = p.baseline_vitals || {};

            return (
              <div
                key={p.id}
                className="bg-slate-800/50 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 rounded-xl p-4 transition shadow-sm flex flex-col justify-between cursor-pointer group"
                onClick={() => setSelectedPatient(p)}
              >
                <div>
                  {/* Top Bar: Name, Sex, Age & Status */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h4 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition flex items-center gap-2">
                        <span>{p.name}</span>
                        <span className="text-xs font-normal text-slate-400">
                          ({p.age}y, {p.sex})
                        </span>
                      </h4>
                      <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                        {p.mrn} • <span className="text-slate-500">{p.id}</span>
                      </div>
                    </div>

                    <span
                      className={`px-2 py-0.5 text-[10px] font-semibold rounded-full border ${
                        isAdmitted
                          ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}
                    >
                      {p.admission_status}
                    </span>
                  </div>

                  {/* Bed & Acuity Badges */}
                  <div className="flex flex-wrap items-center gap-2 my-2.5">
                    <span className="px-2 py-0.5 text-[10px] font-mono bg-slate-900 text-cyan-300 border border-slate-700 rounded">
                      {p.assigned_department} • Bed {p.bed_number || 'TBD'}
                    </span>

                    <span
                      className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                        p.triage_acuity === 'RESUSCITATION'
                          ? 'bg-rose-950 text-rose-400 border border-rose-800'
                          : p.triage_acuity === 'EMERGENT'
                          ? 'bg-amber-950 text-amber-400 border border-amber-800'
                          : 'bg-cyan-950 text-cyan-400 border border-cyan-800'
                      }`}
                    >
                      {p.triage_acuity}
                    </span>
                  </div>

                  {/* Chief Complaint */}
                  <p className="text-xs text-slate-300 line-clamp-2 my-2 bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                    <span className="text-slate-400 font-semibold">Complaint:</span> {p.chief_complaint}
                  </p>

                  {/* Vitals Ribbon */}
                  {vitals.heart_rate && (
                    <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400 bg-slate-950/50 px-2.5 py-1.5 rounded-lg border border-slate-900">
                      <span>HR: <strong className="text-rose-400">{vitals.heart_rate}</strong></span>
                      <span>BP: <strong className="text-cyan-400">{vitals.systolic_bp}/{vitals.diastolic_bp}</strong></span>
                      <span>SpO2: <strong className="text-emerald-400">{vitals.spo2}%</strong></span>
                    </div>
                  )}
                </div>

                {/* Bottom Actions */}
                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between gap-2" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => setSelectedPatient(p)}
                    className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium hover:underline"
                  >
                    View Chart →
                  </button>

                  <div className="flex items-center gap-1.5">
                    {onOpenConsult && isAdmitted && (
                      <button
                        onClick={() => onOpenConsult(p.name)}
                        className="px-2 py-1 bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 text-[10px] rounded transition"
                      >
                        Consult
                      </button>
                    )}

                    {isAdmitted && (
                      <button
                        onClick={() => handleDischarge(p.id)}
                        className="px-2 py-1 bg-slate-800 hover:bg-rose-950 text-slate-400 hover:text-rose-300 border border-slate-700 hover:border-rose-800 text-[10px] rounded transition"
                      >
                        Discharge
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Full Patient EHR Chart Drawer Modal */}
      {selectedPatient && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 shadow-2xl relative">
            {/* Close Button */}
            <button
              onClick={() => setSelectedPatient(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 text-lg p-1"
            >
              ✕
            </button>

            {/* Header */}
            <div className="border-b border-slate-800 pb-4 mb-4">
              <div className="flex items-center gap-3">
                <h3 className="text-xl font-bold text-slate-100">{selectedPatient.name}</h3>
                <span
                  className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${
                    selectedPatient.admission_status === 'ADMITTED'
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  {selectedPatient.admission_status}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs font-mono text-slate-400">
                <span>MRN: {selectedPatient.mrn}</span>
                <span>•</span>
                <span>ID: {selectedPatient.id}</span>
                <span>•</span>
                <span>Age: {selectedPatient.age} ({selectedPatient.sex})</span>
                <span>•</span>
                <span>Dept: {selectedPatient.assigned_department}</span>
                <span>•</span>
                <span>Bed: {selectedPatient.bed_number || 'Unassigned'}</span>
              </div>
            </div>

            {/* Clinical Details */}
            <div className="space-y-4 text-xs">
              {/* Presenting Complaint */}
              <div>
                <h4 className="font-semibold text-slate-300 mb-1 uppercase tracking-wider text-[11px]">Chief Complaint</h4>
                <p className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-200">
                  {selectedPatient.chief_complaint}
                </p>
              </div>

              {/* HPI */}
              {selectedPatient.history_of_present_illness && (
                <div>
                  <h4 className="font-semibold text-slate-300 mb-1 uppercase tracking-wider text-[11px]">History of Present Illness</h4>
                  <p className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300">
                    {selectedPatient.history_of_present_illness}
                  </p>
                </div>
              )}

              {/* Vitals */}
              {selectedPatient.baseline_vitals && (
                <div>
                  <h4 className="font-semibold text-slate-300 mb-1 uppercase tracking-wider text-[11px]">Admission Baseline Vitals</h4>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono">
                    <div>
                      <span className="text-slate-500 block text-[10px]">HR</span>
                      <strong className="text-rose-400">{selectedPatient.baseline_vitals.heart_rate || '--'} bpm</strong>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">BP</span>
                      <strong className="text-cyan-400">
                        {selectedPatient.baseline_vitals.systolic_bp}/{selectedPatient.baseline_vitals.diastolic_bp}
                      </strong>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">RR</span>
                      <strong className="text-slate-200">{selectedPatient.baseline_vitals.respiratory_rate || '--'} /m</strong>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">SpO2</span>
                      <strong className="text-emerald-400">{selectedPatient.baseline_vitals.spo2 || '--'}%</strong>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">Temp</span>
                      <strong className="text-amber-400">{selectedPatient.baseline_vitals.temperature_c || '--'}°C</strong>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">Acuity</span>
                      <strong className="text-rose-300">{selectedPatient.triage_acuity}</strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Allergies */}
              {selectedPatient.allergies && selectedPatient.allergies.length > 0 && (
                <div>
                  <h4 className="font-semibold text-rose-400 mb-1 uppercase tracking-wider text-[11px]">Drug Allergies</h4>
                  <div className="bg-rose-950/30 border border-rose-900/60 p-2.5 rounded-lg text-rose-200 font-medium">
                    {selectedPatient.allergies.join(', ')}
                  </div>
                </div>
              )}

              {/* Past History & Meds */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {selectedPatient.past_medical_history && (
                  <div>
                    <h4 className="font-semibold text-slate-300 mb-1 uppercase tracking-wider text-[11px]">Past Medical History</h4>
                    <ul className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-slate-300 list-disc list-inside space-y-0.5">
                      {selectedPatient.past_medical_history.map((h, i) => (
                        <li key={i}>{h}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {selectedPatient.medications && (
                  <div>
                    <h4 className="font-semibold text-slate-300 mb-1 uppercase tracking-wider text-[11px]">Current Medications</h4>
                    <ul className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-slate-300 list-disc list-inside space-y-0.5">
                      {selectedPatient.medications.map((m, i) => (
                        <li key={i}>{m}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Actions */}
            <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between">
              <span className="text-[11px] text-slate-500">
                Admitted At: {new Date(selectedPatient.admitted_at).toLocaleString()}
              </span>

              <div className="flex items-center gap-2">
                {selectedPatient.admission_status === 'ADMITTED' && (
                  <button
                    onClick={() => handleDischarge(selectedPatient.id)}
                    className="px-3 py-1.5 bg-rose-900/60 hover:bg-rose-800 text-rose-200 text-xs rounded-lg transition"
                  >
                    Discharge Patient
                  </button>
                )}
                <button
                  onClick={() => setSelectedPatient(null)}
                  className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded-lg transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientDirectorySection;
