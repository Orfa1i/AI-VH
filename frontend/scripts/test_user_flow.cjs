const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));

  console.log('Navigating to http://localhost:5173/#portal ...');
  await page.goto('http://localhost:5173/#portal');
  await page.waitForTimeout(1000);

  // Ensure root is displayed
  await page.evaluate(() => {
    const root = document.getElementById('root');
    const landing = document.getElementById('landing-view');
    if (root && landing) {
      landing.style.display = 'none';
      root.style.display = 'flex';
    }
  });
  await page.waitForTimeout(1000);

  // We are on INTAKE tab by default. Look for the iframe.
  const iframeHandle = await page.$('iframe[title="Virtual Hospital Case Intake"]');
  if (!iframeHandle) {
    console.error('Intake iframe not found!');
    await browser.close();
    return;
  }
  const frame = await iframeHandle.contentFrame();
  console.log('Intake iframe loaded. Finding Synthea patients...');

  await frame.waitForSelector('.pt');
  const patientCount = await frame.$$eval('.pt', pts => pts.length);
  console.log(`Found ${patientCount} Synthea patient cards in intake iframe.`);

  // Find an unadmitted patient card
  const unadmittedCards = await frame.$$('.pt:not(.admitted)');
  console.log(`Found ${unadmittedCards.length} unadmitted cards.`);
  if (unadmittedCards.length > 0) {
    const firstUnadmitted = unadmittedCards[0];
    const name = await firstUnadmitted.$eval('h2', el => el.textContent.trim());
    console.log(`Attempting to admit patient: ${name}`);
    const btn = await firstUnadmitted.$('button.admit');
    await btn.click();
    await page.waitForTimeout(2500);
  }

  // Now click on Trajectory graph / Case Room tab in the top navigation of the main React app
  console.log('Clicking Journey / Case Room tab in React app...');
  const journeyNavBtn = await page.$('nav button:has-text("Trajectory")');
  if (journeyNavBtn) {
    await journeyNavBtn.click();
  }

  await page.waitForTimeout(3000);

  // Now we should be on JOURNEY tab, which has HospitalFlowDiagram iframe
  const caseRoomIframeHandle = await page.$('iframe[title="Virtual Hospital Case Room"]');
  if (!caseRoomIframeHandle) {
    console.error('Case Room iframe not found!');
    await browser.close();
    return;
  }
  const caseRoomFrame = await caseRoomIframeHandle.contentFrame();
  await caseRoomFrame.waitForSelector('#case-select');

  const options = await caseRoomFrame.evaluate(() => {
    const sel = document.getElementById('case-select');
    return Array.from(sel.options).map(o => ({ value: o.value, text: o.textContent }));
  });

  console.log('Options in Case Room dropdown after admission:');
  console.log(JSON.stringify(options, null, 2));

  // Take screenshot of case-select and dossier sidebar
  const artifactPath = 'C:/Users/PCD/.gemini/antigravity-cli/brain/17f22c14-b8f7-4171-b34f-c13b0184026f/synthea-admission-case-room.png';
  await page.screenshot({ path: artifactPath, fullPage: true });
  console.log(`Saved screenshot artifact to ${artifactPath}`);

  await browser.close();
})();
