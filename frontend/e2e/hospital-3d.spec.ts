import { expect, test } from '@playwright/test';

/**
 * 3D hospital scene (presentation only): rooms, avatars driven by the event
 * stream, click-through to the 2D detail view, and performance gates
 * (ui.min_fps = 50, ui.max_load_s = 5 in configs/thresholds.yaml).
 * Seeded demo stream: 1 completed + 1 in-progress encounter.
 */
test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /3d hospital/i }).click();
  await page.getByRole('button', { name: /load 3d scene/i }).click();
});

test('scene loads within budget with all rooms and avatars', async ({ page }) => {
  await expect(page.getByTestId('scene-loading')).toBeHidden({ timeout: 15000 });
  const canvas = page.locator('canvas');
  await expect(canvas).toBeVisible();

  const loadMs: number = await page.evaluate(() => window.__board3d?.loadMs ?? -1);
  expect(loadMs).toBeGreaterThanOrEqual(0);
  expect(loadMs).toBeLessThan(5000);

  for (const room of ['ER', 'Reception', 'Lab', 'Radiology', 'Pharmacy', 'Wards', 'ICU', 'Clinics']) {
    await expect(page.getByTestId(`room-chip-${room}`)).toBeVisible();
  }
  const rooms: Record<string, string> = await page.evaluate(() => window.__board3d?.avatarRooms() ?? {});
  expect(rooms['DEMO-RUN-1']).toBe('Wards');
  expect(rooms['DEMO-RUN-2']).toBe('Lab');
});

test('scene state matches the event log and sustains target fps', async ({ page }) => {
  await expect(page.getByTestId('scene-loading')).toBeHidden({ timeout: 15000 });
  // Let avatar motion and shader compilation settle, then sample sustained fps
  // over six seconds so transient stalls cannot dominate the average.
  await page.waitForTimeout(3000);
  const fps: number = await page.evaluate(async () => {
    await new Promise((resolve) => setTimeout(resolve, 6000));
    return window.__board3d?.fps ?? 0;
  });
  expect(fps).toBeGreaterThanOrEqual(50);

  const rooms: Record<string, string> = await page.evaluate(() => window.__board3d?.avatarRooms() ?? {});
  expect(Object.keys(rooms).sort()).toEqual(['DEMO-RUN-1', 'DEMO-RUN-2']);
});

test('clicking an avatar opens the matching 2D detail view', async ({ page }) => {
  await expect(page.getByTestId('scene-loading')).toBeHidden({ timeout: 15000 });
  await page.waitForTimeout(2500);
  const pos = await page.evaluate(() => window.__board3d?.avatarScreenPos('DEMO-RUN-1'));
  expect(pos).not.toBeNull();
  await page.mouse.click(pos!.x, pos!.y);
  await expect(page.getByTestId('timeline-DEMO-RUN-1')).toBeVisible({ timeout: 5000 });
  await expect(page.getByText('E2E board summary.')).toBeVisible();
});
