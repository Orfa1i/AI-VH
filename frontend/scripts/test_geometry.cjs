const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://localhost:5173/#portal');
  await page.waitForTimeout(1000);
  const activeTabInPage = await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('button[role="tab"]')).map(t => ({
      text: t.textContent.trim(),
      selected: t.getAttribute('aria-selected') || t.getAttribute('aria-current')
    }));
    const iframe = document.querySelector('iframe');
    let el = iframe;
    const chain = [];
    while (el) {
      chain.push({
        tag: el.tagName,
        id: el.id,
        className: el.className,
        offsetWidth: el.offsetWidth,
        offsetHeight: el.offsetHeight,
        clientWidth: el.clientWidth,
        clientHeight: el.clientHeight,
        computedDisplay: window.getComputedStyle(el).display,
        computedWidth: window.getComputedStyle(el).width,
        computedHeight: window.getComputedStyle(el).height,
      });
      el = el.parentElement;
    }
    return { tabs, chain };
  });
  console.log('Ancestor chain:', JSON.stringify(activeTabInPage.chain, null, 2));
  await browser.close();
})();
