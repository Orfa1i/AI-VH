import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * End-to-end doctor review flow against the real feedback API (seeded demo
 * data: 1 flagged + 2 plain reports) and the real Clinical AI OS shell.
 * Demo token matches the FEEDBACK_DEMO_TOKEN webServer seed (dev-only).
 */
const DEMO_TOKEN = 'e2e-demo-token-001';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /doctor review/i }).click();
  await page.getByLabel(/reviewer token/i).fill(DEMO_TOKEN);
  await page.getByRole('button', { name: /^connect$/i }).click();
  await expect(page.getByRole('heading', { name: /review queue/i })).toBeVisible();
});

test('review views pass axe accessibility checks', async ({ page }) => {
  // Runs first: read-only, so the decision tests below still find a full queue.
  // Scoped to <main>: the review UI lives entirely inside it. The shell's
  // sub-header census div sits outside any landmark (pre-existing shell issue,
  // flagged for follow-up; not part of the review views).
  const inMain = new AxeBuilder({ page }).include('main');
  expect((await inMain.analyze()).violations).toEqual([]);

  await page.getByRole('button', { name: /CASE-E2E-FLAGGED/ }).click();
  await expect(page.getByRole('alert')).toBeVisible();
  expect((await inMain.analyze()).violations).toEqual([]);
});

test('flagged report heads the queue and verification flags are prominent', async ({ page }) => {
  const items = page.getByRole('button', { name: /CASE-E2E/ });
  await expect(items).toHaveCount(3);
  await expect(items.first()).toContainText('CASE-E2E-FLAGGED');
  await expect(items.first()).toContainText('FLAGGED');

  await items.first().click();
  const banner = page.getByRole('alert');
  await expect(banner).toContainText(/flagged/i);
  await expect(banner).toContainText(/critical_count/i);
});

test('claim expands to evidence, rates, comments, and approves via keyboard', async ({ page }) => {
  await page.getByRole('button', { name: /CASE-E2E-FLAGGED/ }).click();
  await expect(page.getByText('E2E patient summary.')).toBeVisible();

  const toggle = page.getByRole('button', { name: 'CLM-E2E-01', exact: true });
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  await expect(page.getByText('Troponin rise confirms ACS.')).toBeVisible();

  await page.getByLabel(/rating for CLM-E2E-01/i).selectOption('incorrect');
  await page.getByLabel(/taxonomy for CLM-E2E-01/i).selectOption('wrong_diagnosis');
  await page.getByRole('button', { name: /submit rating for CLM-E2E-01/i }).click();
  await expect(page.getByText(/rating recorded/i)).toBeVisible();

  await page.getByLabel(/add a comment/i).fill('Recheck troponin trend.');
  await page.getByRole('button', { name: /^comment$/i }).click();
  await expect(page.getByText('Recheck troponin trend.')).toBeVisible();

  await page.keyboard.press('a');
  await expect(page.getByText(/report approved/i)).toBeVisible();
});

test('correct flow applies inline edits to the final report', async ({ page }) => {
  await page.getByRole('button', { name: /CASE-E2E-PLAIN-1/ }).click();
  await expect(page.getByText('E2E patient summary.')).toBeVisible();
  await page.keyboard.press('c');
  const summaryBox = page.getByLabel(/edit patient summary/i);
  await summaryBox.clear();
  await summaryBox.fill('Corrected E2E summary.');
  await page.getByRole('button', { name: /submit correction/i }).click();
  const status = page.getByRole('status');
  await expect(status).toContainText(/correction submitted/i);
  await expect(status).toContainText('Corrected E2E summary.');
});

test('reject flow closes the review without a final report', async ({ page }) => {
  await page.getByRole('button', { name: /CASE-E2E-PLAIN-2/ }).click();
  await expect(page.getByText('E2E patient summary.')).toBeVisible();
  await page.keyboard.press('r');
  await expect(page.getByText(/report rejected/i)).toBeVisible();
});
