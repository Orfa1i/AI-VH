import { expect, test } from '@playwright/test';

/**
 * 2D department board driven ONLY by the event stream (Step-46 API, seeded
 * demo runs: one completed encounter, one in-progress). No clinical logic
 * lives in the view: states mirror recorded event actions.
 */

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /department board/i }).click();
  await expect(page.getByRole('heading', { name: /department board/i })).toBeVisible();
});

test('replaying a recorded encounter renders the expected state sequence', async ({ page }) => {
  await page.getByLabel(/stream mode/i).selectOption('replay');
  await page.getByRole('button', { name: /load stream/i }).click();

  // Completed run reaches Wards with a filed report; in-progress run sits in Lab.
  const wards = page.getByTestId('department-Wards');
  await expect(wards.getByRole('button', { name: /DEMO-RUN-1/ })).toBeVisible();
  const lab = page.getByTestId('department-Lab');
  await expect(lab.getByRole('button', { name: /DEMO-RUN-2/ })).toBeVisible();

  // Timeline mirrors the recorded action order exactly.
  await wards.getByRole('button', { name: /DEMO-RUN-1/ }).click();
  const timeline = page.getByTestId('timeline-DEMO-RUN-1');
  await expect(timeline.getByTestId('timeline-action')).toHaveCount(5);
  const actions = await timeline.getByTestId('timeline-action').allTextContents();
  expect(actions).toEqual([
    'request_vitals',
    'order_lab',
    'advance_clock',
    'report_findings',
    'submit_report',
  ]);

  // Agent activity feed names the recorded actors in order.
  const feed = page.getByTestId('activity-DEMO-RUN-1');
  await expect(feed.getByTestId('activity-actor')).toHaveCount(5);
  const actors = await feed.getByTestId('activity-actor').allTextContents();
  expect(actors).toEqual(['nurse', 'doctor', 'system', 'diagnostics', 'doctor']);

  // Report link exposes the submitted report carried by the event.
  await expect(page.getByText('E2E board summary.')).toBeVisible();
});

test('live mode shows the same encounter states as replay mode', async ({ page }) => {
  await page.getByLabel(/stream mode/i).selectOption('live');
  await page.getByRole('button', { name: /load stream/i }).click();
  await expect(page.getByTestId('department-Wards').getByRole('button', { name: /DEMO-RUN-1/ })).toBeVisible();
  await expect(page.getByTestId('department-Lab').getByRole('button', { name: /DEMO-RUN-2/ })).toBeVisible();
  await expect(page.getByText('Mode:')).toContainText('Live');
});
