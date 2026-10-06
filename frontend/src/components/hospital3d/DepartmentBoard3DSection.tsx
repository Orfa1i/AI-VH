import React, { useCallback, useState } from 'react';
import { Box } from 'lucide-react';
import { fetchEvents, groupByRun } from '../hospital/api';
import type { StreamEvent } from '../hospital/api';
import { DEPARTMENTS } from '../hospital/departments';
import { PatientCard } from '../hospital/PatientCard';
import { Scene3D } from './Scene3D';

const DEFAULT_BASE_URL =
  (import.meta.env.VITE_EVENT_API_URL as string | undefined) ?? 'http://127.0.0.1:8101';

export const DepartmentBoard3DSection: React.FC = () => {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  // Stable callbacks + memoized scene: the shell clock re-renders App every
  // second, and that must not reconcile the canvas tree (frame hitches).
  const handleSelectRun = useCallback(
    (runId: string) => setSelectedRunId(selectedRunId === runId ? null : runId),
    [selectedRunId],
  );
  const handleReady = useCallback(() => setLoading(false), []);

  const loadScene = () => {
    setError(null);
    setSelectedRunId(null);
    setLoading(true);
    fetchEvents(DEFAULT_BASE_URL)
      .then((loadedEvents) => {
        setEvents(loadedEvents);
        setLoaded(true);
      })
      .catch(() => {
        setError('Could not load the event stream.');
        setLoading(false);
      });
  };

  const runs = groupByRun(events);
  const selected = runs.find((run) => run.run_id === selectedRunId) ?? null;

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="p-4 bg-white border border-[var(--ak-color-border-subtle)] rounded-xl shadow-md hud-bracket">
          <div className="flex items-center gap-2 mb-3">
            <Box className="w-4 h-4 text-[var(--ak-color-primary)]" aria-hidden="true" />
            <h1 className="text-sm font-mono font-bold uppercase tracking-wide text-[var(--ak-color-text-primary)]">
              3D hospital
            </h1>
          </div>
          <div className="flex flex-wrap items-end gap-2">
            <button
              type="button"
              onClick={loadScene}
              className="px-4 py-1.5 text-xs font-mono font-bold text-[var(--ak-color-primary)] hover:bg-[var(--ak-color-primary)] text-white rounded-md transition cursor-pointer"
            >
              Load 3D scene
            </button>
          </div>
          {error !== null && (
            <p role="alert" className="mt-2 text-xs font-sans text-[var(--ak-color-danger)]">
              {error}
            </p>
          )}
        </div>

        {loaded && (
          <div className="relative bg-white border border-[var(--ak-color-border-subtle)] rounded-xl shadow-md overflow-hidden">
            <div className="h-[420px]">
              <Scene3D
                events={events}
                selectedRunId={selectedRunId}
                onSelectRun={handleSelectRun}
                onReady={handleReady}
              />
            </div>
            {loading && (
              <div
                data-testid="scene-loading"
                className="absolute inset-0 flex items-center justify-center bg-white/80"
              >
                <p className="text-sm font-mono text-[var(--ak-color-text-secondary)]">Loading 3D hospital…</p>
              </div>
            )}
            <div className="px-4 py-2 border-t border-[var(--ak-color-border-subtle)] flex flex-wrap gap-1.5">
              {DEPARTMENTS.map((department) => (
                <span
                  key={department}
                  data-testid={`room-chip-${department}`}
                  className="px-2 py-0.5 text-[11px] font-mono text-[var(--ak-color-text-secondary)] border border-[var(--ak-color-border-subtle)] rounded-full"
                >
                  {department}
                </span>
              ))}
            </div>
          </div>
        )}

        {selected !== null && (
          <PatientCard
            runId={selected.run_id}
            caseId={selected.case_id}
            events={selected.events}
            expanded
            onToggle={() => setSelectedRunId(null)}
          />
        )}
      </div>
    </div>
  );
};
