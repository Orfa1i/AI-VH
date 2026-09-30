import { describe, expect, it, vi } from 'vitest';
import { useState } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { departmentForEvent, DEPARTMENTS, encounterStatus } from '../departments';
import type { StreamEvent } from '../api';
import { DepartmentBoard } from '../DepartmentBoard';
import { PatientCard } from '../PatientCard';

function evt(overrides: Partial<StreamEvent> & { event_id: string }): StreamEvent {
  return {
    run_id: 'run-1',
    sim_time: 0,
    wall_time: '2026-09-30T00:00:00+00:00',
    actor: 'doctor',
    action: 'order_lab',
    payload: {},
    result_ref: null,
    ...overrides,
  };
}

describe('departmentForEvent', () => {
  it('covers all eight departments across a realistic encounter', () => {
    const cases: Array<[string, string, string]> = [
      ['nurse', 'request_vitals', 'ER'],
      ['system', 'advance_clock', 'Reception'],
      ['doctor', 'order_lab', 'Lab'],
      ['lab', 'get_lab_result', 'Lab'],
      ['doctor', 'order_imaging', 'Radiology'],
      ['radiology', 'interpret_imaging', 'Radiology'],
      ['pharmacy', 'request_medication_info', 'Pharmacy'],
      ['doctor', 'consult', 'Clinics'],
      ['doctor', 'submit_report', 'Wards'],
      ['doctor', 'diagnose', 'Wards'],
    ];
    for (const [actor, action, department] of cases) {
      expect(departmentForEvent(actor, action)).toBe(department);
    }
    expect(DEPARTMENTS).toHaveLength(8);
  });

  it('is a pure presentation mapping with no clinical content', () => {
    expect(departmentForEvent('doctor', 'order_lab')).toBe('Lab');
    expect(departmentForEvent('unknown_actor', 'unknown_action')).toBe('Reception');
  });
});

describe('encounterStatus', () => {
  it('derives display status from the event sequence only', () => {
    expect(encounterStatus([])).toBe('Pending');
    expect(encounterStatus([evt({ event_id: 'a', action: 'request_vitals' })])).toBe('In care');
    expect(
      encounterStatus([
        evt({ event_id: 'a', action: 'request_vitals' }),
        evt({ event_id: 'b', action: 'submit_report' }),
      ]),
    ).toBe('Report filed');
  });
});

describe('DepartmentBoard', () => {
  it('renders all departments with counts and selectable patient cards', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const events = [
      evt({ event_id: 'e1', actor: 'nurse', action: 'request_vitals', sim_time: 0 }),
      evt({ event_id: 'e2', actor: 'doctor', action: 'order_lab', sim_time: 5 }),
      evt({ event_id: 'e3', actor: 'doctor', action: 'submit_report', sim_time: 45 }),
    ];
    render(
      <DepartmentBoard
        runs={[{ run_id: 'run-1', case_id: 'CASE-1', events }]}
        selectedRunId={null}
        onSelectRun={onSelect}
        mode="replay"
      />,
    );
    for (const department of DEPARTMENTS) {
      expect(screen.getByText(department, { exact: true })).toBeInTheDocument();
    }
    await user.click(screen.getByRole('button', { name: /run-1/ }));
    expect(onSelect).toHaveBeenCalledWith('run-1');
  });

  it('expands a patient card to timeline, activity feed, and report link', async () => {
    const user = userEvent.setup();
    const events = [
      evt({ event_id: 'e1', actor: 'nurse', action: 'request_vitals', sim_time: 0 }),
      evt({
        event_id: 'e2',
        actor: 'doctor',
        action: 'submit_report',
        sim_time: 45,
        payload: { report: { patient_summary: 'Summary here.' } },
        result_ref: 'rep_abc',
      }),
    ];
    function Harness() {
      const [expanded, setExpanded] = useState(false);
      return (
        <PatientCard
          runId="run-1"
          caseId="CASE-1"
          events={events}
          expanded={expanded}
          onToggle={() => setExpanded((value) => !value)}
        />
      );
    }
    render(<Harness />);
    expect(screen.queryByText('request_vitals')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /run-1/ }));
    expect(screen.getByText('request_vitals')).toBeInTheDocument();
    expect(screen.getByText('submit_report')).toBeInTheDocument();
    expect(screen.getByText(/nurse/)).toBeInTheDocument();
    expect(screen.getByText('Summary here.')).toBeInTheDocument();
  });
});
