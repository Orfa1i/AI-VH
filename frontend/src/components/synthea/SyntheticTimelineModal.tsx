import React, { useState, useEffect } from 'react';
import {
  X,
  Clock,
  Activity,
  HeartPulse,
  Pill,
  ShieldAlert,
  Syringe,
  ClipboardList,
  FileSpreadsheet,
  Building2,
  Calendar,
  Tag,
  BedDouble,
  FileCode,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';

interface TimelineEvent {
  id: string;
  resource_type: string;
  category: string;
  timestamp: string;
  display_date: string;
  title: string;
  subtitle?: string;
  status?: string;
  code?: string;
  system?: string;
  details?: Record<string, any>;
}

interface DemoPatientProfile {
  id: string;
  mrn: string;
  name: string;
  gender: string;
  birth_date: string;
  age: number;
  city: string;
  state: string;
  country: string;
  active_conditions: Array<{ name: string; code?: string; status?: string }>;
  current_medications: Array<{ name: string; dosage?: string; status?: string }>;
  allergies: Array<{ substance: string; criticality?: string }>;
  latest_vitals: Record<string, string>;
  total_timeline_events: number;
  disclaimer: string;
}

interface SyntheticTimelineModalProps {
  patientId: string;
  onClose: () => void;
  onAdmitSuccess?: () => void;
}

type EventFilter =
  | 'ALL'
  | 'encounter'
  | 'condition'
  | 'observation'
  | 'medication'
  | 'allergy'
  | 'procedure'
  | 'immunization'
  | 'careplan';

export const SyntheticTimelineModal: React.FC<SyntheticTimelineModalProps> = ({
  patientId,
  onClose,
  onAdmitSuccess,
}) => {
  const [profile, setProfile] = useState<DemoPatientProfile | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeFilter, setActiveFilter] = useState<EventFilter>('ALL');
  const [isAdmitting, setIsAdmitting] = useState<boolean>(false);
  const [admitStatus, setAdmitStatus] = useState<string | null>(null);
  const [showRawJson, setShowRawJson] = useState<boolean>(false);
  const [rawJson, setRawJson] = useState<any>(null);

  useEffect(() => {
    const fetchPatientData = async () => {
      setLoading(true);
      try {
        const [profRes, tlRes] = await Promise.all([
          fetch(`/api/demo-patients/${patientId}`),
          fetch(`/api/demo-patients/${patientId}/timeline`),
        ]);

        if (profRes.ok) {
          const profData = await profRes.json();
          setProfile(profData);
        }
        if (tlRes.ok) {
          const tlData = await tlRes.json();
          setEvents(tlData.events || []);
        }
      } catch (err) {
        console.error('Failed to load patient timeline:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPatientData();
  }, [patientId]);

  const handleAdmitToHospital = async () => {
    setIsAdmitting(true);
    setAdmitStatus(null);
    try {
      const res = await fetch(`/api/demo-patients/${patientId}/admit`, {
        method: 'POST',
      });
      if (res.ok) {
        setAdmitStatus('Patient successfully admitted into hospital ward.');
        if (onAdmitSuccess) {
          onAdmitSuccess();
        }
      } else {
        setAdmitStatus('Failed to admit patient.');
      }
    } catch (err) {
      console.error('Error admitting patient:', err);
      setAdmitStatus('Network error while admitting patient.');
    } finally {
      setIsAdmitting(false);
    }
  };

  const handleFetchRawJson = async () => {
    if (showRawJson) {
      setShowRawJson(false);
      return;
    }
    try {
      const res = await fetch(`/api/demo-patients/${patientId}/raw`);
      if (res.ok) {
        const data = await res.json();
        setRawJson(data);
        setShowRawJson(true);
      }
    } catch (err) {
      console.error('Failed to fetch raw FHIR:', err);
    }
  };

  const filteredEvents = events.filter((e) => {
    if (activeFilter === 'ALL') return true;
    return e.category === activeFilter;
  });

  const getEventBadgeStyle = (category: string) => {
    switch (category) {
      case 'encounter':
        return 'bg-blue-50 text-blue-800 border-blue-200';
      case 'condition':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'observation':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'medication':
        return 'bg-purple-50 text-purple-800 border-purple-200';
      case 'allergy':
        return 'bg-rose-50 text-rose-800 border-rose-200';
      case 'procedure':
        return 'bg-teal-50 text-teal-800 border-teal-200';
      case 'immunization':
        return 'bg-sky-50 text-sky-800 border-sky-200';
      case 'careplan':
        return 'bg-indigo-50 text-indigo-800 border-indigo-200';
      default:
        return 'bg-slate-50 text-slate-800 border-slate-200';
    }
  };

  const getEventIcon = (category: string) => {
    switch (category) {
      case 'encounter':
        return <Building2 className="w-4 h-4 text-blue-600" />;
      case 'condition':
        return <AlertTriangle className="w-4 h-4 text-amber-600" />;
      case 'observation':
        return <HeartPulse className="w-4 h-4 text-emerald-600" />;
      case 'medication':
        return <Pill className="w-4 h-4 text-purple-600" />;
      case 'allergy':
        return <ShieldAlert className="w-4 h-4 text-rose-600" />;
      case 'procedure':
        return <FileSpreadsheet className="w-4 h-4 text-teal-600" />;
      case 'immunization':
        return <Syringe className="w-4 h-4 text-sky-600" />;
      case 'careplan':
        return <ClipboardList className="w-4 h-4 text-indigo-600" />;
      default:
        return <Activity className="w-4 h-4 text-slate-600" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden font-sans">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-sky-100 border border-sky-200 flex items-center justify-center text-sky-700">
              <Clock className="w-5 h-5 text-sky-700" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900 font-mono tracking-tight">
                  {profile ? profile.name : 'Loading Patient Profile...'}
                </h2>
                {profile && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-sky-100 text-sky-800 border border-sky-300">
                    {profile.mrn}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 font-mono">
                {profile
                  ? `${profile.gender.toUpperCase()} • ${profile.age} YRS • DOB: ${profile.birth_date} • ${profile.city}, ${profile.state}`
                  : 'Synthea FHIR R4 Record'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleFetchRawJson}
              className="px-3 py-1.5 text-xs font-mono font-medium rounded-md bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition cursor-pointer flex items-center gap-1.5"
            >
              <FileCode className="w-3.5 h-3.5 text-slate-500" />
              <span>{showRawJson ? 'Hide FHIR' : 'View FHIR'}</span>
            </button>

            <button
              onClick={handleAdmitToHospital}
              disabled={isAdmitting}
              className="px-3.5 py-1.5 text-xs font-mono font-bold rounded-md bg-sky-600 hover:bg-sky-500 text-white transition shadow-xs cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
            >
              <BedDouble className="w-3.5 h-3.5" />
              <span>{isAdmitting ? 'Admitting...' : 'Admit to Hospital'}</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-100 transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Disclaimer Bar */}
        <div className="px-6 py-2 bg-amber-50 border-b border-amber-200 text-amber-800 text-[11px] font-mono flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              SYNTHETIC DATA DISCLAIMER: Generated via Synthea FHIR R4. Demonstration and UI testing only.
            </span>
          </div>
          {admitStatus && (
            <span className="font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded border border-emerald-300 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              {admitStatus}
            </span>
          )}
        </div>

        {/* Patient Summary Quick Bar */}
        {profile && (
          <div className="px-6 py-3 bg-white border-b border-slate-200 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs shrink-0">
            <div>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                Active Diagnoses
              </span>
              <div className="mt-1 flex flex-wrap gap-1">
                {profile.active_conditions.length > 0 ? (
                  profile.active_conditions.map((c, i) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-medium"
                    >
                      {c.name}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-400 italic">None recorded</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                Active Medications
              </span>
              <div className="mt-1 flex flex-wrap gap-1">
                {profile.current_medications.length > 0 ? (
                  profile.current_medications.map((m, i) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-200 text-[10px] font-medium"
                    >
                      {m.name}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-400 italic">None active</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                Known Allergies
              </span>
              <div className="mt-1 flex flex-wrap gap-1">
                {profile.allergies.length > 0 ? (
                  profile.allergies.map((a, i) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 text-[10px] font-medium"
                    >
                      {a.substance} ({a.criticality || 'low'})
                    </span>
                  ))
                ) : (
                  <span className="text-slate-400 italic">No Known Allergies</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                Latest Baseline Vitals
              </span>
              <div className="mt-1 font-mono text-[11px] text-slate-700">
                {profile.latest_vitals && Object.keys(profile.latest_vitals).length > 0 ? (
                  <div className="space-y-0.5">
                    {profile.latest_vitals.heart_rate && (
                      <div>HR: {profile.latest_vitals.heart_rate}</div>
                    )}
                    {profile.latest_vitals['blood_pressure_systolic_&_diastolic'] && (
                      <div>BP: {profile.latest_vitals['blood_pressure_systolic_&_diastolic']}</div>
                    )}
                  </div>
                ) : (
                  <span className="text-slate-400 italic">Vitals standard</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Timeline Category Filters */}
        <div className="px-6 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center gap-1.5 overflow-x-auto shrink-0">
          <span className="text-[10px] font-mono font-bold text-slate-500 uppercase mr-2">
            Filter Lane:
          </span>
          {(
            [
              ['ALL', 'All Events', events.length],
              ['encounter', 'Encounters', events.filter((e) => e.category === 'encounter').length],
              ['condition', 'Conditions', events.filter((e) => e.category === 'condition').length],
              ['observation', 'Labs & Vitals', events.filter((e) => e.category === 'observation').length],
              ['medication', 'Medications', events.filter((e) => e.category === 'medication').length],
              ['procedure', 'Procedures', events.filter((e) => e.category === 'procedure').length],
              ['allergy', 'Allergies', events.filter((e) => e.category === 'allergy').length],
              ['immunization', 'Vaccines', events.filter((e) => e.category === 'immunization').length],
              ['careplan', 'Care Plans', events.filter((e) => e.category === 'careplan').length],
            ] as const
          ).map(([key, label, count]) => (
            <button
              key={key}
              onClick={() => setActiveFilter(key as EventFilter)}
              className={`px-2.5 py-1 rounded text-xs font-mono font-medium flex items-center gap-1.5 transition cursor-pointer whitespace-nowrap ${
                activeFilter === key
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
              }`}
            >
              <span>{label}</span>
              <span
                className={`px-1 rounded-full text-[10px] ${
                  activeFilter === key ? 'bg-slate-800 text-slate-200' : 'bg-slate-100 text-slate-500'
                }`}
              >
                {count}
              </span>
            </button>
          ))}
        </div>

        {/* Main Content Area */}
        <div className="flex-1 p-6 overflow-y-auto bg-slate-100/50">
          {loading ? (
            <div className="py-20 text-center text-slate-400 font-mono text-sm">
              <Clock className="w-8 h-8 animate-spin mx-auto mb-2 text-sky-600" />
              Loading FHIR R4 clinical timeline...
            </div>
          ) : showRawJson ? (
            <div className="bg-slate-900 text-slate-100 p-4 rounded-lg font-mono text-xs overflow-x-auto max-h-[60vh]">
              <pre>{JSON.stringify(rawJson, null, 2)}</pre>
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="py-16 text-center text-slate-400 font-mono text-xs">
              No clinical events found for this filter category.
            </div>
          ) : (
            <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {filteredEvents.map((event) => (
                <div key={event.id} className="relative flex items-start gap-4 group">
                  {/* Timeline dot with icon */}
                  <div
                    className={`absolute -left-6 mt-1 w-6 h-6 rounded-full border flex items-center justify-center bg-white shadow-xs z-10 ${getEventBadgeStyle(
                      event.category
                    )}`}
                  >
                    {getEventIcon(event.category)}
                  </div>

                  {/* Event card */}
                  <div className="flex-1 bg-white border border-slate-200 rounded-lg p-4 shadow-xs hover:border-slate-300 transition">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider border ${getEventBadgeStyle(
                            event.category
                          )}`}
                        >
                          {event.category}
                        </span>
                        <h4 className="text-sm font-bold text-slate-900">{event.title}</h4>
                      </div>

                      <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>{event.display_date}</span>
                      </div>
                    </div>

                    {event.subtitle && (
                      <p className="text-xs text-slate-600 font-medium mb-2">{event.subtitle}</p>
                    )}

                    {/* Metadata & Details */}
                    <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-100">
                      {event.code && (
                        <div className="flex items-center gap-1">
                          <Tag className="w-3 h-3 text-slate-400" />
                          <span>
                            Code: <span className="text-slate-800">{event.code}</span>
                          </span>
                          {event.system && (
                            <span className="text-[10px] text-slate-400">
                              ({event.system.split('/').pop()})
                            </span>
                          )}
                        </div>
                      )}

                      {event.status && (
                        <div className="flex items-center gap-1">
                          <span>
                            Status: <span className="text-slate-800">{event.status}</span>
                          </span>
                        </div>
                      )}

                      {event.details?.components && event.details.components.length > 0 && (
                        <div className="w-full flex items-center gap-2 mt-1">
                          {event.details.components.map((c: any, ci: number) => (
                            <span
                              key={ci}
                              className="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-slate-700 text-[10px]"
                            >
                              {c.name}: <strong>{c.value} {c.unit}</strong>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs font-mono text-slate-500 shrink-0">
          <span>
            Total Events: <strong>{events.length}</strong> • Showing: <strong>{filteredEvents.length}</strong>
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded font-medium transition cursor-pointer"
          >
            Close Timeline
          </button>
        </div>
      </div>
    </div>
  );
};
