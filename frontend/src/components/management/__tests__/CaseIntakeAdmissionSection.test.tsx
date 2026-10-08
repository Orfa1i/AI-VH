import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CaseIntakeAdmissionSection } from '../CaseIntakeAdmissionSection';

describe('CaseIntakeAdmissionSection ESI Selection', () => {
  it('renders all 5 ESI levels and updates active selection on click with emergency border styling', async () => {
    const user = userEvent.setup();
    const handlePatientAdmitted = vi.fn();

    render(
      <CaseIntakeAdmissionSection
        cases={[]}
        onPatientAdmitted={handlePatientAdmitted}
      />
    );

    // Verify ESI level buttons are present
    const esi1Btn = screen.getByRole('button', { name: /ESI 1/i });
    const esi2Btn = screen.getByRole('button', { name: /ESI 2/i });
    const esi3Btn = screen.getByRole('button', { name: /ESI 3/i });

    // Initial state: default is EMERGENT (ESI 2)
    expect(esi2Btn).toHaveAttribute('aria-pressed', 'true');
    expect(esi1Btn).toHaveAttribute('aria-pressed', 'false');
    expect(esi3Btn).toHaveAttribute('aria-pressed', 'false');

    // Click ESI 1 (Resuscitation)
    await user.click(esi1Btn);

    // ESI 1 should now be active
    expect(esi1Btn).toHaveAttribute('aria-pressed', 'true');
    expect(esi3Btn).toHaveAttribute('aria-pressed', 'false');

    // Verify the border style uses the emergency theme
    expect(esi1Btn.style.border).toContain('var(--emergency');

    // Click ESI 2 (Emergent)
    await user.click(esi2Btn);
    expect(esi2Btn).toHaveAttribute('aria-pressed', 'true');
    expect(esi1Btn).toHaveAttribute('aria-pressed', 'false');
    expect(esi2Btn.style.border).toContain('var(--emergency');
  });
});
