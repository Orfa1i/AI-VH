import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReviewQueue } from '../ReviewQueue';
import type { QueueItem } from '../api';

const ITEMS: QueueItem[] = [
  { assignment_id: 'asg-1', original_id: 'rep-1', case_id: 'CASE-001', flagged: true, status: 'assigned' },
  { assignment_id: 'asg-2', original_id: 'rep-2', case_id: 'CASE-002', flagged: false, status: 'assigned' },
];

describe('ReviewQueue', () => {
  it('lists reports with flagged badges on flagged items only', () => {
    render(<ReviewQueue items={ITEMS} selectedId={null} onSelect={() => {}} />);
    expect(screen.getByText('CASE-001')).toBeInTheDocument();
    expect(screen.getByText('CASE-002')).toBeInTheDocument();
    const badges = screen.getAllByText('FLAGGED');
    expect(badges).toHaveLength(1);
  });

  it('shows an empty state when the queue is empty', () => {
    render(<ReviewQueue items={[]} selectedId={null} onSelect={() => {}} />);
    expect(screen.getByText(/no reports awaiting review/i)).toBeInTheDocument();
  });

  it('notifies selection with the original id', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<ReviewQueue items={ITEMS} selectedId={null} onSelect={onSelect} />);
    await user.click(screen.getByRole('button', { name: /CASE-002/ }));
    expect(onSelect).toHaveBeenCalledWith('rep-2');
  });

  it('marks the selected report with aria-current', () => {
    render(<ReviewQueue items={ITEMS} selectedId="rep-1" onSelect={() => {}} />);
    expect(screen.getByRole('button', { name: /CASE-001/ })).toHaveAttribute('aria-current', 'true');
  });
});
