import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LeftNotificationDrawer } from '../LeftNotificationDrawer';
import type { HospitalEvent } from '../../../types';

const MOCK_EVENTS: HospitalEvent[] = [
  {
    id: 'EVT-001',
    event_type: 'PATIENT_ARRIVED',
    timestamp: '2026-10-03T12:00:00Z',
    encounter_id: 'ENC-001',
    patient_id: 'PAT-101',
    sender_agent_id: 'triage',
    department: 'RECEPTION',
    payload: { name: 'Sarah Connor' },
    summary: 'Patient Sarah Connor arrived at Emergency Intake with acute dyspnea.',
  },
  {
    id: 'EVT-002',
    event_type: 'CLINICAL_REPORT_GENERATED',
    timestamp: '2026-10-03T12:05:00Z',
    encounter_id: 'ENC-001',
    patient_id: 'PAT-101',
    sender_agent_id: 'attending',
    department: 'EXAMINATION_ROOM_1',
    payload: { diagnosis: 'Acute Heart Failure' },
    summary: 'Clinical Diagnostic Report generated and routed to physician review queue.',
  },
];

describe('LeftNotificationDrawer', () => {
  it('renders the docked notification trigger on the left edge', () => {
    render(<LeftNotificationDrawer events={MOCK_EVENTS} isConnected={true} />);

    expect(screen.getByTitle('Open Hospital Event Notifications')).toBeInTheDocument();
    expect(screen.getByText(/Notifications/i)).toBeInTheDocument();
  });

  it('slides out the drawer when clicking the dock trigger', async () => {
    const user = userEvent.setup();
    render(<LeftNotificationDrawer events={MOCK_EVENTS} isConnected={true} />);

    const trigger = screen.getByTitle('Open Hospital Event Notifications');
    await user.click(trigger);

    expect(screen.getByText('Hospital Event Feed')).toBeInTheDocument();
    expect(screen.getByText('Telemetry Stream Active')).toBeInTheDocument();
    expect(
      screen.getByText(/Patient Sarah Connor arrived at Emergency Intake/i)
    ).toBeInTheDocument();
  });

  it('filters events when clicking category filter pills', async () => {
    const user = userEvent.setup();
    render(<LeftNotificationDrawer events={MOCK_EVENTS} isConnected={true} />);

    await user.click(screen.getByTitle('Open Hospital Event Notifications'));

    const reportsFilter = screen.getByRole('button', { name: 'REPORTS' });
    await user.click(reportsFilter);

    expect(
      screen.getByText(/Clinical Diagnostic Report generated/i)
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/Patient Sarah Connor arrived at Emergency Intake/i)
    ).not.toBeInTheDocument();
  });

  it('calls onNavigateToTab when clicking view report on a report event', async () => {
    const onNavigate = vi.fn();
    const user = userEvent.setup();
    render(
      <LeftNotificationDrawer
        events={MOCK_EVENTS}
        isConnected={true}
        onNavigateToTab={onNavigate}
      />
    );

    await user.click(screen.getByTitle('Open Hospital Event Notifications'));

    const inspectBtn = screen.getByRole('button', {
      name: /Inspect in Clinical Review/i,
    });
    await user.click(inspectBtn);

    expect(onNavigate).toHaveBeenCalledWith('REPORTS');
  });
});
