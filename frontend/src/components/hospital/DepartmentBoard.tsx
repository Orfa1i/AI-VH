import React from 'react';
import type { RunGroup } from './api';
import { DEPARTMENTS, currentDepartment, encounterStatus } from './departments';
import { PatientCard } from './PatientCard';

interface DepartmentBoardProps {
  runs: RunGroup[];
  selectedRunId: string | null;
  onSelectRun: (runId: string) => void;
  mode: 'live' | 'replay';
}

export const DepartmentBoard: React.FC<DepartmentBoardProps> = ({ runs, selectedRunId, onSelectRun, mode }) => {
  const byDepartment = new Map<string, RunGroup[]>();
  for (const run of runs) {
    const department = currentDepartment(run.events);
    if (department === null) continue;
    const list = byDepartment.get(department) ?? [];
    list.push(run);
    byDepartment.set(department, list);
  }

  return (
    <div className="space-y-3">
      <p className="text-[11px] font-mono text-[var(--ak-color-text-secondary)]">
        Mode: <span className="font-bold text-[var(--ak-color-primary)]">{mode === 'live' ? 'Live' : 'Replay'}</span>
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        {DEPARTMENTS.map((department) => {
          const placed = byDepartment.get(department) ?? [];
          return (
            <section
              key={department}
              data-testid={`department-${department}`}
              className="bg-white border border-[var(--ak-color-border-subtle)] rounded-xl shadow-md overflow-hidden"
            >
              <header className="px-3 py-2 border-b border-[var(--ak-color-border-subtle)] flex items-center gap-2">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-[var(--ak-color-text-primary)]">
                  {department}
                </h3>
                <span className="ml-auto text-[11px] font-mono text-[var(--ak-color-text-secondary)]">{placed.length}</span>
              </header>
              <div className="p-2 space-y-2">
                {placed.length === 0 && (
                  <p className="px-1 py-2 text-[11px] font-sans text-[var(--ak-color-text-muted)]">No active encounters.</p>
                )}
                {placed.map((run) => (
                  <div key={run.run_id}>
                    <PatientCard
                      runId={run.run_id}
                      caseId={run.case_id}
                      events={run.events}
                      expanded={run.run_id === selectedRunId}
                      onToggle={() => onSelectRun(run.run_id)}
                    />
                    <p className="sr-only">{encounterStatus(run.events)}</p>
                  </div>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
};
