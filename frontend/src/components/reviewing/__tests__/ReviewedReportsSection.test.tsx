import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReviewedReportsSection } from '../ReviewedReportsSection';

const MOCK_REVIEWED_DATA = [
  {
    id: 'REV-001',
    report_id: 'REP-001',
    encounter_id: 'ENC-001',
    physician_name: 'Dr. Marcus Vance, MD, FACP',
    reviewed_at: '2026-10-03T12:00:00Z',
    diagnosis_grade: 'CORRECT',
    reasoning_grade: 'SOUND',
    tests_grade: 'APPROPRIATE',
    treatment_grade: 'SAFE_AND_OPTIMAL',
    overall_score: 5,
    approved: true,
    notes: 'Excellent clinical pathway adherence.',
    corrected_diagnosis: undefined,
    corrected_treatment: undefined,
    report: {
      id: 'REP-001',
      encounter_id: 'ENC-001',
      patient_id: 'PAT-101',
      patient_name: 'John Miller',
      patient_age: 62,
      patient_sex: 'Male',
      chief_complaint: 'Crushing substernal chest pressure',
      primary_diagnosis: 'Acute NSTEMI',
      diagnostic_confidence: 0.95,
      clinical_reasoning: 'Elevated troponin with ischemic changes.',
      treatment_plan: ['Dual antiplatelet therapy', 'Anticoagulation'],
      created_at: '2026-10-03T11:00:00Z',
    },
  },
];

describe('ReviewedReportsSection', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders reviewed reports after fetching data', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => MOCK_REVIEWED_DATA,
    } as Response);

    render(<ReviewedReportsSection />);

    await waitFor(() => {
      expect(screen.getByText('John Miller')).toBeInTheDocument();
    });

    expect(screen.getAllByText(/Acute NSTEMI/)[0]).toBeInTheDocument();
    expect(screen.getByText('5.0 / 5.0 Rating')).toBeInTheDocument();
    expect(screen.getByText('CLINICALLY APPROVED')).toBeInTheDocument();
  });

  it('opens manual fine-tuning console when button is clicked', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => MOCK_REVIEWED_DATA,
    } as Response);

    const user = userEvent.setup();
    render(<ReviewedReportsSection />);

    const trainButton = screen.getByRole('button', { name: /MANUAL MODEL TRAINING/i });
    expect(trainButton).toBeInTheDocument();
    await user.click(trainButton);

    expect(screen.getByText(/Manual Model Fine-Tuning Console/i)).toBeInTheDocument();
    expect(screen.getByText(/SEND DATA FOR MODEL TRAINING/i)).toBeInTheDocument();
  });

  it('shows empty state when no reviewed reports are returned', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    render(<ReviewedReportsSection />);

    await waitFor(() => {
      expect(screen.getByText(/No reviewed cases found/i)).toBeInTheDocument();
    });
  });
});
