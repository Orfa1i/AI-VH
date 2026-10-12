import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ActiveTrajectoryStepper } from '../ActiveTrajectoryStepper';
import type { BenchmarkCase, HospitalEvent } from '../../../types';

const mockCase: BenchmarkCase = {
  id: 'CASE-101',
  name: 'Robert Miller',
  age: 62,
  sex: 'Male',
  acuity: 'Critical',
  chief_complaint: 'Substernal chest pressure radiating to left arm and jaw.',
  assigned_department: 'CARDIOLOGY',
} as any;

const mockEvent: HospitalEvent = {
  id: 'evt-001',
  encounter_id: 'ENC-101',
  patient_id: 'CASE-101',
  event_type: 'TRIAGE_COMPLETED',
  timestamp: '2026-10-03T18:00:00Z',
  sender_agent_id: 'nurse-01',
  department: 'NURSE_STATION',
  payload: {},
  summary: 'Vital signs acquired and acuity set to ESI 1',
};

describe('ActiveTrajectoryStepper Component', () => {
  it('renders all 4 stages and progress indicator dynamically mapped to activeStep', () => {
    render(
      <ActiveTrajectoryStepper
        activeStep={3}
        isRunning={true}
        currentCase={mockCase}
        latestEvent={mockEvent}
        activeDepartment="LABORATORY"
      />
    );

    expect(screen.getByText('ACTIVE TRAJECTORY SEQUENCE & STATE FLOW')).toBeInTheDocument();
    expect(screen.getByText('75% PROGRESS')).toBeInTheDocument();
    expect(screen.getByText('Clinical Intake & Triage')).toBeInTheDocument();
    expect(screen.getByText('Attending Examination')).toBeInTheDocument();
    expect(screen.getByText('Multidisciplinary Labs')).toBeInTheDocument();
    expect(screen.getByText('Discharge Hub')).toBeInTheDocument();
  });

  it('renders metadata footer with acuity and patient info', () => {
    render(
      <ActiveTrajectoryStepper
        activeStep={3}
        isRunning={false}
        currentCase={mockCase}
        activeDepartment="RECEPTION"
      />
    );

    expect(screen.getByText('PATIENT ACUITY:')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('62yo Male')).toBeInTheDocument();
    expect(screen.getByText('100% GROUNDED')).toBeInTheDocument();
    expect(screen.getByText('M. Vance, MD')).toBeInTheDocument();
  });

  it('reveals popover tooltip HUD on hover', () => {
    render(
      <ActiveTrajectoryStepper
        activeStep={2}
        isRunning={true}
        currentCase={mockCase}
      />
    );

    const triageNode = screen.getByLabelText(/Clinical Intake & Triage/i);
    fireEvent.mouseEnter(triageNode);

    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    expect(screen.getByText(/STAGE 1: GATEWAY/i)).toBeInTheDocument();
    expect(screen.getByText(/Automated ESI Level calculation/i)).toBeInTheDocument();

    fireEvent.mouseLeave(triageNode);
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });

  it('triggers onSelectStage and onOpenDepartmentStation callbacks on click', () => {
    const onSelectStage = vi.fn();
    const onOpenDepartmentStation = vi.fn();

    render(
      <ActiveTrajectoryStepper
        activeStep={1}
        isRunning={true}
        currentCase={mockCase}
        onSelectStage={onSelectStage}
        onOpenDepartmentStation={onOpenDepartmentStation}
      />
    );

    const triageNode = screen.getByLabelText(/Clinical Intake & Triage/i);
    fireEvent.click(triageNode);

    expect(onSelectStage).toHaveBeenCalledWith('INTAKE');
    expect(onOpenDepartmentStation).toHaveBeenCalledWith('NURSE_STATION');
  });
});
