const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    for (const url of ['http://localhost:5173', 'http://localhost:5173/landing.html']) {
      console.log(`Checking ${url}...`);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });

      // Verify trajectory section
      const journeySec = await page.$('#journey');
      if (!journeySec) throw new Error('#journey section not found on ' + url);

      // Scroll into view so IntersectionObserver sees #rail
      await page.locator('#journey').scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);

      // Verify .node elements
      const nodes = await page.$$('#steps .step .node');
      console.log(`Found ${nodes.length} trajectory nodes`);
      if (nodes.length !== 4) throw new Error(`Expected 4 nodes, got ${nodes.length}`);

      // Check node text contents
      const nodeTexts = await Promise.all(nodes.map(n => n.innerText()));
      console.log('Node text contents:', nodeTexts);

      for (const text of nodeTexts) {
        if (/Gateway/i.test(text)) throw new Error('Found Gateway in node text: ' + text);
        if (/Assessment/i.test(text)) throw new Error('Found Assessment in node text: ' + text);
        if (/Diagnostics/i.test(text)) throw new Error('Found Diagnostics in node text: ' + text);
        if (/Disposition/i.test(text)) throw new Error('Found Disposition in node text: ' + text);
      }
      console.log(`PASS: No Gateway, Assessment, Diagnostics, or Disposition labels on ${url}`);

      // Verify rail and dot exist
      const railDot = await page.$('#rail-dot');
      if (!railDot) throw new Error('#rail-dot element not found');

      // Check dot animation across time
      const initialCx = parseFloat(await railDot.getAttribute('cx') || '0');
      await page.waitForTimeout(1000);
      const movedCx = parseFloat(await railDot.getAttribute('cx') || '0');
      console.log(`rail-dot animation: initial cx=${initialCx.toFixed(2)}, moved cx=${movedCx.toFixed(2)}`);

      if (initialCx === movedCx) {
        throw new Error('rail-dot is not animating across frames on ' + url);
      }
      console.log(`PASS: Dot is moving smoothly along the trajectory line on ${url}`);
    }

    console.log('>>> ALL VERIFICATION CHECKS PASSED FOR BOTH / AND /landing.html! <<<');
  } catch (err) {
    console.error('VERIFICATION FAILED:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
