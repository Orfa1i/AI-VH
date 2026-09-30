import React from 'react';
import type { StreamEvent } from './api';
import { encounterStatus } from './departments';

interface PatientCardProps {
  runId: string;
  caseId: string;
  events: StreamEvent[];
  expanded: boolean;
  onToggle: () => void;
}

function reportSummary(events: StreamEvent[]): string | null {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const payload = events[index].payload ?? {};
    const report = payload.report as { patient_summary?: unknown } | undefined;
    if (report !== undefined && typeof report.patient_summary === 'string') {
      return report.patient_summary;
    }
  }
  return null;
}

export const PatientCard: React.FC<PatientCardProps> = ({ runId, caseId, events, expanded, onToggle }) => {
  const status = encounterStatus(events);
  const summary = reportSummary(events);
  return (
    <div className="border border-slate-200 rounded-md overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded ? 'true' : 'false'}
        className="w-full px-3 py-2 text-left cursor-pointer hover:bg-slate-100"
      >
        <span className="block text-xs font-mono font-semibold text-slate-900">{runId}</span>
        <span className="block text-[11px] font-mono text-slate-600">
          {caseId} • {status}
        </span>
      </button>
      {expanded && (
        <div className="px-3 pb-3 space-y-3">
          <section>
            <h4 className="text-[11px] font-mono font-bold uppercase tracking-wide text-slate-900">
              Encounter timeline
            </h4>
            <ol data-testid={`timeline-${runId}`} className="mt-1 space-y-1">
              {events.map((event) => (
                <li key={event.event_id} className="text-xs font-sans text-slate-600">
                  <span className="font-mono text-slate-500">t+{event.sim_time}m</span>{' '}
                  <span data-testid="timeline-action">{event.action}</span>
                </li>
              ))}
            </ol>
          </section>
          <section>
            <h4 className="text-[11px] font-mono font-bold uppercase tracking-wide text-slate-900">
              Agent activity
            </h4>
            <ul data-testid={`activity-${runId}`} className="mt-1 space-y-1">
              {events.map((event) => (
                <li key={event.event_id} className="text-xs font-sans text-slate-600">
                  <span data-testid="activity-actor" className="font-mono text-slate-500">
                    {event.actor}
                  </span>{' '}
                  → {event.action}
                </li>
              ))}
            </ul>
          </section>
          {summary !== null && (
            <section>
              <h4 className="text-[11px] font-mono font-bold uppercase tracking-wide text-slate-900">
                Filed report
              </h4>
              <p className="text-xs text-slate-600 font-sans">{summary}</p>
            </section>
          )}
        </div>
      )}
    </div>
  );
};
