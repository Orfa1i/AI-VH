import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { ReportView } from '../ReportView';
import { ReviewQueue } from '../ReviewQueue';
import type { QueueItem, ReportDetail, SessionDetail } from '../api';

const DETAIL: ReportDetail = {
  original_id: 'rep-1',
  case_id: 'CASE-001',
  flagged: true,
  verification: { status: 'flagged', critical_count: 2, reason: 'Unverified troponin claim.' },
  claims: [{ claim_id: 'CLM-DX-01', text: 'ACS confirmed by troponin.' }],
  report: {
    patient_summary: '62yo male with acute substernal pressure.',
    differential: [{ dx: 'Acute Anterior STEMI', likelihood: 'high' }],
    recommendations: [{ text: 'Aspirin 325 mg.' }],
    claims: [{ claim_id: 'CLM-DX-01', text: 'ACS confirmed by troponin.' }],
  },
};

const SESSION: SessionDetail = {
  session: { id: 'ses-1', assignment_id: 'asg-1', decision: null },
  edits: [],
  claim_ratings: [],
  comments: [{ id: 1, author: 'rev-9', text: 'Prior note.' }],
};

const QUEUE: QueueItem[] = [
  { assignment_id: 'asg-1', original_id: 'rep-1', case_id: 'CASE-001', flagged: true, status: 'assigned' },
];

function renderView(overrides: Partial<Parameters<typeof ReportView>[0]> = {}) {
  const props = {
    detail: DETAIL,
    session: SESSION,
    onRateClaim: vi.fn(),
    onAddComment: vi.fn(),
    onDecide: vi.fn(),
    ...overrides,
  };
  return render(<ReportView {...props} />);
}

describe('ReportView', () => {
  it('shows verification flags prominently when flagged', () => {
    renderView();
    const banner = screen.getByRole('alert');
    expect(banner).toHaveTextContent(/flagged/i);
    expect(banner).toHaveTextContent(/Unverified troponin claim/);
  });

  it('expands a claim to reveal its evidence text', async () => {
    const user = userEvent.setup();
    renderView();
    const toggle = screen.getByRole('button', { name: /CLM-DX-01/ });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    await user.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('ACS confirmed by troponin.')).toBeInTheDocument();
  });

  it('submits a per-claim rating with a taxonomy code', async () => {
    const user = userEvent.setup();
    const onRateClaim = vi.fn();
    renderView({ onRateClaim });
    await user.click(screen.getByRole('button', { name: /CLM-DX-01/ }));
    await user.selectOptions(screen.getByLabelText(/rating for CLM-DX-01/i), 'incorrect');
    await user.selectOptions(screen.getByLabelText(/taxonomy for CLM-DX-01/i), 'wrong_diagnosis');
    await user.click(screen.getByRole('button', { name: /submit rating for CLM-DX-01/i }));
    expect(onRateClaim).toHaveBeenCalledWith('CLM-DX-01', 'incorrect', 'wrong_diagnosis');
  });

  it('submits a free-text comment', async () => {
    const user = userEvent.setup();
    const onAddComment = vi.fn();
    renderView({ onAddComment });
    await user.type(screen.getByLabelText(/add a comment/i), 'Needs troponin recheck.');
    await user.click(screen.getByRole('button', { name: /^comment$/i }));
    expect(onAddComment).toHaveBeenCalledWith('Needs troponin recheck.');
  });

  it('supports approve, correct with inline edits, and reject decisions', async () => {
    const user = userEvent.setup();
    const onDecide = vi.fn();
    renderView({ onDecide });
    await user.click(screen.getByRole('button', { name: /^approve$/i }));
    expect(onDecide).toHaveBeenCalledWith('approve', []);

    await user.click(screen.getByRole('button', { name: /^correct$/i }));
    const summaryBox = screen.getByLabelText(/edit patient summary/i);
    await user.clear(summaryBox);
    await user.type(summaryBox, 'Corrected summary.');
    await user.click(screen.getByRole('button', { name: /submit correction/i }));
    expect(onDecide).toHaveBeenCalledWith('correct', [
      { op: 'replace', path: ['patient_summary'], value: 'Corrected summary.' },
    ]);

    await user.click(screen.getByRole('button', { name: /^reject$/i }));
    expect(onDecide).toHaveBeenCalledWith('reject', []);
  });

  it('drives approve/correct/reject from the keyboard (a/c/r)', async () => {
    const user = userEvent.setup();
    const onDecide = vi.fn();
    renderView({ onDecide });
    await user.keyboard('{a}');
    expect(onDecide).toHaveBeenCalledWith('approve', []);
    await user.keyboard('{r}');
    expect(onDecide).toHaveBeenCalledWith('reject', []);
    await user.keyboard('{c}');
    expect(screen.getByLabelText(/edit patient summary/i)).toBeInTheDocument();
  });

  it('ignores shortcuts while typing in a field', async () => {
    const user = userEvent.setup();
    const onDecide = vi.fn();
    renderView({ onDecide });
    const box = screen.getByLabelText(/add a comment/i);
    await user.click(box);
    await user.keyboard('{a}');
    expect(onDecide).not.toHaveBeenCalled();
    expect(box).toHaveValue('a');
  });

  it('passes basic axe accessibility checks on queue and report views', async () => {
    const { container: queueContainer } = render(
      <ReviewQueue items={QUEUE} selectedId={null} onSelect={() => {}} />,
    );
    const queueResults = await axe.run(queueContainer, {
      rules: { 'color-contrast': { enabled: false } },
    });
    expect(queueResults.violations).toEqual([]);

    const { container: reportContainer } = render(
      <ReportView
        detail={DETAIL}
        session={SESSION}
        onRateClaim={() => {}}
        onAddComment={() => {}}
        onDecide={() => {}}
      />,
    );
    const reportResults = await axe.run(reportContainer, {
      rules: { 'color-contrast': { enabled: false } },
    });
    expect(reportResults.violations).toEqual([]);
  });

  it('uses shell tokens only: no ad-hoc colours or fonts in review components', () => {
    const dir = join(process.cwd(), 'src', 'components', 'review');
    const files = readdirSync(dir).filter((f) => f.endsWith('.tsx') || f.endsWith('.ts'));
    expect(files.length).toBeGreaterThan(0);
    for (const file of files) {
      const source = readFileSync(join(dir, file), 'utf-8');
      expect(source, `${file} must not hardcode hex colours`).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
      expect(source, `${file} must not declare fonts`).not.toMatch(/font-family/i);
    }
  });
});
