const { chromium } = require('@playwright/test');
const path = require('path');

async function testModal() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto('http://localhost:5173');
  await page.click('.btn-primary');
  await page.waitForTimeout(1000);

  // Click "Staff Roster" nav button inside #root
  await page.getByRole('button', { name: /Staff Roster/i }).click();
  await page.waitForTimeout(1000);

  // Trigger OPEN_CHAT from window
  await page.evaluate(() => {
    window.postMessage({ type: 'OPEN_CHAT', agentKey: 'im', agentName: 'Dr. Marcus Vance' }, '*');
  });

  // Wait for modal animation
  await page.waitForTimeout(1000);

  const screenshotPath = path.resolve('C:/Users/PCD/.gemini/antigravity-cli/brain/17f22c14-b8f7-4171-b34f-c13b0184026f/chat-consultant-compact.png');
  await page.screenshot({ path: screenshotPath, fullPage: false });
  console.log('Saved screenshot to:', screenshotPath);

  await browser.close();
}

testModal().catch(err => {
  console.error('Screenshot error:', err);
  process.exit(1);
});
