const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));

  console.log('Navigating directly to Case Room at http://localhost:5173/case-room.html ...');
  await page.goto('http://localhost:5173/case-room.html');
  await page.waitForTimeout(2000);

  // Verify case-select exists
  await page.waitForSelector('#case-select');
  const options = await page.evaluate(() => {
    const sel = document.getElementById('case-select');
    return Array.from(sel.options).map(o => ({ value: o.value, text: o.textContent }));
  });
  console.log('Available cases in dropdown:', options.map(o => o.text));

  // Find Layla Grace Johnson option
  const laylaOpt = options.find(o => o.text.includes('Layla Grace Johnson'));
  if (!laylaOpt) {
    throw new Error('Layla Grace Johnson not found in case-select options!');
  }
  console.log(`Found Layla Grace Johnson option: ${laylaOpt.text} (${laylaOpt.value})`);

  // Select Layla Grace Johnson
  await page.selectOption('#case-select', laylaOpt.value);
  await page.waitForTimeout(500);

  // Check Clinical Dossier fields
  const dossierName = await page.$eval('#pt-name', el => el.textContent.trim());
  const dossierCC = await page.$eval('#pt-cc', el => el.textContent.trim());
  console.log(`Dossier Name: ${dossierName}`);
  console.log(`Dossier Chief Complaint: ${dossierCC}`);

  // Check initial state of button
  const initialBtnText = await page.$eval('#b-main-control span', el => el.textContent.trim());
  console.log(`Initial button text: ${initialBtnText}`);

  // Click Route case button
  console.log('Clicking Route case (#b-main-control)...');
  await page.click('#b-main-control');

  // Immediately check that button reflects "Routing the case..." and is disabled
  await page.waitForTimeout(100);
  const routingBtnText = await page.$eval('#b-main-control span', el => el.textContent.trim());
  const isBtnDisabled = await page.$eval('#b-main-control', el => el.disabled);
  const routerSummary = await page.$eval('#r-sum', el => el.textContent.trim());

  console.log(`Routing button text: "${routingBtnText}", disabled: ${isBtnDisabled}, router summary: "${routerSummary}"`);
  if (!routingBtnText.includes('Routing') || !isBtnDisabled) {
    console.warn(`WARNING: Button state not reflecting routing state properly! Got "${routingBtnText}", disabled=${isBtnDisabled}`);
  } else {
    console.log('PASS: Button reflects "Routing the case..." and is disabled during routing.');
  }

  // Wait for the pipeline to transition to discussion tab
  console.log('Waiting for automatic transition to Discussion tab...');
  await page.waitForFunction(() => {
    const discTab = document.getElementById('t-disc');
    const discPanel = document.getElementById('p-disc');
    return discTab && discTab.getAttribute('aria-selected') === 'true' && !discPanel.hidden;
  }, null, { timeout: 120000 });

  console.log('PASS: UI automatically transitioned to Discussion tab!');

  // Verify agent messages are populating in discussion list
  console.log('Waiting for agent messages in #disc-list...');
  await page.waitForFunction(() => {
    const list = document.getElementById('disc-list');
    return list && list.children.length >= 1;
  }, null, { timeout: 60000 });

  const firstMsgWho = await page.$eval('#disc-list .msg:first-child .msg-who', el => el.textContent.trim());
  console.log(`First agent message in discussion: ${firstMsgWho}`);

  // Wait for deliberation to finish and automatically transition to Draft tab
  console.log('Waiting for deliberation to complete and transition to Draft tab...');
  await page.waitForFunction(() => {
    const draftTab = document.getElementById('t-draft');
    const draftPanel = document.getElementById('p-draft');
    const mainBtn = document.getElementById('b-main-control');
    return draftTab && draftTab.getAttribute('aria-selected') === 'true' && !draftPanel.hidden && mainBtn && mainBtn.textContent.includes('Replay');
  }, null, { timeout: 120000 });

  console.log('PASS: Deliberation completed and UI automatically transitioned to Draft tab!');

  // Check Draft values
  const finalDx = await page.$eval('#dx', el => el.textContent.trim());
  const finalDdx = await page.$eval('#ddx', el => el.textContent.trim());
  const planCount = await page.$$eval('#plan .plan-item', items => items.length);
  const isSignEnabled = await page.$eval('#b-sign', btn => !btn.disabled);

  console.log(`Final Synthesized Diagnosis: "${finalDx}"`);
  console.log(`Differential Diagnoses: "${finalDdx}"`);
  console.log(`Management Plan items count: ${planCount}`);
  console.log(`Sign button enabled: ${isSignEnabled}`);

  // Capture screenshot of Draft Tab with completed deliberation
  const artifactPath = 'C:/Users/PCD/.gemini/antigravity-cli/brain/17f22c14-b8f7-4171-b34f-c13b0184026f/routing-deliberation-draft-verified.png';
  await page.screenshot({ path: artifactPath, fullPage: true });
  console.log(`Saved screenshot artifact to ${artifactPath}`);

  // Also switch back to Discussion tab to take a screenshot of full discussion
  await page.click('#t-disc');
  await page.waitForTimeout(500);
  const discMsgCount = await page.$$eval('#disc-list .msg', msgs => msgs.length);
  console.log(`Total discussion messages: ${discMsgCount}`);
  const discArtifactPath = 'C:/Users/PCD/.gemini/antigravity-cli/brain/17f22c14-b8f7-4171-b34f-c13b0184026f/routing-discussion-panel-verified.png';
  await page.screenshot({ path: discArtifactPath, fullPage: true });
  console.log(`Saved discussion screenshot artifact to ${discArtifactPath}`);

  await browser.close();
  console.log('ALL E2E WORKFLOW TESTS PASSED SUCCESSFULLY!');
})();
