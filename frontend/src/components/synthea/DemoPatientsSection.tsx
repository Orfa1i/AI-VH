import React, { useState, useEffect } from 'react';
import {
  Search,
  Sparkles,
  RefreshCw,
  Clock,
  BedDouble,
  AlertTriangle,
  CheckCircle,
  PlusCircle,
  X,
} from 'lucide-react';
import { SyntheticTimelineModal } from './SyntheticTimelineModal';

interface DemoPatientSummary {
  id: string;
  mrn: string;
  name: string;
  gender: string;
  birth_date: string;
  age: number;
  city: string;
  state: string;
  active_condition_count: number;
  encounter_count: number;
  observation_count: number;
  medication_count: number;
  allergy_count: number;
  procedure_count: number;
  immunization_count: number;
  care_plan_count: number;
  primary_diagnoses: string[];
}

interface DemoPatientsSectionProps {
  onAdmitSuccess?: () => void;
}

export const DemoPatientsSection: React.FC<DemoPatientsSectionProps> = ({
  onAdmitSuccess,
}) => {
  const [patients, setPatients] = useState<DemoPatientSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [genderFilter, setGenderFilter] = useState<string>('ALL');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);

  // Generation Modal State
  const [isGenModalOpen, setIsGenModalOpen] = useState<boolean>(false);
  const [genPopulation, setGenPopulation] = useState<number>(3);
  const [genSeed, setGenSeed] = useState<number>(101);
  const [genGender, setGenGender] = useState<string>('');
  const [genState, setGenState] = useState<string>('Massachusetts');
  const [genAgeMin, setGenAgeMin] = useState<number>(25);
  const [genAgeMax, setGenAgeMax] = useState<number>(75);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [genFeedback, setGenFeedback] = useState<string | null>(null);
  const [genError, setGenError] = useState<string | null>(null);

  // Toast / Status state
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/demo-patients');
      if (res.ok) {
        const data = await res.json();
        setPatients(data.patients || []);
      }
    } catch (err) {
      console.error('Failed to load demo patients:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    setGenFeedback(null);
    setGenError(null);
    try {
      const payload: Record<string, any> = {
        population: genPopulation,
        seed: genSeed,
        state: genState,
        age_range: [genAgeMin, genAgeMax],
        allow_docker: false,
      };
      if (genGender) {
        payload.gender = genGender;
      }

      const res = await fetch('/api/demo-patients/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        setGenFeedback(`Successfully generated ${data.population_generated} synthetic patients!`);
        await fetchPatients();
        setTimeout(() => {
          setIsGenModalOpen(false);
          setGenFeedback(null);
          setGenError(null);
        }, 1400);
      } else {
        let errorDetail = `HTTP ${res.status}: ${res.statusText || 'Request failed'}`;
        try {
          const errData = await res.json();
          if (errData && errData.detail) {
            errorDetail = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch (_) {}
        setGenError(`Failed to generate patients: ${errorDetail}`);
      }
    } catch (err: any) {
      console.error('Error generating patients:', err);
      setGenError(`Network error while requesting Synthea generation: ${err?.message || err}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAdmit = async (patientId: string, patientName: string) => {
    try {
      const res = await fetch(`/api/demo-patients/${patientId}/admit`, {
        method: 'POST',
      });
      if (res.ok) {
        setToastMessage(`Patient ${patientName} admitted to hospital wards.`);
        if (onAdmitSuccess) {
          onAdmitSuccess();
        }
        setTimeout(() => setToastMessage(null), 3500);
      } else {
        let msg = `HTTP ${res.status}`;
        try {
          const errData = await res.json();
          if (errData?.detail) {
            msg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch (_) {}
        setToastMessage(`Failed to admit ${patientName}: ${msg}`);
        setTimeout(() => setToastMessage(null), 4000);
      }
    } catch (err: any) {
      console.error('Error admitting patient:', err);
      setToastMessage(`Network error admitting ${patientName}: ${err?.message || err}`);
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  const filteredPatients = patients.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.mrn.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.primary_diagnoses.some((d) => d.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesGender =
      genderFilter === 'ALL' || p.gender.toLowerCase() === genderFilter.toLowerCase();

    return matchesSearch && matchesGender;
  });

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] overflow-hidden font-sans">
      {/* Disclaimer Banner */}
      <div className="px-6 py-2.5 bg-amber-50 border-b border-amber-200 text-amber-900 text-xs font-mono flex items-center justify-between shrink-0 shadow-2xs">
        <div className="flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            <strong>SYNTHETIC DATA DISCLAIMER:</strong> All profiles are generated via Synthea FHIR R4.
            For development, UI testing, and multi-agent simulation only. Never use for real clinical care.
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] px-2 py-0.5 rounded bg-amber-200/60 font-semibold border border-amber-300">
            FHIR R4 SPEC
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-amber-200/60 font-semibold border border-amber-300">
            OFFLINE CAPABLE
          </span>
        </div>
      </div>

      {/* Control Horizon Toolbar */}
      <div className="px-6 py-4 bg-white border-b border-slate-200 flex flex-wrap items-center justify-between gap-4 shrink-0 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-700 shadow-2xs">
            <Sparkles className="w-5 h-5 text-sky-600" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 font-mono tracking-tight flex items-center gap-2">
              <span>SYNTHEA SYNTHETIC PATIENT REPOSITORY</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 font-semibold border border-sky-300">
                {patients.length} Loaded
              </span>
            </h1>
            <p className="text-xs text-slate-500 font-mono">
              Self-hosted synthetic population generator with multi-resource clinical timelines
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Search Bar */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search name, diagnosis, MRN..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-xs font-mono rounded-md border border-slate-300 focus:outline-none focus:ring-1 focus:ring-sky-500 bg-slate-50 w-64 text-slate-800"
            />
          </div>

          {/* Gender Filter */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-md border border-slate-200 text-xs font-mono">
            {['ALL', 'MALE', 'FEMALE'].map((g) => (
              <button
                key={g}
                onClick={() => setGenderFilter(g)}
                className={`px-2.5 py-1 rounded cursor-pointer transition ${
                  genderFilter === g
                    ? 'bg-white font-bold text-slate-900 shadow-xs'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                {g}
              </button>
            ))}
          </div>

          {/* Refresh Button */}
          <button
            onClick={fetchPatients}
            disabled={loading}
            className="p-2 rounded-md bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 transition cursor-pointer"
            title="Reload repository"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          {/* Generate Synthetic Population Action */}
          <button
            onClick={() => {
              setGenFeedback(null);
              setGenError(null);
              setIsGenModalOpen(true);
            }}
            className="px-3.5 py-2 rounded-md bg-sky-600 hover:bg-sky-500 text-white font-mono font-bold text-xs flex items-center gap-1.5 shadow-xs transition cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Generate Patients</span>
          </button>
        </div>
      </div>

      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="px-6 py-2 bg-emerald-50 border-b border-emerald-200 text-emerald-800 text-xs font-mono flex items-center justify-between animate-fade-in shrink-0">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span>{toastMessage}</span>
          </div>
          <button
            onClick={() => setToastMessage(null)}
            className="text-emerald-700 hover:text-emerald-900"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Patient Cards Grid */}
      <div className="flex-1 p-6 overflow-y-auto">
        {loading ? (
          <div className="py-24 text-center text-slate-400 font-mono text-sm">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-sky-600" />
            Loading synthetic patient repository...
          </div>
        ) : filteredPatients.length === 0 ? (
          <div className="py-20 text-center text-slate-400 font-mono text-xs">
            No synthetic patients found matching search criteria.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {filteredPatients.map((patient) => (
              <div
                key={patient.id}
                onClick={() => setSelectedPatientId(patient.id)}
                className="group bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:border-sky-400 hover:shadow-md transition flex flex-col justify-between cursor-pointer"
              >
                <div>
                  {/* Top Demographics Bar */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-slate-100 group-hover:bg-sky-50 group-hover:border-sky-200 border border-slate-200 flex items-center justify-center text-slate-700 group-hover:text-sky-700 font-mono font-bold text-sm transition">
                        {patient.gender === 'male' ? 'M' : 'F'}
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 group-hover:text-sky-700 font-mono transition flex items-center gap-1.5">
                          <span>{patient.name}</span>
                        </h3>
                        <p className="text-[11px] text-slate-500 font-mono">
                          {patient.age} yrs • {patient.gender.toUpperCase()} • {patient.city}, {patient.state}
                        </p>
                      </div>
                    </div>

                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                      {patient.mrn}
                    </span>
                  </div>

                  {/* Primary Diagnoses Chips */}
                  <div className="mb-4">
                    <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1.5">
                      Diagnoses & Conditions
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {patient.primary_diagnoses.length > 0 ? (
                        patient.primary_diagnoses.map((diag, di) => (
                          <span
                            key={di}
                            className="px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 text-[11px] font-medium"
                          >
                            {diag}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-400 text-xs italic">Routine Evaluation</span>
                      )}
                    </div>
                  </div>

                  {/* Resource Counters Grid */}
                  <div className="grid grid-cols-4 gap-2 py-3 px-3 bg-slate-50 rounded-lg border border-slate-100 font-mono text-center mb-4">
                    <div>
                      <span className="text-[10px] text-slate-400 block">Encounters</span>
                      <span className="text-xs font-bold text-slate-800">
                        {patient.encounter_count}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">Meds</span>
                      <span className="text-xs font-bold text-purple-700">
                        {patient.medication_count}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">Labs/Obs</span>
                      <span className="text-xs font-bold text-emerald-700">
                        {patient.observation_count}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">Allergies</span>
                      <span className="text-xs font-bold text-rose-700">
                        {patient.allergy_count}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Bottom Actions */}
                <div className="flex items-center gap-2 pt-3 border-t border-slate-100 font-mono">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedPatientId(patient.id);
                    }}
                    className="flex-1 py-1.5 px-3 bg-sky-50 hover:bg-sky-100 text-sky-800 text-xs font-bold rounded-md transition cursor-pointer flex items-center justify-center gap-1.5 border border-sky-200"
                  >
                    <Clock className="w-3.5 h-3.5 text-sky-600" />
                    <span>View Case Details</span>
                  </button>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAdmit(patient.id, patient.name);
                    }}
                    className="py-1.5 px-3 bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold rounded-md transition cursor-pointer flex items-center justify-center gap-1 shadow-2xs"
                    title="Admit directly into hospital wards"
                  >
                    <BedDouble className="w-3.5 h-3.5" />
                    <span>Admit</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Generation Modal */}
      {isGenModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="relative w-full max-w-lg bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden font-sans p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-md bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-700">
                  <Sparkles className="w-4 h-4 text-sky-600" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 font-mono">
                    Generate Synthetic Population
                  </h3>
                  <p className="text-[11px] text-slate-500 font-mono">
                    Synthea FHIR R4 deterministic engine
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsGenModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleGenerate} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-700 font-bold mb-1">
                  Population Count: {genPopulation}
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={genPopulation}
                  onChange={(e) => setGenPopulation(Number(e.target.value))}
                  className="w-full accent-sky-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Random Seed</label>
                  <input
                    type="number"
                    value={genSeed}
                    onChange={(e) => setGenSeed(Number(e.target.value))}
                    className="w-full px-3 py-1.5 rounded border border-slate-300 bg-slate-50 text-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-slate-700 font-bold mb-1">Gender</label>
                  <select
                    value={genGender}
                    onChange={(e) => setGenGender(e.target.value)}
                    className="w-full px-3 py-1.5 rounded border border-slate-300 bg-slate-50 text-slate-800"
                  >
                    <option value="">Any (Random)</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">State Demographics</label>
                  <select
                    value={genState}
                    onChange={(e) => setGenState(e.target.value)}
                    className="w-full px-3 py-1.5 rounded border border-slate-300 bg-slate-50 text-slate-800"
                  >
                    <option value="Massachusetts">Massachusetts</option>
                    <option value="California">California</option>
                    <option value="Texas">Texas</option>
                    <option value="New York">New York</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-bold mb-1">Age Range</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={genAgeMin}
                      onChange={(e) => setGenAgeMin(Number(e.target.value))}
                      className="w-1/2 px-2 py-1.5 rounded border border-slate-300 bg-slate-50 text-slate-800"
                    />
                    <span>-</span>
                    <input
                      type="number"
                      placeholder="Max"
                      value={genAgeMax}
                      onChange={(e) => setGenAgeMax(Number(e.target.value))}
                      className="w-1/2 px-2 py-1.5 rounded border border-slate-300 bg-slate-50 text-slate-800"
                    />
                  </div>
                </div>
              </div>

              {genFeedback && (
                <div className="p-2.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-mono flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0"></span>
                  <span>{genFeedback}</span>
                </div>
              )}

              {genError && (
                <div className="p-2.5 rounded bg-rose-50 border border-rose-200 text-rose-800 text-[11px] font-mono flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>{genError}</span>
                </div>
              )}

              <div className="pt-3 border-t border-slate-200 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsGenModalOpen(false)}
                  className="px-4 py-2 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white font-bold transition cursor-pointer flex items-center gap-1.5 shadow-xs disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{isGenerating ? 'Generating...' : 'Run Generator'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Timeline Inspector Modal */}
      {selectedPatientId && (
        <SyntheticTimelineModal
          patientId={selectedPatientId}
          onClose={() => setSelectedPatientId(null)}
          onAdmitSuccess={() => {
            if (onAdmitSuccess) {
              onAdmitSuccess();
            }
          }}
        />
      )}
    </div>
  );
};
