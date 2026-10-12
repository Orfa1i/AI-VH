const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('http://localhost:5173/case-room.html');
  await page.waitForLoadState('domcontentloaded');

  // Verify initial sign button state
  const initialText = await page.$eval('#b-sign', el => el.innerText.trim());
  const initialDisabled = await page.$eval('#b-sign', el => el.disabled);
  console.log('Initial Button:', { text: initialText, disabled: initialDisabled });

  // Simulate deliberation completion to reach signoff phase
  await page.evaluate(() => {
    window.__vhState.phase = 'signoff';
    window.__vhState.reportId = 'REP-TEST-001';
    window.__vhSyncUI();
  });

  const readyDisabled = await page.$eval('#b-sign', el => el.disabled);
  console.log('Signoff Phase Enabled:', !readyDisabled);

  // Click #b-sign
  await page.click('#b-sign');
  await page.waitForTimeout(300);

  // Verify button immediately turns green
  const signedState = await page.evaluate(() => {
    const btn = document.querySelector('#b-sign');
    const modal = document.querySelector('#sign-modal');
    const banner = document.querySelector('#signed-banner');
    return {
      text: btn.innerText.trim(),
      disabled: btn.disabled,
      hasSignedClass: btn.classList.contains('is-signed'),
      inlineBg: btn.style.background,
      inlineColor: btn.style.color,
      background: window.getComputedStyle(btn).backgroundColor,
      modalHidden: modal ? modal.hidden : true,
      bannerExists: !!banner,
      isSigned: window.__vhState.isSigned
    };
  });

  console.log('After Click Result:', signedState);

  await browser.close();

  if (signedState.isSigned && signedState.modalHidden && !signedState.bannerExists && signedState.hasSignedClass) {
    console.log('VERIFICATION SUCCESSFUL: Button immediately turned green, modal stayed hidden, no banner/redirect.');
    process.exit(0);
  } else {
    console.error('VERIFICATION FAILED:', signedState);
    process.exit(1);
  }
})();
