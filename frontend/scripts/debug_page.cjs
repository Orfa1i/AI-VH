const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  await page.goto('http://localhost:5173');
  await page.waitForTimeout(2000);

  await page.screenshot({ path: 'C:/Users/PCD/.gemini/antigravity-cli/brain/17f22c14-b8f7-4171-b34f-c13b0184026f/initial-page.png' });
  console.log('Saved initial-page.png');

  const buttons = await page.locator('button').allInnerTexts();
  console.log('Buttons found on page:', buttons.slice(0, 20));

  await browser.close();
})();
