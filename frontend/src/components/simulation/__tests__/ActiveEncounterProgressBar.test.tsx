import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ActiveEncounterProgressBar } from '../ActiveEncounterProgressBar';

describe('ActiveEncounterProgressBar', () => {
  it('does not render when not running and no progress', () => {
    const { container } = render(
      <ActiveEncounterProgressBar isRunning={false} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders actively when running with patient name and milestone indicators', () => {
    render(
      <ActiveEncounterProgressBar
        isRunning={true}
        patientName="Robert Miller"
        encounterId="ENC-TEST-001"
      />
    );

    expect(screen.getByText('Robert Miller')).toBeInTheDocument();
    expect(screen.getByText('ENC-TEST-001')).toBeInTheDocument();
    expect(screen.getByText('Intake & Vitals')).toBeInTheDocument();
    expect(screen.getByText('Nurse Triage')).toBeInTheDocument();
    expect(screen.getByText('Doctor Exam & RAG')).toBeInTheDocument();
    expect(screen.getByText('Labs & Pharmacy')).toBeInTheDocument();
    expect(screen.getByText('Clinical Report')).toBeInTheDocument();
  });

  it('collapses and expands milestones view when chevron is toggled', async () => {
    const user = userEvent.setup();
    render(
      <ActiveEncounterProgressBar
        isRunning={true}
        patientName="Jane Doe"
      />
    );

    const toggleBtn = screen.getByTitle(/Collapse Trajectory/i);
    expect(screen.getByText('Intake & Vitals')).toBeInTheDocument();

    await user.click(toggleBtn);
    expect(screen.queryByText('Intake & Vitals')).not.toBeInTheDocument();

    const expandBtn = screen.getByTitle(/Expand Trajectory/i);
    await user.click(expandBtn);
    expect(screen.getByText('Intake & Vitals')).toBeInTheDocument();
  });
});
