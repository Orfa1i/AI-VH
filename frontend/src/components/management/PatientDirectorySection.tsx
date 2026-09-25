import React, { useState, useEffect } from 'react';
import type { PatientRecord } from '../../types';
import {
  Users,
  Search,
  RefreshCw,
  Stethoscope,
  X,
  ChevronRight
} from 'lucide-react';

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
    <div className="flex-1 p-4 md:p-6 bg-slate-950 overflow-y-auto max-w-7xl mx-auto w-full telemetry-grid">
      {/* ═══════════════════════════════════════════════════════════════════
          TOP HEADER & EHR STORE STATUS
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <Users className="w-4 h-4" />
            </div>
            <h2 className="text-base font-bold text-slate-100 tracking-wide font-headline-sm uppercase">
              Master Patient Census &amp; Inpatient Bed Board
            </h2>
            <span className="px-2 py-0.5 text-[10px] font-mono font-semibold bg-sky-950 text-sky-400 border border-sky-800 rounded">
              EHR CENTRAL STORE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time acute census matrix, bed assignments, longitudinal vitals telemetry, and discharge lifecycle tracking.
          </p>
        </div>

        <button
          onClick={fetchPatients}
          disabled={loading}
          className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-mono rounded border border-slate-800 flex items-center gap-1.5 transition self-start cursor-pointer active:scale-95 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${loading ? 'animate-spin' : ''}`} />
          <span>REFRESH CENSUS</span>
        </button>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          TACTICAL KPI METRIC TILES
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded hud-bracket backdrop-blur-md">
          <div className="text-[10px] font-mono font-semibold text-slate-400 uppercase tracking-wider">
            TOTAL CENSUS
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-0.5 tabular-nums">
            {totalCount}
          </div>
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">Persisted in database</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded hud-bracket backdrop-blur-md">
          <div className="text-[10px] font-mono font-semibold text-emerald-400 uppercase tracking-wider">
            ACTIVE INPATIENTS
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-0.5 tabular-nums">
            {admittedCount}
          </div>
          <div className="text-[10px] font-mono text-emerald-500/80 mt-0.5">Occupying clinical beds</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded hud-bracket backdrop-blur-md">
          <div className="text-[10px] font-mono font-semibold text-rose-400 uppercase tracking-wider">
            HIGH ACUITY (ESI 1-2)
          </div>
          <div className="text-2xl font-bold font-mono text-rose-400 mt-0.5 tabular-nums">
            {criticalCount}
          </div>
          <div className="text-[10px] font-mono text-rose-500/80 mt-0.5">Continuous telemetry active</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3.5 rounded hud-bracket backdrop-blur-md">
          <div className="text-[10px] font-mono font-semibold text-slate-400 uppercase tracking-wider">
            DISCHARGED
          </div>
          <div className="text-2xl font-bold font-mono text-slate-300 mt-0.5 tabular-nums">
            {dischargedCount}
          </div>
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">Disposition finalized</div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          SEARCH & FILTER TOOLBAR
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="bg-slate-900/80 border border-slate-800 p-3 rounded hud-bracket mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-500 ml-1" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by patient name, MRN, or clinical complaint..."
            className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded px-3 py-1.5 focus:outline-none focus:border-sky-500 font-mono"
          />
        </div>

        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
            <span>STATUS:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 text-slate-200 text-xs rounded px-2.5 py-1.5 border border-slate-800 focus:outline-none font-mono"
            >
              <option value="ALL">All Statuses</option>
              <option value="ADMITTED">Admitted Only</option>
              <option value="DISCHARGED">Discharged Only</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
            <span>DEPT:</span>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="bg-slate-950 text-slate-200 text-xs rounded px-2.5 py-1.5 border border-slate-800 focus:outline-none font-mono"
            >
              <option value="ALL">All Departments</option>
              <option value="EMERGENCY">Emergency</option>
              <option value="CARDIOLOGY">Cardiology</option>
              <option value="ICU">Medical ICU</option>
              <option value="INTERNAL_MEDICINE">Internal Med</option>
              <option value="STEP_DOWN">Step-Down</option>
            </select>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          CENSUS GRID / ROSTER
          ═══════════════════════════════════════════════════════════════════ */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-2 font-mono">
          <span className="w-5 h-5 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin" />
          <span>SYNCHRONIZING PATIENT CENSUS FROM EHR...</span>
        </div>
      ) : filteredPatients.length === 0 ? (
        <div className="py-16 text-center bg-slate-900/40 border border-slate-800 rounded p-8 hud-bracket">
          <Users className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-slate-300">No Patient Records Found</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto font-mono">
            No matching patient records found. Use the Clinical Case Intake tab to admit new cases.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {filteredPatients.map((p) => {
            const isAdmitted = p.admission_status === 'ADMITTED';
            const vitals = p.baseline_vitals || {};

            return (
              <div
                key={p.id}
                className="bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 rounded p-3.5 transition shadow-sm flex flex-col justify-between cursor-pointer group hud-bracket"
                onClick={() => setSelectedPatient(p)}
              >
                <div>
                  {/* Top Bar: Name, Demographics, & Acuity */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-xs font-bold text-slate-100 group-hover:text-sky-300 transition">
                          {p.name}
                        </h4>
                        <span className="text-[10px] font-mono text-slate-400">
                          {p.age}y {p.sex}
                        </span>
                      </div>
                      <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                        {p.mrn} • <span className="text-sky-400">{p.id}</span>
                      </div>
                    </div>

                    <span
                      className={`px-1.5 py-0.2 text-[9px] font-mono font-bold rounded border ${
                        isAdmitted
                          ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}
                    >
                      {p.admission_status}
                    </span>
                  </div>

                  {/* Bed & Acuity Badges */}
                  <div className="flex flex-wrap items-center gap-1.5 my-2">
                    <span className="px-1.5 py-0.2 text-[9px] font-mono bg-slate-950 text-sky-400 border border-slate-800 rounded">
                      {p.assigned_department} • Bed {p.bed_number || 'TBD'}
                    </span>

                    <span
                      className={`px-1.5 py-0.2 text-[9px] font-mono font-bold rounded border ${
                        p.triage_acuity === 'RESUSCITATION'
                          ? 'bg-rose-950 text-rose-400 border-rose-800'
                          : p.triage_acuity === 'EMERGENT'
                          ? 'bg-amber-950 text-amber-400 border-amber-800'
                          : 'bg-sky-950 text-sky-400 border-sky-800'
                      }`}
                    >
                      {p.triage_acuity}
                    </span>
                  </div>

                  {/* Chief Complaint */}
                  <p className="text-[11px] text-slate-300 line-clamp-2 my-2 bg-slate-950/80 p-2 rounded border border-slate-800/80 font-normal leading-relaxed">
                    <span className="text-slate-400 font-semibold font-mono text-[10px]">PRESENTATION:</span> {p.chief_complaint}
                  </p>

                  {/* Vitals Ribbon */}
                  {vitals.heart_rate && (
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 bg-slate-950/90 px-2 py-1 rounded border border-slate-800/60">
                      <span>HR: <strong className="text-emerald-400 tabular-nums">{vitals.heart_rate}</strong></span>
                      <span>BP: <strong className="text-slate-200 tabular-nums">{vitals.systolic_bp}/{vitals.diastolic_bp}</strong></span>
                      <span>SpO2: <strong className="text-sky-400 tabular-nums">{vitals.spo2}%</strong></span>
                    </div>
                  )}
                </div>

                {/* Bottom Actions */}
                <div
                  className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between gap-2"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => setSelectedPatient(p)}
                    className="text-[10px] font-mono text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-0.5 cursor-pointer"
                  >
                    <span>VIEW CHART</span>
                    <ChevronRight className="w-3 h-3" />
                  </button>

                  <div className="flex items-center gap-1.5">
                    {onOpenConsult && isAdmitted && (
                      <button
                        onClick={() => onOpenConsult(p.name)}
                        className="px-2 py-0.5 bg-sky-950/80 hover:bg-sky-900 text-sky-400 border border-sky-800/80 text-[10px] font-mono rounded transition cursor-pointer"
                      >
                        CONSULT
                      </button>
                    )}

                    {isAdmitted && (
                      <button
                        onClick={() => handleDischarge(p.id)}
                        className="px-2 py-0.5 bg-slate-800 hover:bg-rose-950 text-slate-400 hover:text-rose-400 border border-slate-700 hover:border-rose-800 text-[10px] font-mono rounded transition cursor-pointer"
                      >
                        DISCHARGE
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          PATIENT EHR CHART DRAWER MODAL
          ═══════════════════════════════════════════════════════════════════ */}
      {selectedPatient && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded max-w-2xl w-full max-h-[85vh] overflow-y-auto p-5 shadow-2xl relative hud-bracket">
            {/* Close Button */}
            <button
              onClick={() => setSelectedPatient(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 p-1 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Header */}
            <div className="border-b border-slate-800 pb-3.5 mb-4">
              <div className="flex items-center gap-3">
                <h3 className="text-base font-bold text-slate-100 font-headline-sm">{selectedPatient.name}</h3>
                <span
                  className={`px-2 py-0.2 text-[10px] font-mono font-bold rounded border ${
                    selectedPatient.admission_status === 'ADMITTED'
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  {selectedPatient.admission_status}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3 mt-1 text-[11px] font-mono text-slate-400">
                <span>MRN: <strong className="text-slate-200">{selectedPatient.mrn}</strong></span>
                <span>•</span>
                <span>AGE: <strong className="text-slate-200">{selectedPatient.age}yo {selectedPatient.sex}</strong></span>
                <span>•</span>
                <span>DEPT: <strong className="text-sky-400">{selectedPatient.assigned_department}</strong> [Bed: {selectedPatient.bed_number || 'TBD'}]</span>
              </div>
            </div>

            {/* Clinical Content */}
            <div className="space-y-3.5 text-xs">
              <div>
                <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                  Chief Complaint
                </span>
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-200 font-medium">
                  {selectedPatient.chief_complaint}
                </div>
              </div>

              {selectedPatient.history_of_present_illness && (
                <div>
                  <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                    History of Present Illness (HPI)
                  </span>
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-300 leading-relaxed font-normal">
                    {selectedPatient.history_of_present_illness}
                  </div>
                </div>
              )}

              {/* Baseline Vitals */}
              {selectedPatient.baseline_vitals && (
                <div>
                  <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                    Admission Baseline Vitals
                  </span>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 font-mono">
                    <div className="bg-slate-950 p-2 rounded border border-slate-800">
                      <div className="text-[9px] text-slate-500">HEART RATE</div>
                      <div className="text-sm font-bold text-emerald-400">{selectedPatient.baseline_vitals.heart_rate} bpm</div>
                    </div>
                    <div className="bg-slate-950 p-2 rounded border border-slate-800">
                      <div className="text-[9px] text-slate-500">BLOOD PRESSURE</div>
                      <div className="text-sm font-bold text-slate-200">{selectedPatient.baseline_vitals.systolic_bp}/{selectedPatient.baseline_vitals.diastolic_bp}</div>
                    </div>
                    <div className="bg-slate-950 p-2 rounded border border-slate-800">
                      <div className="text-[9px] text-slate-500">RESP RATE</div>
                      <div className="text-sm font-bold text-slate-200">{selectedPatient.baseline_vitals.respiratory_rate} /min</div>
                    </div>
                    <div className="bg-slate-950 p-2 rounded border border-slate-800">
                      <div className="text-[9px] text-slate-500">SPO2</div>
                      <div className="text-sm font-bold text-sky-400">{selectedPatient.baseline_vitals.spo2}%</div>
                    </div>
                    <div className="bg-slate-950 p-2 rounded border border-slate-800">
                      <div className="text-[9px] text-slate-500">TEMP</div>
                      <div className="text-sm font-bold text-slate-200">{selectedPatient.baseline_vitals.temperature_c}°C</div>
                    </div>
                    <div className="bg-slate-950 p-2 rounded border border-slate-800">
                      <div className="text-[9px] text-slate-500">ACUITY</div>
                      <div className="text-sm font-bold text-rose-400">{selectedPatient.triage_acuity}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Past Medical History & Allergies */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                    Past Medical History
                  </span>
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-300 min-h-[48px]">
                    {selectedPatient.past_medical_history?.join(', ') || 'None recorded'}
                  </div>
                </div>

                <div>
                  <span className="font-mono text-[10px] text-rose-400 uppercase tracking-wider block mb-1">
                    Known Allergies
                  </span>
                  <div className="p-2.5 rounded bg-slate-950 border border-rose-900/40 text-rose-300 min-h-[48px] font-medium">
                    {selectedPatient.allergies?.join(', ') || 'No known drug allergies (NKDA)'}
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="mt-5 pt-3.5 border-t border-slate-800 flex items-center justify-between">
              <button
                onClick={() => setSelectedPatient(null)}
                className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono rounded transition cursor-pointer"
              >
                CLOSE CHART
              </button>

              <div className="flex items-center gap-2">
                {onOpenConsult && selectedPatient.admission_status === 'ADMITTED' && (
                  <button
                    onClick={() => {
                      onOpenConsult(selectedPatient.name);
                      setSelectedPatient(null);
                    }}
                    className="px-3.5 py-1.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-mono font-bold text-xs rounded transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <Stethoscope className="w-3.5 h-3.5" />
                    <span>CONSULT ATTENDING</span>
                  </button>
                )}

                {selectedPatient.admission_status === 'ADMITTED' && (
                  <button
                    onClick={() => handleDischarge(selectedPatient.id)}
                    className="px-3 py-1.5 bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-800 text-xs font-mono rounded transition cursor-pointer"
                  >
                    DISCHARGE PATIENT
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientDirectorySection;
