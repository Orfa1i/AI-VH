const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Navigate to main app and activate portal
  await page.goto('http://localhost:5173/#journey');
  await page.waitForTimeout(1000);
  await page.evaluate(() => {
    const landing = document.getElementById('landing-view');
    const root = document.getElementById('root');
    if (landing && root) {
      landing.style.display = 'none';
      root.style.display = 'flex';
    }
  });
  await page.waitForTimeout(1000);

  // Access the Case Room iframe
  const iframeEl = await page.waitForSelector('iframe[title="Virtual Hospital Case Room"]');
  const frame = await iframeEl.contentFrame();

  if (!frame) {
    throw new Error('Case Room iframe contentFrame not accessible');
  }

  // Advance simulation to signoff
  await frame.evaluate(() => {
    window.__vhState.phase = 'signoff';
    window.__vhState.reportId = 'REP-TEST-PORTAL-01';
    window.__vhSyncUI();
  });

  await frame.waitForTimeout(300);

  // Click Review and sign inside the iframe
  const signBtn = await frame.waitForSelector('#b-sign');
  await signBtn.click();
  await frame.waitForTimeout(400);

  // Verify the button inside the iframe is green and completed
  const iframeButtonResult = await frame.evaluate(() => {
    const btn = document.querySelector('#b-sign');
    const modal = document.querySelector('#sign-modal');
    const banner = document.querySelector('#signed-banner');
    return {
      text: btn.innerText.trim(),
      hasSignedClass: btn.classList.contains('is-signed'),
      bg: window.getComputedStyle(btn).backgroundColor,
      modalHidden: modal ? modal.hidden : true,
      bannerExists: !!banner
    };
  });

  console.log('Portal Integration Result:', iframeButtonResult);

  // Verify the user stayed on the Trajectory graph tab (no redirection)
  const currentTab = await page.evaluate(() => {
    const activeNav = document.querySelector('.ak-nav__item[aria-current="page"]');
    return activeNav ? activeNav.innerText.trim() : 'none';
  });

  console.log('Current Active Nav Tab (no redirection):', currentTab);

  await browser.close();

  if (iframeButtonResult.hasSignedClass && iframeButtonResult.bg === 'rgb(5, 150, 105)' && iframeButtonResult.modalHidden && !iframeButtonResult.bannerExists && currentTab.includes('Trajectory graph')) {
    console.log('ALL PORTAL INTEGRATION CHECKS PASSED!');
    process.exit(0);
  } else {
    console.error('PORTAL INTEGRATION FAILED');
    process.exit(1);
  }
})();
