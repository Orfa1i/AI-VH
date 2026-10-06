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
    <div className="flex-1 flex flex-col h-full bg-[var(--ak-color-bg-app)] overflow-hidden font-sans">
      {/* Disclaimer Banner */}
      <div className="px-6 py-2.5 bg-[var(--ak-color-warning-soft)] border-b border-[var(--ak-color-border-subtle)] text-[var(--ak-color-warning)] text-xs font-mono flex items-center justify-between shrink-0 shadow-2xs">
        <div className="flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-[var(--ak-color-warning)] shrink-0" />
          <span>
            <strong>SYNTHETIC DATA DISCLAIMER:</strong> All profiles are generated via Synthea FHIR R4.
            For development, UI testing, and multi-agent simulation only. Never use for real clinical care.
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] px-2 py-0.5 rounded border-[var(--ak-color-border-subtle)]/60 font-semibold border border-[var(--ak-color-border-subtle)]">
            FHIR R4 SPEC
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded border-[var(--ak-color-border-subtle)]/60 font-semibold border border-[var(--ak-color-border-subtle)]">
            OFFLINE CAPABLE
          </span>
        </div>
      </div>

      {/* Control Horizon Toolbar */}
      <div className="px-6 py-4 bg-white border-b border-[var(--ak-color-border-subtle)] flex flex-wrap items-center justify-between gap-4 shrink-0 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[var(--ak-color-primary-soft)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-primary)] shadow-2xs">
            <Sparkles className="w-5 h-5 text-[var(--ak-color-primary)]" />
          </div>
          <div>
            <h1 className="text-base font-bold text-[var(--ak-color-text-primary)] font-mono tracking-tight flex items-center gap-2">
              <span>SYNTHEA SYNTHETIC PATIENT REPOSITORY</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--ak-color-primary-soft)] text-[var(--ak-color-primary)] font-semibold border border-[var(--ak-color-border-subtle)]">
                {patients.length} Loaded
              </span>
            </h1>
            <p className="text-xs text-[var(--ak-color-text-muted)] font-mono">
              Self-hosted synthetic population generator with multi-resource clinical timelines
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Search Bar */}
          <div className="relative">
            <Search className="w-4 h-4 text-[var(--ak-color-text-muted)] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search name, diagnosis, MRN..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-xs font-mono rounded-md border border-[var(--ak-color-border-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--ak-color-primary)] bg-[var(--ak-color-bg-subtle)] w-64 text-[var(--ak-color-text-primary)]"
            />
          </div>

          {/* Gender Filter */}
          <div className="flex items-center bg-[var(--ak-color-bg-subtle)] p-0.5 rounded-md border border-[var(--ak-color-border-subtle)] text-xs font-mono">
            {['ALL', 'MALE', 'FEMALE'].map((g) => (
              <button
                key={g}
                onClick={() => setGenderFilter(g)}
                className={`px-2.5 py-1 rounded cursor-pointer transition ${
                  genderFilter === g
                    ? 'bg-white font-bold text-[var(--ak-color-text-primary)] shadow-xs'
                    : 'text-[var(--ak-color-text-muted)] hover:text-[var(--ak-color-text-primary)]'
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
            className="p-2 rounded-md bg-white border border-[var(--ak-color-border-subtle)] text-[var(--ak-color-text-secondary)] hover:bg-[var(--ak-color-bg-subtle)] transition cursor-pointer"
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
            className="px-3.5 py-2 rounded-md bg-[var(--ak-color-primary)] hover:bg-[var(--ak-color-primary-soft)]0 text-white font-mono font-bold text-xs flex items-center gap-1.5 shadow-xs transition cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Generate Patients</span>
          </button>
        </div>
      </div>

      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="px-6 py-2 bg-[var(--ak-color-success-soft)] border-b border-[var(--ak-color-border-subtle)] text-[var(--ak-color-success)] text-xs font-mono flex items-center justify-between animate-fade-in shrink-0">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-[var(--ak-color-success)]" />
            <span>{toastMessage}</span>
          </div>
          <button
            onClick={() => setToastMessage(null)}
            className="text-[var(--ak-color-success)] hover:text-[var(--ak-color-success)]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Patient Cards Grid */}
      <div className="flex-1 p-6 overflow-y-auto">
        {loading ? (
          <div className="py-24 text-center text-[var(--ak-color-text-muted)] font-mono text-sm">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-[var(--ak-color-primary)]" />
            Loading synthetic patient repository...
          </div>
        ) : filteredPatients.length === 0 ? (
          <div className="py-20 text-center text-[var(--ak-color-text-muted)] font-mono text-xs">
            No synthetic patients found matching search criteria.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {filteredPatients.map((patient) => (
              <div
                key={patient.id}
                onClick={() => setSelectedPatientId(patient.id)}
                className="group bg-white border border-[var(--ak-color-border-subtle)] rounded-xl p-5 shadow-xs hover:bg-[var(--ak-color-primary)] hover:shadow-md transition flex flex-col justify-between cursor-pointer"
              >
                <div>
                  {/* Top Demographics Bar */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-[var(--ak-color-bg-subtle)] group-hover:bg-[var(--ak-color-primary-soft)] group-hover:border-[var(--ak-color-border-subtle)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-text-secondary)] group-hover:text-[var(--ak-color-primary)] font-mono font-bold text-sm transition">
                        {patient.gender === 'male' ? 'M' : 'F'}
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-[var(--ak-color-text-primary)] group-hover:text-[var(--ak-color-primary)] font-mono transition flex items-center gap-1.5">
                          <span>{patient.name}</span>
                        </h3>
                        <p className="text-[11px] text-[var(--ak-color-text-muted)] font-mono">
                          {patient.age} yrs • {patient.gender.toUpperCase()} • {patient.city}, {patient.state}
                        </p>
                      </div>
                    </div>

                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-secondary)] border border-[var(--ak-color-border-subtle)]">
                      {patient.mrn}
                    </span>
                  </div>

                  {/* Primary Diagnoses Chips */}
                  <div className="mb-4">
                    <span className="text-[10px] font-mono text-[var(--ak-color-text-muted)] uppercase tracking-wider block mb-1.5">
                      Diagnoses & Conditions
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {patient.primary_diagnoses.length > 0 ? (
                        patient.primary_diagnoses.map((diag, di) => (
                          <span
                            key={di}
                            className="px-2 py-0.5 rounded-md bg-[var(--ak-color-warning-soft)] text-[var(--ak-color-warning)] border border-[var(--ak-color-border-subtle)] text-[11px] font-medium"
                          >
                            {diag}
                          </span>
                        ))
                      ) : (
                        <span className="text-[var(--ak-color-text-muted)] text-xs italic">Routine Evaluation</span>
                      )}
                    </div>
                  </div>

                  {/* Resource Counters Grid */}
                  <div className="grid grid-cols-4 gap-2 py-3 px-3 bg-[var(--ak-color-bg-subtle)] rounded-lg border border-[var(--ak-color-border-subtle)] font-mono text-center mb-4">
                    <div>
                      <span className="text-[10px] text-[var(--ak-color-text-muted)] block">Encounters</span>
                      <span className="text-xs font-bold text-[var(--ak-color-text-primary)]">
                        {patient.encounter_count}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--ak-color-text-muted)] block">Meds</span>
                      <span className="text-xs font-bold text-[var(--ak-color-primary)]">
                        {patient.medication_count}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--ak-color-text-muted)] block">Labs/Obs</span>
                      <span className="text-xs font-bold text-[var(--ak-color-success)]">
                        {patient.observation_count}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--ak-color-text-muted)] block">Allergies</span>
                      <span className="text-xs font-bold text-[var(--ak-color-danger)]">
                        {patient.allergy_count}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Bottom Actions */}
                <div className="flex items-center gap-2 pt-3 border-t border-[var(--ak-color-border-subtle)] font-mono">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedPatientId(patient.id);
                    }}
                    className="flex-1 py-1.5 px-3 bg-[var(--ak-color-primary-soft)] hover:bg-[var(--ak-color-primary-soft)] text-[var(--ak-color-primary)] text-xs font-bold rounded-md transition cursor-pointer flex items-center justify-center gap-1.5 border border-[var(--ak-color-border-subtle)]"
                  >
                    <Clock className="w-3.5 h-3.5 text-[var(--ak-color-primary)]" />
                    <span>View Case Details</span>
                  </button>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAdmit(patient.id, patient.name);
                    }}
                    className="py-1.5 px-3 bg-[var(--ak-color-primary)] hover:bg-[var(--ak-color-primary-soft)]0 text-white text-xs font-bold rounded-md transition cursor-pointer flex items-center justify-center gap-1 shadow-2xs"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--ak-color-text-primary)]/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="relative w-full max-w-lg bg-white border border-[var(--ak-color-border-subtle)] rounded-xl shadow-2xl overflow-hidden font-sans p-6">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--ak-color-border-subtle)] mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-md bg-[var(--ak-color-primary-soft)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-primary)]">
                  <Sparkles className="w-4 h-4 text-[var(--ak-color-primary)]" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[var(--ak-color-text-primary)] font-mono">
                    Generate Synthetic Population
                  </h3>
                  <p className="text-[11px] text-[var(--ak-color-text-muted)] font-mono">
                    Synthea FHIR R4 deterministic engine
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsGenModalOpen(false)}
                className="text-[var(--ak-color-text-muted)] hover:text-[var(--ak-color-text-secondary)] p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleGenerate} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-[var(--ak-color-text-secondary)] font-bold mb-1">
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
                  <label className="block text-[var(--ak-color-text-secondary)] font-bold mb-1">Random Seed</label>
                  <input
                    type="number"
                    value={genSeed}
                    onChange={(e) => setGenSeed(Number(e.target.value))}
                    className="w-full px-3 py-1.5 rounded border border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)]"
                  />
                </div>

                <div>
                  <label className="block text-[var(--ak-color-text-secondary)] font-bold mb-1">Gender</label>
                  <select
                    value={genGender}
                    onChange={(e) => setGenGender(e.target.value)}
                    className="w-full px-3 py-1.5 rounded border border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)]"
                  >
                    <option value="">Any (Random)</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[var(--ak-color-text-secondary)] font-bold mb-1">State Demographics</label>
                  <select
                    value={genState}
                    onChange={(e) => setGenState(e.target.value)}
                    className="w-full px-3 py-1.5 rounded border border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)]"
                  >
                    <option value="Massachusetts">Massachusetts</option>
                    <option value="California">California</option>
                    <option value="Texas">Texas</option>
                    <option value="New York">New York</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[var(--ak-color-text-secondary)] font-bold mb-1">Age Range</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={genAgeMin}
                      onChange={(e) => setGenAgeMin(Number(e.target.value))}
                      className="w-1/2 px-2 py-1.5 rounded border border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)]"
                    />
                    <span>-</span>
                    <input
                      type="number"
                      placeholder="Max"
                      value={genAgeMax}
                      onChange={(e) => setGenAgeMax(Number(e.target.value))}
                      className="w-1/2 px-2 py-1.5 rounded border border-[var(--ak-color-border-subtle)] bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)]"
                    />
                  </div>
                </div>
              </div>

              {genFeedback && (
                <div className="p-2.5 rounded bg-[var(--ak-color-success-soft)] border border-[var(--ak-color-border-subtle)] text-[var(--ak-color-success)] text-[11px] font-mono flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[var(--ak-color-success-soft)]0 animate-pulse shrink-0"></span>
                  <span>{genFeedback}</span>
                </div>
              )}

              {genError && (
                <div className="p-2.5 rounded bg-[var(--ak-color-warning-soft)] border border-[var(--ak-color-border-subtle)] text-[var(--ak-color-danger)] text-[11px] font-mono flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-[var(--ak-color-danger)] shrink-0" />
                  <span>{genError}</span>
                </div>
              )}

              <div className="pt-3 border-t border-[var(--ak-color-border-subtle)] flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsGenModalOpen(false)}
                  className="px-4 py-2 rounded bg-[var(--ak-color-bg-subtle)] hover:bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-secondary)] font-medium transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="px-4 py-2 rounded bg-[var(--ak-color-primary)] hover:bg-[var(--ak-color-primary-soft)]0 text-white font-bold transition cursor-pointer flex items-center gap-1.5 shadow-xs disabled:opacity-50"
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
