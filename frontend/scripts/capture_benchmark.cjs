const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  
  console.log('Navigating to http://localhost:5173...');
  await page.goto('http://localhost:5173');
  await page.waitForTimeout(1500);

  // If on landing page, click "Enter Virtual Hospital Demo"
  const enterBtn = page.locator('button:has-text("Enter Virtual Hospital Demo")').first();
  if (await enterBtn.count() > 0 && await enterBtn.isVisible()) {
    console.log('Clicking Enter Virtual Hospital Demo...');
    await enterBtn.click();
    await page.waitForTimeout(1000);
  }

  // Click on the Policy Benchmark tab
  console.log('Finding and clicking Policy Benchmark tab...');
  const benchmarkTab = page.locator('button:has-text("Policy Benchmark")').first();
  await benchmarkTab.click();
  console.log('Clicked Policy Benchmark tab, waiting for render...');
  await page.waitForTimeout(2000);

  // Capture Overview screenshot
  const screenshot1 = 'C:/Users/PCD/.gemini/antigravity-cli/brain/17f22c14-b8f7-4171-b34f-c13b0184026f/policy-benchmark-optimized.png';
  await page.screenshot({ path: screenshot1 });
  console.log('Saved:', screenshot1);

  // Click on the Reviewed Cohort Data Flow tab
  const cohortTab = page.locator('button:has-text("Reviewed Cohort Data Flow")').first();
  if (await cohortTab.count() > 0 && await cohortTab.isVisible()) {
    console.log('Clicking Reviewed Cohort Data Flow tab...');
    await cohortTab.click();
    await page.waitForTimeout(1000);
    const screenshot2 = 'C:/Users/PCD/.gemini/antigravity-cli/brain/17f22c14-b8f7-4171-b34f-c13b0184026f/policy-benchmark-reviewed-cohort.png';
    await page.screenshot({ path: screenshot2 });
    console.log('Saved:', screenshot2);
  }

  // Click on the Case Head-to-Head tab
  const casesTab = page.locator('button:has-text("Case Head-to-Head")').first();
  if (await casesTab.count() > 0 && await casesTab.isVisible()) {
    console.log('Clicking Case Head-to-Head tab...');
    await casesTab.click();
    await page.waitForTimeout(1000);
    const screenshot3 = 'C:/Users/PCD/.gemini/antigravity-cli/brain/17f22c14-b8f7-4171-b34f-c13b0184026f/policy-benchmark-cases-drilldown.png';
    await page.screenshot({ path: screenshot3 });
    console.log('Saved:', screenshot3);
  }

  // Click on Live GPU Inference tab
  const liveTab = page.locator('button:has-text("Live GPU Inference")').first();
  if (await liveTab.count() > 0 && await liveTab.isVisible()) {
    console.log('Clicking Live GPU Inference tab...');
    await liveTab.click();
    await page.waitForTimeout(1000);
    const screenshot4 = 'C:/Users/PCD/.gemini/antigravity-cli/brain/17f22c14-b8f7-4171-b34f-c13b0184026f/policy-benchmark-live-inference.png';
    await page.screenshot({ path: screenshot4 });
    console.log('Saved:', screenshot4);
  }

  await browser.close();
  console.log('All screenshots captured successfully.');
})();
