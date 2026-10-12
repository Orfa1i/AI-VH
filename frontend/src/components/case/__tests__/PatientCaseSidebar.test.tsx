import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PatientCaseSidebar } from '../PatientCaseSidebar';
import type { PatientRecord } from '../../../types';

describe('PatientCaseSidebar Component', () => {
  const samplePatient: PatientRecord = {
    id: 'PAT-4102-ICU',
    mrn: 'VH-4102-ICU',
    name: 'Marcus Holloway',
    age: 58,
    sex: 'Male',
    triage_acuity: 'RESUSCITATION',
    chief_complaint: 'High fevers, rigors, progressive confusion, productive cough with rust-colored sputum.',
    history_of_present_illness: '58-year-old male with 4-day history of worsening cough and fever.',
    past_medical_history: ['COPD', 'Former smoker (35 pack-years)'],
    medications: ['Tiotropium inhaler', 'Albuterol PRN'],
    allergies: ['Penicillin (Anaphylaxis)'],
    baseline_vitals: {
      heart_rate: 128,
      systolic_bp: 78,
      diastolic_bp: 46,
      respiratory_rate: 32,
      temperature_c: 39.4,
      spo2_percent: 88.0,
      pain_score: 4,
    },
    admission_status: 'ADMITTED',
    assigned_department: 'EMERGENCY',
    bed_number: 'ICU-BAY-02',
    admitted_at: new Date().toISOString(),
  };

  it('renders fixed header with patient name, MRN, admission status, and triage acuity', () => {
    render(<PatientCaseSidebar patient={samplePatient} />);

    // Header content
    expect(screen.getByText('Marcus Holloway')).toBeInTheDocument();
    expect(screen.getByText('VH-4102-ICU')).toBeInTheDocument();
    expect(screen.getByText('ADMITTED')).toBeInTheDocument();
    expect(screen.getByText('RESUSCITATION')).toBeInTheDocument();

    // Bed & Demographics
    expect(screen.getByText(/58y · M/)).toBeInTheDocument();
    expect(screen.getByText(/ICU-BAY-02/)).toBeInTheDocument();
  });

  it('renders collapsible accordion sections and supports expand/collapse toggles', () => {
    render(<PatientCaseSidebar patient={samplePatient} />);

    // Section header buttons
    const complaintBtn = screen.getByRole('button', { name: /chief complaint/i });
    const vitalsBtn = screen.getByRole('button', { name: /vital signs & telemetry/i });
    const historyBtn = screen.getByRole('button', { name: /clinical history/i });
    const planBtn = screen.getByRole('button', { name: /active clinical plan/i });

    expect(complaintBtn).toBeInTheDocument();
    expect(vitalsBtn).toBeInTheDocument();
    expect(historyBtn).toBeInTheDocument();
    expect(planBtn).toBeInTheDocument();

    // Complaint is initially open
    expect(complaintBtn).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(/High fevers, rigors/)).toBeInTheDocument();

    // Toggle complaint closed
    fireEvent.click(complaintBtn);
    expect(complaintBtn).toHaveAttribute('aria-expanded', 'false');

    // Toggle complaint open again
    fireEvent.click(complaintBtn);
    expect(complaintBtn).toHaveAttribute('aria-expanded', 'true');
  });

  it('renders global expand all / collapse all toggle button', () => {
    render(<PatientCaseSidebar patient={samplePatient} />);

    // Check if the bulk toggle button exists
    const toggleAllBtn = screen.getByRole('button', { name: /expand all|collapse all/i });
    expect(toggleAllBtn).toBeInTheDocument();

    // Clicking it toggles all sections
    fireEvent.click(toggleAllBtn);
    const complaintBtn = screen.getByRole('button', { name: /chief complaint/i });
    // All should now be either all true or all false
    const stateAfterClick = complaintBtn.getAttribute('aria-expanded');

    fireEvent.click(toggleAllBtn);
    expect(complaintBtn.getAttribute('aria-expanded')).not.toBe(stateAfterClick);
  });

  it('renders responsive vital signs telemetry grid with subtle status indicators', () => {
    render(<PatientCaseSidebar patient={samplePatient} />);

    // Check that vital labels and tabular values are displayed
    expect(screen.getByText('BP')).toBeInTheDocument();
    expect(screen.getByText('78/46')).toBeInTheDocument();

    expect(screen.getByText('Heart Rate')).toBeInTheDocument();
    expect(screen.getByText('128')).toBeInTheDocument();

    expect(screen.getByText('Resp Rate')).toBeInTheDocument();
    expect(screen.getByText('32')).toBeInTheDocument();

    expect(screen.getByText('SpO₂')).toBeInTheDocument();
    expect(screen.getByText('88%')).toBeInTheDocument();

    expect(screen.getByText('Temperature')).toBeInTheDocument();
    expect(screen.getByText('39.4°C')).toBeInTheDocument();

    // SpO2 < 92 and HR >= 120 and SBP <= 90 should have critical badges
    const criticalBadges = screen.getAllByText('critical');
    expect(criticalBadges.length).toBeGreaterThan(0);
  });

  it('applies custom-thin-scrollbar class for sleek aesthetics', () => {
    const { container } = render(<PatientCaseSidebar patient={samplePatient} />);

    const scrollContainer = container.querySelector('.custom-thin-scrollbar');
    expect(scrollContainer).toBeInTheDocument();
  });

  it('allows checking active care plan items and triggers onPlanItemToggle callback', () => {
    const handleToggle = vi.fn();
    render(<PatientCaseSidebar patient={samplePatient} onPlanItemToggle={handleToggle} />);

    const planItem = screen.getByText(/IV Magnesium Sulfate loading/i);
    expect(planItem).toBeInTheDocument();

    fireEvent.click(planItem);
    expect(handleToggle).toHaveBeenCalledWith('mag_sulfate');
  });

  it('handles copy MRN button click with feedback', () => {
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockImplementation(() => Promise.resolve()),
      },
    });

    render(<PatientCaseSidebar patient={samplePatient} />);
    const copyBtn = screen.getByRole('button', { name: /copy medical record number/i });
    expect(copyBtn).toBeInTheDocument();

    fireEvent.click(copyBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('VH-4102-ICU');
  });

  it('renders discharge button when onDischarge callback is provided', () => {
    const handleDischarge = vi.fn();
    render(<PatientCaseSidebar patient={samplePatient} onDischarge={handleDischarge} />);

    const dcBtn = screen.getByRole('button', { name: /discharge patient from ward/i });
    expect(dcBtn).toBeInTheDocument();

    fireEvent.click(dcBtn);
    expect(handleDischarge).toHaveBeenCalledWith('PAT-4102-ICU');
  });
});
