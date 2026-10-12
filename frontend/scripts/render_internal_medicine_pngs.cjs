const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

async function render() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const svgBase = path.join(__dirname, '../public/assets/svg');
  const targetDir = path.join(__dirname, '../src/assets');

  const circleSvg = fs.readFileSync(path.join(svgBase, 'vh-agent-internal-medicine-circle.svg'), 'utf8');
  const compactSvg = fs.readFileSync(path.join(svgBase, 'vh-agent-internal-medicine-compact.svg'), 'utf8');
  const roundedSvg = fs.readFileSync(path.join(svgBase, 'vh-agent-internal-medicine-rounded.svg'), 'utf8');
  const transparentSvg = fs.readFileSync(path.join(svgBase, 'vh-agent-internal-medicine-transparent.svg'), 'utf8');

  async function renderSvgToPng(svgContent, width, height, outPath) {
    await page.setViewportSize({ width, height });
    const html = `<!DOCTYPE html><html><head><style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body { width: ${width}px; height: ${height}px; background: transparent; overflow: hidden; }
      svg { width: 100%; height: 100%; display: block; }
    </style></head><body>${svgContent}</body></html>`;
    await page.setContent(html);
    const buf = await page.screenshot({ omitBackground: true, type: 'png' });
    fs.writeFileSync(outPath, buf);
    console.log(`Rendered ${path.basename(outPath)} (${width}x${height}, ${buf.length} bytes)`);
  }

  // Circle sizes
  const circleSizes = [1024, 512, 256, 128, 64];
  for (const s of circleSizes) {
    await renderSvgToPng(circleSvg, s, s, path.join(targetDir, `vh-agent-internal-medicine-${s}.png`));
  }
  // Default unnumbered png and dr_marcus_vance.jpg
  await renderSvgToPng(circleSvg, 512, 512, path.join(targetDir, 'vh-agent-internal-medicine.png'));
  await renderSvgToPng(circleSvg, 512, 512, path.join(targetDir, 'dr_marcus_vance.jpg'));

  // Compact sizes
  const compactSizes = [1024, 128, 64, 48, 32];
  for (const s of compactSizes) {
    await renderSvgToPng(compactSvg, s, s, path.join(targetDir, `vh-agent-internal-medicine-compact-${s}.png`));
  }

  // Rounded & transparent 1024
  await renderSvgToPng(roundedSvg, 1024, 1024, path.join(targetDir, 'vh-agent-internal-medicine-rounded-1024.png'));
  await renderSvgToPng(transparentSvg, 1024, 1024, path.join(targetDir, 'vh-agent-internal-medicine-transparent-1024.png'));

  // Also check if public/assets/png exists
  const pubPngDir = path.join(__dirname, '../public/assets/png');
  if (fs.existsSync(pubPngDir)) {
    for (const s of circleSizes) {
      await renderSvgToPng(circleSvg, s, s, path.join(pubPngDir, `vh-agent-internal-medicine-${s}.png`));
    }
  }

  await browser.close();
  console.log('All internal medicine avatar PNGs re-rendered successfully!');
}

render().catch(err => {
  console.error('Render error:', err);
  process.exit(1);
});
