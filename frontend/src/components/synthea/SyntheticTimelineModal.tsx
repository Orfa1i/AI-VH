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
        return 'bg-[var(--ak-color-primary-soft)] text-[var(--ak-color-primary)] border-[var(--ak-color-border-subtle)]';
      case 'condition':
        return 'bg-[var(--ak-color-warning-soft)] text-[var(--ak-color-warning)] border-[var(--ak-color-border-subtle)]';
      case 'observation':
        return 'bg-[var(--ak-color-success-soft)] text-[var(--ak-color-success)] border-[var(--ak-color-border-subtle)]';
      case 'medication':
        return 'bg-[var(--ak-color-primary-soft)] text-[var(--ak-color-primary)] border-[var(--ak-color-border-subtle)]';
      case 'allergy':
        return 'bg-[var(--ak-color-warning-soft)] text-[var(--ak-color-danger)] border-[var(--ak-color-border-subtle)]';
      case 'procedure':
        return 'bg-[var(--ak-color-primary-soft)] text-[var(--ak-color-primary)] border-[var(--ak-color-border-subtle)]';
      case 'immunization':
        return 'bg-[var(--ak-color-primary-soft)] text-[var(--ak-color-primary)] border-[var(--ak-color-border-subtle)]';
      case 'careplan':
        return 'bg-[var(--ak-color-primary-soft)] text-[var(--ak-color-primary)] border-[var(--ak-color-border-subtle)]';
      default:
        return 'bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-primary)] border-[var(--ak-color-border-subtle)]';
    }
  };

  const getEventIcon = (category: string) => {
    switch (category) {
      case 'encounter':
        return <Building2 className="w-4 h-4 text-[var(--ak-color-primary)]" />;
      case 'condition':
        return <AlertTriangle className="w-4 h-4 text-[var(--ak-color-warning)]" />;
      case 'observation':
        return <HeartPulse className="w-4 h-4 text-[var(--ak-color-success)]" />;
      case 'medication':
        return <Pill className="w-4 h-4 text-[var(--ak-color-primary)]" />;
      case 'allergy':
        return <ShieldAlert className="w-4 h-4 text-[var(--ak-color-danger)]" />;
      case 'procedure':
        return <FileSpreadsheet className="w-4 h-4 text-[var(--ak-color-primary)]" />;
      case 'immunization':
        return <Syringe className="w-4 h-4 text-[var(--ak-color-primary)]" />;
      case 'careplan':
        return <ClipboardList className="w-4 h-4 text-[var(--ak-color-primary)]" />;
      default:
        return <Activity className="w-4 h-4 text-[var(--ak-color-text-secondary)]" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--ak-color-text-primary)]/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col bg-white border border-[var(--ak-color-border-subtle)] rounded-xl shadow-2xl overflow-hidden font-sans">
        {/* Header */}
        <div className="px-6 py-4 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[var(--ak-color-primary-soft)] border border-[var(--ak-color-border-subtle)] flex items-center justify-center text-[var(--ak-color-primary)]">
              <Clock className="w-5 h-5 text-[var(--ak-color-primary)]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-[var(--ak-color-text-primary)] font-mono tracking-tight">
                  {profile ? profile.name : 'Loading Patient Profile...'}
                </h2>
                {profile && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[var(--ak-color-primary-soft)] text-[var(--ak-color-primary)] border border-[var(--ak-color-border-subtle)]">
                    {profile.mrn}
                  </span>
                )}
              </div>
              <p className="text-xs text-[var(--ak-color-text-muted)] font-mono">
                {profile
                  ? `${profile.gender.toUpperCase()} • ${profile.age} YRS • DOB: ${profile.birth_date} • ${profile.city}, ${profile.state}`
                  : 'Synthea FHIR R4 Record'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleFetchRawJson}
              className="px-3 py-1.5 text-xs font-mono font-medium rounded-md bg-white border border-[var(--ak-color-border-subtle)] text-[var(--ak-color-text-secondary)] hover:bg-[var(--ak-color-bg-subtle)] transition cursor-pointer flex items-center gap-1.5"
            >
              <FileCode className="w-3.5 h-3.5 text-[var(--ak-color-text-muted)]" />
              <span>{showRawJson ? 'Hide FHIR' : 'View FHIR'}</span>
            </button>

            <button
              onClick={handleAdmitToHospital}
              disabled={isAdmitting}
              className="px-3.5 py-1.5 text-xs font-mono font-bold rounded-md bg-[var(--ak-color-primary)] hover:bg-[var(--ak-color-primary-soft)]0 text-white transition shadow-xs cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
            >
              <BedDouble className="w-3.5 h-3.5" />
              <span>{isAdmitting ? 'Admitting...' : 'Admit to Hospital'}</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 text-[var(--ak-color-text-muted)] hover:text-[var(--ak-color-text-secondary)] rounded-md hover:bg-[var(--ak-color-bg-subtle)] transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Disclaimer Bar */}
        <div className="px-6 py-2 bg-[var(--ak-color-warning-soft)] border-b border-[var(--ak-color-border-subtle)] text-[var(--ak-color-warning)] text-[11px] font-mono flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[var(--ak-color-warning)] shrink-0" />
            <span>
              SYNTHETIC DATA DISCLAIMER: Generated via Synthea FHIR R4. Demonstration and UI testing only.
            </span>
          </div>
          {admitStatus && (
            <span className="font-bold text-[var(--ak-color-success)] bg-[var(--ak-color-success-soft)] px-2 py-0.5 rounded border border-[var(--ak-color-border-subtle)] flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              {admitStatus}
            </span>
          )}
        </div>

        {/* Patient Summary Quick Bar */}
        {profile && (
          <div className="px-6 py-3 bg-white border-b border-[var(--ak-color-border-subtle)] grid grid-cols-2 md:grid-cols-4 gap-4 text-xs shrink-0">
            <div>
              <span className="text-[10px] font-mono text-[var(--ak-color-text-muted)] uppercase tracking-wider block">
                Active Diagnoses
              </span>
              <div className="mt-1 flex flex-wrap gap-1">
                {profile.active_conditions.length > 0 ? (
                  profile.active_conditions.map((c, i) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 rounded bg-[var(--ak-color-warning-soft)] text-[var(--ak-color-warning)] border border-[var(--ak-color-border-subtle)] text-[10px] font-medium"
                    >
                      {c.name}
                    </span>
                  ))
                ) : (
                  <span className="text-[var(--ak-color-text-muted)] italic">None recorded</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-[10px] font-mono text-[var(--ak-color-text-muted)] uppercase tracking-wider block">
                Active Medications
              </span>
              <div className="mt-1 flex flex-wrap gap-1">
                {profile.current_medications.length > 0 ? (
                  profile.current_medications.map((m, i) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 rounded bg-[var(--ak-color-primary-soft)] text-[var(--ak-color-primary)] border border-[var(--ak-color-border-subtle)] text-[10px] font-medium"
                    >
                      {m.name}
                    </span>
                  ))
                ) : (
                  <span className="text-[var(--ak-color-text-muted)] italic">None active</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-[10px] font-mono text-[var(--ak-color-text-muted)] uppercase tracking-wider block">
                Known Allergies
              </span>
              <div className="mt-1 flex flex-wrap gap-1">
                {profile.allergies.length > 0 ? (
                  profile.allergies.map((a, i) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 rounded bg-[var(--ak-color-warning-soft)] text-[var(--ak-color-danger)] border border-[var(--ak-color-border-subtle)] text-[10px] font-medium"
                    >
                      {a.substance} ({a.criticality || 'low'})
                    </span>
                  ))
                ) : (
                  <span className="text-[var(--ak-color-text-muted)] italic">No Known Allergies</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-[10px] font-mono text-[var(--ak-color-text-muted)] uppercase tracking-wider block">
                Latest Baseline Vitals
              </span>
              <div className="mt-1 font-mono text-[11px] text-[var(--ak-color-text-secondary)]">
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
                  <span className="text-[var(--ak-color-text-muted)] italic">Vitals standard</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Timeline Category Filters */}
        <div className="px-6 py-2.5 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] flex items-center gap-1.5 overflow-x-auto shrink-0">
          <span className="text-[10px] font-mono font-bold text-[var(--ak-color-text-muted)] uppercase mr-2">
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
                  ? 'bg-[var(--ak-color-text-primary)] text-white shadow-xs'
                  : 'bg-white border border-[var(--ak-color-border-subtle)] text-[var(--ak-color-text-secondary)] hover:bg-[var(--ak-color-bg-subtle)]'
              }`}
            >
              <span>{label}</span>
              <span
                className={`px-1 rounded-full text-[10px] ${
                  activeFilter === key ? 'bg-[var(--ak-color-text-primary)] text-[var(--ak-color-text-muted)]' : 'bg-[var(--ak-color-bg-subtle)] text-[var(--ak-color-text-muted)]'
                }`}
              >
                {count}
              </span>
            </button>
          ))}
        </div>

        {/* Main Content Area */}
        <div className="flex-1 p-6 overflow-y-auto bg-[var(--ak-color-bg-subtle)]/50">
          {loading ? (
            <div className="py-20 text-center text-[var(--ak-color-text-muted)] font-mono text-sm">
              <Clock className="w-8 h-8 animate-spin mx-auto mb-2 text-[var(--ak-color-primary)]" />
              Loading FHIR R4 clinical timeline...
            </div>
          ) : showRawJson ? (
            <div className="bg-[var(--ak-color-text-primary)] text-[var(--ak-color-text-muted)] p-4 rounded-lg font-mono text-xs overflow-x-auto max-h-[60vh]">
              <pre>{JSON.stringify(rawJson, null, 2)}</pre>
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="py-16 text-center text-[var(--ak-color-text-muted)] font-mono text-xs">
              No clinical events found for this filter category.
            </div>
          ) : (
            <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:border-[var(--ak-color-border-subtle)]">
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
                  <div className="flex-1 bg-white border border-[var(--ak-color-border-subtle)] rounded-lg p-4 shadow-xs hover:border-[var(--ak-color-border-subtle)] transition">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider border ${getEventBadgeStyle(
                            event.category
                          )}`}
                        >
                          {event.category}
                        </span>
                        <h4 className="text-sm font-bold text-[var(--ak-color-text-primary)]">{event.title}</h4>
                      </div>

                      <div className="flex items-center gap-1.5 text-xs text-[var(--ak-color-text-muted)] font-mono">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>{event.display_date}</span>
                      </div>
                    </div>

                    {event.subtitle && (
                      <p className="text-xs text-[var(--ak-color-text-secondary)] font-medium mb-2">{event.subtitle}</p>
                    )}

                    {/* Metadata & Details */}
                    <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-[var(--ak-color-text-muted)] pt-2 border-t border-[var(--ak-color-border-subtle)]">
                      {event.code && (
                        <div className="flex items-center gap-1">
                          <Tag className="w-3 h-3 text-[var(--ak-color-text-muted)]" />
                          <span>
                            Code: <span className="text-[var(--ak-color-text-primary)]">{event.code}</span>
                          </span>
                          {event.system && (
                            <span className="text-[10px] text-[var(--ak-color-text-muted)]">
                              ({event.system.split('/').pop()})
                            </span>
                          )}
                        </div>
                      )}

                      {event.status && (
                        <div className="flex items-center gap-1">
                          <span>
                            Status: <span className="text-[var(--ak-color-text-primary)]">{event.status}</span>
                          </span>
                        </div>
                      )}

                      {event.details?.components && event.details.components.length > 0 && (
                        <div className="w-full flex items-center gap-2 mt-1">
                          {event.details.components.map((c: any, ci: number) => (
                            <span
                              key={ci}
                              className="px-2 py-0.5 rounded bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] text-[var(--ak-color-text-secondary)] text-[10px]"
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
        <div className="px-6 py-3 bg-[var(--ak-color-bg-subtle)] border-t border-[var(--ak-color-border-subtle)] flex items-center justify-between text-xs font-mono text-[var(--ak-color-text-muted)] shrink-0">
          <span>
            Total Events: <strong>{events.length}</strong> • Showing: <strong>{filteredEvents.length}</strong>
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 border-[var(--ak-color-border-subtle)] hover:border-[var(--ak-color-border-subtle)] text-[var(--ak-color-text-primary)] rounded font-medium transition cursor-pointer"
          >
            Close Timeline
          </button>
        </div>
      </div>
    </div>
  );
};
