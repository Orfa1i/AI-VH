import React, { useState, useEffect } from 'react';
import type { PatientRecord } from '../../types';
import {
  Users,
  Search,
  RefreshCw,
  Stethoscope,
  X,
  HeartPulse,
  Activity,
  Thermometer,
  ShieldAlert,
  FileText,
  Bed,
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
        return 'bg-rose-50 text-rose-800 border-rose-200';
      case 'EMERGENT':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'URGENT':
        return 'bg-yellow-50 text-yellow-800 border-yellow-200';
      case 'LESS_URGENT':
        return 'bg-sky-50 text-sky-800 border-sky-200';
      default:
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    }
  };

  return (
    <div className="flex-1 p-4 md:p-6 bg-[#f8fafc] overflow-y-auto max-w-7xl mx-auto w-full telemetry-grid text-slate-900">
      {/* ═══════════════════════════════════════════════════════════════════
          TOP HEADER: MASTER CENSUS & BED BOARD
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 shadow-xs">
              <Users className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 tracking-wide font-sans uppercase">
                Master Patient Census &amp; Inpatient Bed Board
              </h2>
              <p className="text-xs text-slate-500 mt-0.5 font-sans">
                Real-time acute census matrix, inpatient bed assignments, longitudinal vitals telemetry, and discharge tracking.
              </p>
            </div>
          </div>
        </div>

        {/* Refresh Census Action Button */}
        <button
          onClick={fetchPatients}
          disabled={loading}
          className="group relative px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-mono font-medium rounded-xl border border-slate-200 flex items-center gap-2.5 transition-all self-start cursor-pointer active:scale-[0.98] disabled:opacity-50 shadow-xs"
        >
          <div className="w-5 h-5 rounded-md bg-white flex items-center justify-center group-hover:scale-110 transition-transform shadow-2xs">
            <RefreshCw className={`w-3.5 h-3.5 text-sky-600 ${loading ? 'animate-spin' : ''}`} />
          </div>
          <span>REFRESH CENSUS</span>
        </button>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          TACTICAL KPI METRIC TILES
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 mb-6">
        {/* Total Census */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>TOTAL CENSUS</span>
            <FileText className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1 tabular-nums">
            {totalCount}
          </div>
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">REGISTERED EHR RECORDS</div>
        </div>

        {/* Admitted Inpatients */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="text-[10px] font-mono font-bold text-emerald-700 uppercase tracking-wider flex items-center justify-between">
            <span>ACTIVE ADMITTED</span>
            <Bed className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-700 mt-1 tabular-nums">
            {admittedCount}
          </div>
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">CURRENT BED OCCUPANCY</div>
        </div>

        {/* High Acuity Patients */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="text-[10px] font-mono font-bold text-rose-700 uppercase tracking-wider flex items-center justify-between">
            <span>HIGH ACUITY (ESI 1-2)</span>
            <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-rose-700 mt-1 tabular-nums">
            {criticalCount}
          </div>
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">CRITICAL CARE SURVEILLANCE</div>
        </div>

        {/* Discharged Patients */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>DISCHARGED</span>
            <Users className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-700 mt-1 tabular-nums">
            {dischargedCount}
          </div>
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">COMPLETED ENCOUNTERS</div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          FILTER & SEARCH HORIZON BAR
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-xs mb-6 flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Patient Name, MRN, or Chief Complaint..."
            className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-sky-500 focus:ring-1 focus:ring-sky-500 focus:outline-none font-medium transition"
          />
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Status Tabs */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
            {['ALL', 'ADMITTED', 'DISCHARGED'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2.5 py-1 text-[10px] font-mono font-semibold rounded-md transition cursor-pointer ${
                  statusFilter === st
                    ? 'bg-white text-sky-700 shadow-xs border border-slate-200'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* Department Select */}
          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="bg-slate-50 text-slate-700 text-xs rounded-lg px-2.5 py-1.5 border border-slate-200 font-mono focus:bg-white focus:outline-none focus:border-sky-500 transition cursor-pointer"
          >
            <option value="ALL">All Departments</option>
            <option value="EMERGENCY">Emergency</option>
            <option value="CARDIOLOGY">Cardiology / CCU</option>
            <option value="ICU">Medical ICU</option>
            <option value="INTERNAL_MEDICINE">Internal Medicine</option>
            <option value="STEP_DOWN">Step-Down Wing</option>
          </select>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          CENSUS GRID: INPATIENT CARDS
          ═══════════════════════════════════════════════════════════════════ */}
      {loading ? (
        <div className="py-20 text-center text-slate-500 text-xs flex flex-col items-center justify-center gap-3 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-sky-400 border-t-sky-600 animate-spin" />
          <span>SYNCHRONIZING PATIENT CENSUS FROM EHR CENTRAL STORE...</span>
        </div>
      ) : filteredPatients.length === 0 ? (
        <div className="py-16 text-center bg-white border border-slate-200 rounded-2xl p-8 shadow-xs">
          <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400 mx-auto mb-3">
            <Users className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-semibold text-slate-900 font-sans">No Patient Records in Hospital Census</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto font-sans leading-relaxed">
            Hospital census is currently empty. Use the Case Intake tab to register real patient encounters for clinical testing.
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
                className="group p-4 rounded-xl bg-white border border-slate-200 hover:border-sky-400 hover:shadow-md transition-all duration-200 cursor-pointer flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar: Name, Demographics, & Acuity */}
                  <div className="flex items-start justify-between gap-2 mb-2.5">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-slate-900 group-hover:text-sky-700 transition font-sans">
                          {p.name}
                        </h4>
                        <span className="text-[10px] font-mono text-slate-500">
                          {p.age}y {p.sex}
                        </span>
                      </div>
                      <div className="text-[10px] font-mono text-slate-400 mt-0.5 flex items-center gap-1.5">
                        <span>MRN: <strong className="text-slate-600">{p.mrn}</strong></span>
                        <span>•</span>
                        <span className="text-sky-700 font-semibold">{p.id}</span>
                      </div>
                    </div>

                    <span
                      className={`px-2 py-0.5 text-[9px] font-mono font-bold rounded-md border ${
                        isAdmitted
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                          : 'bg-slate-100 text-slate-600 border-slate-200'
                      }`}
                    >
                      {p.admission_status}
                    </span>
                  </div>

                  {/* Department, Bed, & Acuity Badges */}
                  <div className="flex flex-wrap items-center gap-2 my-2.5">
                    <span className="px-2 py-0.5 text-[10px] font-mono bg-slate-100 text-sky-800 border border-slate-200 rounded-md flex items-center gap-1 font-medium">
                      <Bed className="w-3 h-3 text-sky-600" />
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
                  <div className="my-2.5 bg-slate-50 p-2.5 rounded-xl border border-slate-200 font-normal leading-relaxed">
                    <div className="text-[9px] text-slate-500 font-bold font-mono uppercase mb-0.5">
                      PRESENTING PROBLEM
                    </div>
                    <p className="text-xs text-slate-800 line-clamp-2 font-sans">
                      {p.chief_complaint}
                    </p>
                  </div>

                  {/* Vitals Telemetry Ribbon */}
                  {vitals.heart_rate && (
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-600 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 mt-2">
                      <span className="flex items-center gap-1">
                        <HeartPulse className="w-3 h-3 text-emerald-600" />
                        <strong className="text-emerald-700 tabular-nums">{vitals.heart_rate}</strong> BPM
                      </span>
                      <span className="flex items-center gap-1">
                        <Activity className="w-3 h-3 text-sky-600" />
                        <strong className="text-slate-800 tabular-nums">{vitals.systolic_bp}/{vitals.diastolic_bp}</strong>
                      </span>
                      <span className="flex items-center gap-1">
                        <Thermometer className="w-3 h-3 text-sky-600" />
                        <strong className="text-sky-700 tabular-nums">{vitals.spo2}%</strong>
                      </span>
                    </div>
                  )}
                </div>

                {/* Bottom Card Actions */}
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-400">
                    ADMITTED {new Date(p.admitted_at).toLocaleDateString()}
                  </span>

                  <div className="flex items-center gap-2">
                    {onOpenConsult && isAdmitted && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenConsult(p.name);
                        }}
                        className="px-2 py-1 bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 text-[10px] font-mono font-medium rounded-lg transition cursor-pointer flex items-center gap-1"
                        title="Consult Internal Medicine Specialist"
                      >
                        <Stethoscope className="w-3 h-3 text-sky-600" />
                        <span>CONSULT</span>
                      </button>
                    )}

                    {isAdmitted && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDischarge(p.id);
                        }}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-rose-50 text-slate-600 hover:text-rose-700 border border-slate-200 hover:border-rose-200 text-[10px] font-mono font-bold rounded-lg transition cursor-pointer active:scale-95"
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
          PATIENT EHR CHART DRAWER MODAL (LIGHT MODE)
          ═══════════════════════════════════════════════════════════════════ */}
      {selectedPatient && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 relative">
              {/* Close Button */}
              <button
                onClick={() => setSelectedPatient(null)}
                className="absolute top-5 right-5 text-slate-400 hover:text-slate-700 p-1 rounded-lg bg-slate-100 border border-slate-200 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>

              {/* Modal Header */}
              <div className="border-b border-slate-200 pb-4 mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 font-bold font-mono text-sm shadow-xs">
                    {selectedPatient.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-slate-900 font-sans tracking-tight">
                        {selectedPatient.name}
                      </h3>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded-md border ${
                          selectedPatient.admission_status === 'ADMITTED'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : 'bg-slate-100 text-slate-600 border-slate-200'
                        }`}
                      >
                        {selectedPatient.admission_status}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 mt-1 text-[11px] font-mono text-slate-500">
                      <span>MRN: <strong className="text-slate-800">{selectedPatient.mrn}</strong></span>
                      <span>•</span>
                      <span>AGE: <strong className="text-slate-800">{selectedPatient.age}y {selectedPatient.sex}</strong></span>
                      <span>•</span>
                      <span>DEPT: <strong className="text-sky-700">{selectedPatient.assigned_department}</strong> [Bed: {selectedPatient.bed_number || 'TBD'}]</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Clinical Content */}
              <div className="space-y-4 text-xs">
                {/* Chief Complaint */}
                <div>
                  <span className="font-mono text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
                    Chief Complaint (Presenting Problem)
                  </span>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 font-medium font-sans">
                    {selectedPatient.chief_complaint}
                  </div>
                </div>

                {/* HPI */}
                {selectedPatient.history_of_present_illness && (
                  <div>
                    <span className="font-mono text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
                      History of Present Illness (HPI)
                    </span>
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 leading-relaxed font-sans">
                      {selectedPatient.history_of_present_illness}
                    </div>
                  </div>
                )}

                {/* Baseline Vitals Telemetry Grid */}
                {selectedPatient.baseline_vitals && (
                  <div>
                    <span className="font-mono text-[10px] text-slate-500 uppercase tracking-wider block mb-1.5 flex items-center justify-between">
                      <span>Admission Baseline Vitals</span>
                      <span className="text-emerald-700 font-semibold">LEAD II SYNCHRONIZED</span>
                    </span>
                    <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 font-mono">
                      <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center">
                        <div className="text-[9px] text-slate-500">HEART RATE</div>
                        <div className="text-sm font-bold text-emerald-700 mt-0.5 tabular-nums">
                          {selectedPatient.baseline_vitals.heart_rate} BPM
                        </div>
                      </div>
                      <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center">
                        <div className="text-[9px] text-slate-500">BLOOD PRESSURE</div>
                        <div className="text-sm font-bold text-slate-800 mt-0.5 tabular-nums">
                          {selectedPatient.baseline_vitals.systolic_bp}/{selectedPatient.baseline_vitals.diastolic_bp}
                        </div>
                      </div>
                      <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center">
                        <div className="text-[9px] text-slate-500">RESP RATE</div>
                        <div className="text-sm font-bold text-slate-800 mt-0.5 tabular-nums">
                          {selectedPatient.baseline_vitals.respiratory_rate} bpm
                        </div>
                      </div>
                      <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center">
                        <div className="text-[9px] text-slate-500">SPO2 %</div>
                        <div className="text-sm font-bold text-sky-700 mt-0.5 tabular-nums">
                          {selectedPatient.baseline_vitals.spo2}%
                        </div>
                      </div>
                      <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center">
                        <div className="text-[9px] text-slate-500">TEMP CORE</div>
                        <div className="text-sm font-bold text-slate-800 mt-0.5 tabular-nums">
                          {selectedPatient.baseline_vitals.temperature_c}°C
                        </div>
                      </div>
                      <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center">
                        <div className="text-[9px] text-slate-500">ACUITY</div>
                        <div className="text-sm font-bold text-rose-700 mt-0.5">
                          {selectedPatient.triage_acuity}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Medical History & Allergies */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  <div>
                    <span className="font-mono text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
                      Past Medical History
                    </span>
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 min-h-[48px] font-sans">
                      {selectedPatient.past_medical_history?.join(', ') || 'None recorded'}
                    </div>
                  </div>

                  <div>
                    <span className="font-mono text-[10px] text-rose-700 uppercase tracking-wider block mb-1 flex items-center gap-1 font-semibold">
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                      <span>Known Allergies &amp; Adverse Reactions</span>
                    </span>
                    <div className="p-3 rounded-xl bg-rose-50/60 border border-rose-200 text-rose-900 min-h-[48px] font-medium font-sans">
                      {selectedPatient.allergies?.join(', ') || 'No known drug allergies (NKDA)'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Modal Actions */}
              <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-between">
                <button
                  onClick={() => setSelectedPatient(null)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-mono rounded-xl border border-slate-300 transition cursor-pointer"
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
                      className="group relative px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-mono font-bold text-xs rounded-xl shadow-xs transition-all flex items-center gap-2 cursor-pointer active:scale-[0.98]"
                    >
                      <span>CONSULT ATTENDING</span>
                      <div className="w-5 h-5 rounded-md bg-white/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <Stethoscope className="w-3.5 h-3.5 text-white" />
                      </div>
                    </button>
                  )}

                  {selectedPatient.admission_status === 'ADMITTED' && (
                    <button
                      onClick={() => handleDischarge(selectedPatient.id)}
                      className="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-mono font-bold rounded-xl transition cursor-pointer active:scale-95"
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
