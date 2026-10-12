const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  console.log('--- Step 1: Loading case-room.html ---');
  await page.goto('http://localhost:5173/case-room.html', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1000);

  // 1. Verify Initial State: All 7 agents start in Ready state
  console.log('--- Step 2: Verifying Initial State (All agents in Ready state) ---');
  const agentStatuses = await page.evaluate(() => {
    const seatOrder = ['im', 'ca', 'ne', 'su', 'em', 'ob', 'gy'];
    return seatOrder.map(k => {
      const el = document.getElementById('node-' + k);
      return {
        key: k,
        isStandby: el ? el.classList.contains('standby') : false,
        statusText: el ? el.querySelector('.st')?.textContent?.trim() : null
      };
    });
  });

  console.log('Agent initial statuses:', JSON.stringify(agentStatuses));
  for (const a of agentStatuses) {
    if (a.isStandby) {
      throw new Error(`FAIL: Agent ${a.key} started in standby! Expected Ready.`);
    }
    if (a.statusText !== 'Ready') {
      throw new Error(`FAIL: Agent ${a.key} status text is "${a.statusText}", expected "Ready".`);
    }
  }
  console.log('PASS: All 7 agents verified in Ready state on initial load.');

  // 2. Verify Router Cards before routing
  const routerTags = await page.evaluate(() => {
    const tags = Array.from(document.querySelectorAll('#rcols .rc .tag'));
    return tags.map(t => t.textContent.trim());
  });
  console.log('Router initial tags:', routerTags);
  const allReadyTags = routerTags.every(t => t === 'Ready');
  if (!allReadyTags) {
    throw new Error('FAIL: Not all router cards display "Ready" tag before routing!');
  }
  console.log('PASS: Router cards correctly display Ready indicators before routing execution.');

  // 3. Verify Routing Execution: Click "Route case"
  console.log('--- Step 3: Triggering Routing Execution ---');
  await page.click('#b-main-control');

  // Wait for review/deliberation phase to start (takes ~1.2s for visual routing delay)
  await page.waitForFunction(() => {
    return document.querySelectorAll('#rcols .rc.standby').length > 0;
  }, { timeout: 15000 });

  const postRoutingAgents = await page.evaluate(() => {
    const seatOrder = ['im', 'ca', 'ne', 'su', 'em', 'ob', 'gy'];
    return seatOrder.map(k => {
      const el = document.getElementById('node-' + k);
      return {
        key: k,
        isStandby: el ? el.classList.contains('standby') : false,
        statusText: el ? el.querySelector('.st')?.textContent?.trim() : null
      };
    });
  });

  const activeAgents = postRoutingAgents.filter(a => !a.isStandby);
  const standbyAgents = postRoutingAgents.filter(a => a.isStandby);

  console.log(`Active agents after routing (${activeAgents.length}):`, activeAgents.map(a => a.key));
  console.log(`Standby agents after routing (${standbyAgents.length}):`, standbyAgents.map(a => a.key));

  if (activeAgents.length === 0) {
    throw new Error('FAIL: No agents remained active after routing!');
  }
  if (standbyAgents.length === 0) {
    throw new Error('FAIL: No agents were shifted to Standby after routing!');
  }
  console.log('PASS: Routing execution correctly partitioned active vs standby specialists.');

  // 4. Verify Dynamic Handoff: Trigger referral event
  console.log('--- Step 4: Testing Dynamic Handoff on Standby Specialist ---');
  const targetSpecialist = standbyAgents[0].key;
  console.log(`Simulating referral targeting standby specialist: ${targetSpecialist}`);

  const handoffResult = await page.evaluate((targetKey) => {
    const ev = {
      who: 'ob',
      to: targetKey,
      kind: 'referral',
      short: `REFERRAL: Requesting consult with ${targetKey.toUpperCase()}`,
      detail: 'Referral for urgent assistance.',
      voice: 'Requesting consultation.'
    };
    // Call handleDynamicHandoff with the referral event
    if (typeof handleDynamicHandoff === 'function') {
      handleDynamicHandoff(ev);
    }
    const node = document.getElementById('node-' + targetKey);
    return {
      isStandby: node ? node.classList.contains('standby') : true,
      hasPulseReady: node ? node.classList.contains('pulse-ready') : false,
      statusText: node ? node.querySelector('.st')?.textContent?.trim() : null,
      cardStandby: document.querySelector(`.rc[aria-label*="${targetKey}"]`)?.classList.contains('standby')
    };
  }, targetSpecialist);

  console.log('Handoff result on target specialist:', JSON.stringify(handoffResult));
  if (handoffResult.isStandby) {
    throw new Error(`FAIL: Target specialist ${targetSpecialist} still in standby after referral!`);
  }
  if (handoffResult.statusText !== 'Ready') {
    throw new Error(`FAIL: Target specialist status is "${handoffResult.statusText}", expected "Ready".`);
  }
  console.log(`PASS: Dynamic Handoff successfully awakened ${targetSpecialist} to Ready status to assist!`);

  console.log('\n>>> ALL 4 FRONTEND LIFECYCLE TESTS VERIFIED SUCCESSFULLY! <<<\n');
  await browser.close();
})();
