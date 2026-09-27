import React, { useState, useEffect } from 'react';
import type { PatientRecord } from '../../types';
import {
  Users,
  Search,
  RefreshCw,
  Stethoscope,
  X,
  ChevronRight,
  UserCheck,
  Activity,
  HeartPulse,
  Thermometer,
  ShieldAlert,
  FileText,
  Bed
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

  const getAcuityColor = (acuity: string) => {
    switch (acuity) {
      case 'RESUSCITATION':
        return 'bg-rose-950/80 text-rose-300 border-rose-800/80';
      case 'EMERGENT':
        return 'bg-amber-950/80 text-amber-300 border-amber-800/80';
      case 'URGENT':
        return 'bg-yellow-950/80 text-yellow-300 border-yellow-800/80';
      case 'LESS_URGENT':
        return 'bg-sky-950/80 text-sky-300 border-sky-800/80';
      default:
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80';
    }
  };

  return (
    <div className="flex-1 p-4 md:p-6 bg-slate-950 overflow-y-auto max-w-7xl mx-auto w-full telemetry-grid text-slate-200">
      {/* ═══════════════════════════════════════════════════════════════════
          TOP HEADER: MASTER CENSUS & BED BOARD
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <Users className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 tracking-wide font-sans uppercase">
                Master Patient Census &amp; Inpatient Bed Board
              </h2>
              <p className="text-xs text-slate-400 mt-0.5 font-sans">
                Real-time acute census matrix, inpatient bed assignments, longitudinal vitals telemetry, and discharge tracking.
              </p>
            </div>
          </div>
        </div>

        {/* Refresh Census Action Button (Button-in-Button) */}
        <button
          onClick={fetchPatients}
          disabled={loading}
          className="group relative px-4 py-2 bg-slate-900 hover:bg-slate-850 text-slate-300 hover:text-white text-xs font-mono font-medium rounded-xl border border-slate-850 flex items-center gap-2.5 transition-all self-start cursor-pointer active:scale-[0.98] disabled:opacity-50 shadow-sm"
        >
          <div className="w-5 h-5 rounded-md bg-slate-800/80 flex items-center justify-center group-hover:scale-110 transition-transform">
            <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${loading ? 'animate-spin' : ''}`} />
          </div>
          <span>REFRESH CENSUS</span>
        </button>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          TACTICAL KPI METRIC TILES (DOUBLE-BEZEL CONCENTRIC CARDS)
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 mb-6">
        {/* Total Census */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-slate-800/60 to-slate-900/40 border border-slate-700/50 shadow-xl">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>TOTAL CENSUS</span>
              <FileText className="w-3.5 h-3.5 text-slate-500" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-1 tabular-nums">
              {totalCount}
            </div>
            <div className="text-[10px] font-mono text-slate-500 mt-1">Persisted in hospital database</div>
          </div>
        </div>

        {/* Active Inpatients */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-emerald-500/20 via-slate-800/40 to-slate-900/60 border border-emerald-500/30 shadow-xl">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider flex items-center justify-between">
              <span>ACTIVE INPATIENTS</span>
              <Bed className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1 tabular-nums">
              {admittedCount}
            </div>
            <div className="text-[10px] font-mono text-emerald-500/80 mt-1">Occupying clinical beds</div>
          </div>
        </div>

        {/* High Acuity (ESI 1-2) */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-rose-500/20 via-slate-800/40 to-slate-900/60 border border-rose-500/30 shadow-xl">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="text-[10px] font-mono font-bold text-rose-400 uppercase tracking-wider flex items-center justify-between">
              <span>HIGH ACUITY (ESI 1-2)</span>
              <Activity className="w-3.5 h-3.5 text-rose-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-rose-400 mt-1 tabular-nums">
              {criticalCount}
            </div>
            <div className="text-[10px] font-mono text-rose-500/80 mt-1">Continuous telemetry active</div>
          </div>
        </div>

        {/* Discharged */}
        <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-slate-800/60 to-slate-900/40 border border-slate-700/50 shadow-xl">
          <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md">
            <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>DISCHARGED</span>
              <UserCheck className="w-3.5 h-3.5 text-slate-500" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-300 mt-1 tabular-nums">
              {dischargedCount}
            </div>
            <div className="text-[10px] font-mono text-slate-500 mt-1">Disposition finalized</div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          SEARCH & FILTER TOOLBAR (DOUBLE-BEZEL GLASS BAR)
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="relative rounded-2xl p-0.5 bg-gradient-to-r from-slate-800/70 via-slate-800/40 to-slate-800/70 border border-slate-700/50 shadow-lg mb-6">
        <div className="p-3.5 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 flex-1 min-w-[260px]">
            <Search className="w-4 h-4 text-slate-400 ml-1 shrink-0" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by patient name, MRN, or clinical complaint..."
              className="w-full bg-slate-900/80 border border-slate-800 text-slate-200 text-xs rounded-xl px-3.5 py-2 focus:outline-none focus:border-sky-500 font-mono transition placeholder-slate-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
              <span>STATUS:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-900 text-slate-200 text-xs rounded-xl px-3 py-2 border border-slate-800 focus:outline-none focus:border-sky-500 font-mono transition cursor-pointer"
              >
                <option value="ALL">All Statuses</option>
                <option value="ADMITTED">Admitted Only</option>
                <option value="DISCHARGED">Discharged Only</option>
              </select>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
              <span>DEPT:</span>
              <select
                value={departmentFilter}
                onChange={(e) => setDepartmentFilter(e.target.value)}
                className="bg-slate-900 text-slate-200 text-xs rounded-xl px-3 py-2 border border-slate-800 focus:outline-none focus:border-sky-500 font-mono transition cursor-pointer"
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
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          CENSUS GRID: INPATIENT CARDS
          ═══════════════════════════════════════════════════════════════════ */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-3 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-sky-400/30 border-t-sky-400 animate-spin" />
          <span>SYNCHRONIZING PATIENT CENSUS FROM EHR CENTRAL STORE...</span>
        </div>
      ) : filteredPatients.length === 0 ? (
        <div className="py-16 text-center bg-slate-900/40 border border-slate-800/80 rounded-2xl p-8">
          <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 mx-auto mb-3">
            <Users className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-semibold text-slate-200 font-sans">No Patient Records Found</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto font-mono">
            No matching patient records match your filter criteria. Use the Case Intake tab to admit new cases.
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
                onClick={() => setSelectedPatient(p)}
                className="group relative rounded-2xl p-0.5 bg-gradient-to-b from-slate-800/60 to-slate-900/40 border border-slate-700/50 hover:border-sky-500/50 hover:shadow-xl hover:shadow-sky-500/10 transition-all duration-200 cursor-pointer flex flex-col justify-between"
              >
                <div className="p-4 rounded-[calc(1rem-2px)] bg-slate-950/90 backdrop-blur-md flex flex-col justify-between h-full">
                  <div>
                    {/* Top Bar: Name, Demographics, & Acuity */}
                    <div className="flex items-start justify-between gap-2 mb-2.5">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-bold text-slate-100 group-hover:text-sky-300 transition font-sans">
                            {p.name}
                          </h4>
                          <span className="text-[10px] font-mono text-slate-400">
                            {p.age}y {p.sex}
                          </span>
                        </div>
                        <div className="text-[10px] font-mono text-slate-400 mt-0.5 flex items-center gap-1.5">
                          <span>MRN: <strong className="text-slate-300">{p.mrn}</strong></span>
                          <span>•</span>
                          <span className="text-sky-400 font-semibold">{p.id}</span>
                        </div>
                      </div>

                      <span
                        className={`px-2 py-0.5 text-[9px] font-mono font-bold rounded-md border ${
                          isAdmitted
                            ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800/80'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}
                      >
                        {p.admission_status}
                      </span>
                    </div>

                    {/* Department, Bed, & Acuity Badges */}
                    <div className="flex flex-wrap items-center gap-2 my-2.5">
                      <span className="px-2 py-0.5 text-[10px] font-mono bg-slate-900 text-sky-400 border border-slate-800 rounded-md flex items-center gap-1">
                        <Bed className="w-3 h-3 text-sky-400" />
                        {p.assigned_department} • Bed {p.bed_number || 'TBD'}
                      </span>

                      <span
                        className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded-md border ${getAcuityColor(
                          p.triage_acuity
                        )}`}
                      >
                        {p.triage_acuity}
                      </span>
                    </div>

                    {/* Chief Complaint Presentation */}
                    <div className="my-2.5 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80 font-normal leading-relaxed">
                      <div className="text-[9px] text-slate-400 font-bold font-mono uppercase mb-0.5">
                        PRESENTING PROBLEM
                      </div>
                      <p className="text-xs text-slate-200 line-clamp-2 font-sans">
                        {p.chief_complaint}
                      </p>
                    </div>

                    {/* Vitals Telemetry Ribbon */}
                    {vitals.heart_rate && (
                      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 bg-slate-900/90 px-3 py-1.5 rounded-xl border border-slate-800/80 mt-2">
                        <span className="flex items-center gap-1">
                          <HeartPulse className="w-3 h-3 text-emerald-400" />
                          <strong className="text-emerald-400 tabular-nums">{vitals.heart_rate}</strong> BPM
                        </span>
                        <span className="flex items-center gap-1">
                          <Activity className="w-3 h-3 text-sky-400" />
                          <strong className="text-slate-200 tabular-nums">{vitals.systolic_bp}/{vitals.diastolic_bp}</strong>
                        </span>
                        <span className="flex items-center gap-1">
                          <Thermometer className="w-3 h-3 text-sky-400" />
                          <strong className="text-sky-400 tabular-nums">{vitals.spo2}%</strong>
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Bottom Action Controls (Button-in-Button) */}
                  <div
                    className="mt-3.5 pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={() => setSelectedPatient(p)}
                      className="group/btn text-[11px] font-mono text-sky-400 hover:text-sky-300 font-bold flex items-center gap-1 cursor-pointer transition"
                    >
                      <span>VIEW CHART</span>
                      <ChevronRight className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 transition-transform" />
                    </button>

                    <div className="flex items-center gap-2">
                      {onOpenConsult && isAdmitted && (
                        <button
                          onClick={() => onOpenConsult(p.name)}
                          className="px-2.5 py-1 bg-sky-950/80 hover:bg-sky-900 text-sky-300 border border-sky-800/80 text-[10px] font-mono font-bold rounded-lg transition cursor-pointer active:scale-95"
                        >
                          CONSULT
                        </button>
                      )}

                      {isAdmitted && (
                        <button
                          onClick={() => handleDischarge(p.id)}
                          className="px-2.5 py-1 bg-slate-900 hover:bg-rose-950/80 text-slate-400 hover:text-rose-300 border border-slate-800 hover:border-rose-800/80 text-[10px] font-mono font-bold rounded-lg transition cursor-pointer active:scale-95"
                        >
                          DISCHARGE
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

      {/* ═══════════════════════════════════════════════════════════════════
          PATIENT EHR CHART DRAWER MODAL (DOUBLE-BEZEL CONCENTRIC MODAL)
          ═══════════════════════════════════════════════════════════════════ */}
      {selectedPatient && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="relative rounded-2xl p-0.5 bg-gradient-to-b from-sky-500/40 via-slate-800/50 to-slate-900/70 border border-sky-500/40 shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 rounded-[calc(1rem-2px)] bg-slate-950/95 backdrop-blur-xl relative">
              {/* Close Button */}
              <button
                onClick={() => setSelectedPatient(null)}
                className="absolute top-5 right-5 text-slate-400 hover:text-slate-100 p-1 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>

              {/* Modal Header */}
              <div className="border-b border-slate-800/80 pb-4 mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 font-bold font-mono text-sm">
                    {selectedPatient.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-slate-100 font-sans tracking-tight">
                        {selectedPatient.name}
                      </h3>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded-md border ${
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
                      <span>AGE: <strong className="text-slate-200">{selectedPatient.age}y {selectedPatient.sex}</strong></span>
                      <span>•</span>
                      <span>DEPT: <strong className="text-sky-400">{selectedPatient.assigned_department}</strong> [Bed: {selectedPatient.bed_number || 'TBD'}]</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Clinical Content */}
              <div className="space-y-4 text-xs">
                {/* Chief Complaint */}
                <div>
                  <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                    Chief Complaint (Presenting Problem)
                  </span>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-200 font-medium font-sans">
                    {selectedPatient.chief_complaint}
                  </div>
                </div>

                {/* HPI */}
                {selectedPatient.history_of_present_illness && (
                  <div>
                    <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                      History of Present Illness (HPI)
                    </span>
                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-300 leading-relaxed font-sans">
                      {selectedPatient.history_of_present_illness}
                    </div>
                  </div>
                )}

                {/* Baseline Vitals Telemetry Grid */}
                {selectedPatient.baseline_vitals && (
                  <div>
                    <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider block mb-1.5 flex items-center justify-between">
                      <span>Admission Baseline Vitals</span>
                      <span className="text-emerald-400 font-semibold">LEAD II SYNCHRONIZED</span>
                    </span>
                    <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 font-mono">
                      <div className="bg-slate-900/70 p-2.5 rounded-xl border border-slate-800 text-center">
                        <div className="text-[9px] text-slate-400">HEART RATE</div>
                        <div className="text-sm font-bold text-emerald-400 mt-0.5 tabular-nums">
                          {selectedPatient.baseline_vitals.heart_rate} BPM
                        </div>
                      </div>
                      <div className="bg-slate-900/70 p-2.5 rounded-xl border border-slate-800 text-center">
                        <div className="text-[9px] text-slate-400">BLOOD PRESSURE</div>
                        <div className="text-sm font-bold text-slate-200 mt-0.5 tabular-nums">
                          {selectedPatient.baseline_vitals.systolic_bp}/{selectedPatient.baseline_vitals.diastolic_bp}
                        </div>
                      </div>
                      <div className="bg-slate-900/70 p-2.5 rounded-xl border border-slate-800 text-center">
                        <div className="text-[9px] text-slate-400">RESP RATE</div>
                        <div className="text-sm font-bold text-slate-200 mt-0.5 tabular-nums">
                          {selectedPatient.baseline_vitals.respiratory_rate} bpm
                        </div>
                      </div>
                      <div className="bg-slate-900/70 p-2.5 rounded-xl border border-slate-800 text-center">
                        <div className="text-[9px] text-slate-400">SPO2 %</div>
                        <div className="text-sm font-bold text-sky-400 mt-0.5 tabular-nums">
                          {selectedPatient.baseline_vitals.spo2}%
                        </div>
                      </div>
                      <div className="bg-slate-900/70 p-2.5 rounded-xl border border-slate-800 text-center">
                        <div className="text-[9px] text-slate-400">TEMP CORE</div>
                        <div className="text-sm font-bold text-slate-200 mt-0.5 tabular-nums">
                          {selectedPatient.baseline_vitals.temperature_c}°C
                        </div>
                      </div>
                      <div className="bg-slate-900/70 p-2.5 rounded-xl border border-slate-800 text-center">
                        <div className="text-[9px] text-slate-400">ACUITY</div>
                        <div className="text-sm font-bold text-rose-400 mt-0.5">
                          {selectedPatient.triage_acuity}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Medical History & Allergies */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  <div>
                    <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                      Past Medical History
                    </span>
                    <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 text-slate-300 min-h-[48px] font-sans">
                      {selectedPatient.past_medical_history?.join(', ') || 'None recorded'}
                    </div>
                  </div>

                  <div>
                    <span className="font-mono text-[10px] text-rose-400 uppercase tracking-wider block mb-1 flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      <span>Known Allergies &amp; Adverse Reactions</span>
                    </span>
                    <div className="p-3 rounded-xl bg-slate-900/70 border border-rose-900/60 text-rose-300 min-h-[48px] font-medium font-sans">
                      {selectedPatient.allergies?.join(', ') || 'No known drug allergies (NKDA)'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Modal Actions (Button-in-Button Architecture) */}
              <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between">
                <button
                  onClick={() => setSelectedPatient(null)}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-mono rounded-xl border border-slate-800 transition cursor-pointer"
                >
                  CLOSE CHART
                </button>

                <div className="flex items-center gap-2.5">
                  {onOpenConsult && selectedPatient.admission_status === 'ADMITTED' && (
                    <button
                      onClick={() => {
                        onOpenConsult(selectedPatient.name);
                        setSelectedPatient(null);
                      }}
                      className="group relative px-4 py-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-mono font-bold text-xs rounded-xl shadow-lg shadow-sky-500/20 transition-all flex items-center gap-2 cursor-pointer active:scale-[0.98]"
                    >
                      <span>CONSULT ATTENDING</span>
                      <div className="w-5 h-5 rounded-md bg-slate-950/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <Stethoscope className="w-3.5 h-3.5 text-slate-950" />
                      </div>
                    </button>
                  )}

                  {selectedPatient.admission_status === 'ADMITTED' && (
                    <button
                      onClick={() => handleDischarge(selectedPatient.id)}
                      className="px-4 py-2 bg-rose-950/80 hover:bg-rose-900 text-rose-200 border border-rose-800/80 text-xs font-mono font-bold rounded-xl transition cursor-pointer active:scale-95"
                    >
                      DISCHARGE PATIENT
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientDirectorySection;
