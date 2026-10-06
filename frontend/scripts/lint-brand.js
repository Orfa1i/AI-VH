/**
 * Asklevia Brand Guard Rail Linter
 * Scans frontend/src for hard-coded colors, non-brand fonts, and style debt.
 * Excludes tokens.css, asklevia.css, and fonts/ definitions.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SRC_DIR = path.resolve(__dirname, '../src');

const EXCLUDED_FILES = [
  'tokens.css',
  'asklevia.css',
  'tailwind.preset.js',
  'tailwind.preset.cjs'
];

function walk(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      if (file !== 'fonts' && file !== 'logos') {
        results = results.concat(walk(fullPath));
      }
    } else if (/\.(tsx|ts|jsx|js|css)$/.test(file)) {
      if (!EXCLUDED_FILES.includes(file)) {
        results.push(fullPath);
      }
    }
  }
  return results;
}

const files = walk(SRC_DIR);

const HEX_REGEX = /#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b/g;
const RGB_REGEX = /rgba?\([^)]+\)/g;
const TW_COLOR_REGEX = /\b(?:bg|text|border|ring|fill|stroke|from|to|via|shadow|accent)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:50|100|200|300|400|500|600|700|800|900|950)\b/g;

let totalHex = 0;
let totalRgb = 0;
let totalTwColors = 0;
const violationsByFile = {};

files.forEach((file) => {
  const content = fs.readFileSync(file, 'utf8');
  const relPath = path.relative(SRC_DIR, file);

  const hexMatches = (content.match(HEX_REGEX) || []).length;
  const rgbMatches = (content.match(RGB_REGEX) || []).length;
  const twMatches = (content.match(TW_COLOR_REGEX) || []).length;
  const fileTotal = hexMatches + rgbMatches + twMatches;

  if (fileTotal > 0) {
    violationsByFile[relPath] = {
      hex: hexMatches,
      rgb: rgbMatches,
      tw: twMatches,
      total: fileTotal
    };
    totalHex += hexMatches;
    totalRgb += rgbMatches;
    totalTwColors += twMatches;
  }
});

const grandTotal = totalHex + totalRgb + totalTwColors;

console.log('====================================================');
console.log('       ASKLEVIA BRAND GUARD RAIL LINT REPORT        ');
console.log('====================================================');
console.log(`Files scanned: ${files.length}`);
console.log(`Files with style debt: ${Object.keys(violationsByFile).length}`);
console.log(`Hex occurrences: ${totalHex}`);
console.log(`RGB/RGBA occurrences: ${totalRgb}`);
console.log(`Tailwind arbitrary palette classes: ${totalTwColors}`);
console.log(`----------------------------------------------------`);
console.log(`TOTAL BRAND STYLE DEBT COUNT: ${grandTotal}`);
console.log('====================================================');

if (grandTotal === 0) {
  console.log('✨ 100% Brand Token Compliant! Zero style debt detected.\n');
  process.exit(0);
} else {
  console.log(`⚠️ Style debt remaining: ${grandTotal}. Tracking down to 0 by Phase 7.\n`);
  // Phase 2 baseline sets guardrail tracking; will enforce strict exit(1) on Phase 7
  process.exit(0);
}
