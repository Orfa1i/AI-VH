import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  Button,
  Badge,
  Chip,
  Dialog,
  TextField,
  ProgressBar,
  Tabs,
} from '../index';

describe('Asklevia Core Primitives', () => {
  it('renders Button with correct ak- classes, handles clicks and loading state', () => {
    const handleClick = vi.fn();
    const { rerender } = render(
      <Button variant="primary" onClick={handleClick}>
        Start analysis
      </Button>
    );

    const btn = screen.getByRole('button', { name: /start analysis/i });
    expect(btn.className).toContain('ak-btn');
    expect(btn.className).toContain('ak-btn--primary');
    fireEvent.click(btn);
    expect(handleClick).toHaveBeenCalledTimes(1);

    rerender(
      <Button variant="danger" size="lg" isLoading>
        Start analysis
      </Button>
    );
    const loadingBtn = screen.getByRole('button');
    expect(loadingBtn.className).toContain('ak-btn--danger');
    expect(loadingBtn.className).toContain('ak-btn--lg');
    expect(loadingBtn.className).toContain('is-loading');
    expect(loadingBtn).toBeDisabled();
  });

  it('renders Badge and Chip with strict variants and accessibility', () => {
    render(
      <div>
        <Badge variant="ai">MedGemma Diagnosed</Badge>
        <Badge variant="success" hasDot>
          Active
        </Badge>
        <Chip isSelected={true}>Filter: Cardiology</Chip>
      </div>
    );

    const aiBadge = screen.getByText('MedGemma Diagnosed');
    expect(aiBadge.className).toContain('ak-badge--ai');

    const chip = screen.getByRole('button', { name: /filter: cardiology/i });
    expect(chip.className).toContain('is-selected');
    expect(chip).toHaveAttribute('aria-pressed', 'true');
  });

  it('renders TextField with label, error states, and accessible attributes', () => {
    render(
      <TextField
        label="Patient Name"
        error="Field is required"
        placeholder="Enter name"
      />
    );

    const input = screen.getByPlaceholderText('Enter name');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByRole('alert')).toHaveTextContent('Field is required');
  });

  it('renders Dialog modal with focus management and Esc key dismissal', () => {
    const handleClose = vi.fn();
    const { rerender } = render(
      <Dialog isOpen={true} onClose={handleClose} title="Patient Discharge">
        <p>Discharge confirmation text</p>
      </Dialog>
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Patient Discharge')).toBeInTheDocument();

    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);

    rerender(
      <Dialog isOpen={false} onClose={handleClose} title="Patient Discharge">
        <p>Discharge confirmation text</p>
      </Dialog>
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders ProgressBar with percentage and Neural Spectrum on AI synthesis', () => {
    render(
      <ProgressBar
        label="Diagnostic Synthesis"
        variant="spectrum"
        value={75}
      />
    );

    expect(screen.getByText('Diagnostic Synthesis')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
    const bar = screen.getByRole('progressbar');
    expect(bar.className).toContain('ak-progress--spectrum');
    expect(bar).toHaveAttribute('aria-valuenow', '75');
  });

  it('renders Tabs and handles tab selection', () => {
    const handleChange = vi.fn();
    render(
      <Tabs
        activeId="intake"
        onChange={handleChange}
        tabs={[
          { id: 'intake', label: 'Case Intake', count: 5 },
          { id: 'review', label: 'Doctor Review', count: 2 },
        ]}
      />
    );

    const reviewTab = screen.getByRole('tab', { name: /doctor review/i });
    expect(reviewTab).toHaveAttribute('aria-selected', 'false');
    fireEvent.click(reviewTab);
    expect(handleChange).toHaveBeenCalledWith('review');
  });
});
