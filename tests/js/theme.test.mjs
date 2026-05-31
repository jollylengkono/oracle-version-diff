import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const lightCss = readFileSync('css/theme-openclaw-light.css', 'utf8');
const darkCss = readFileSync('css/theme-github-dark.css', 'utf8');
const html = readFileSync('index.html', 'utf8');

test('hidden comparison panels stay hidden when tabs switch sections', () => {
  assert.match(lightCss, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
  assert.match(darkCss, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
});

test('index uses OpenClaw-inspired light theme by default', () => {
  assert.match(html, /href="css\/theme-openclaw-light\.css"/);
  assert.doesNotMatch(html, /href="css\/theme\.css"/);
});

test('fallback GitHub dark theme is preserved', () => {
  assert.match(darkCss, /--bg:\s*#0d1117;/i);
  assert.match(darkCss, /--surface:\s*#161b22;/i);
  assert.match(darkCss, /--surface-raised:\s*#21262d;/i);
  assert.match(darkCss, /--border:\s*#30363d;/i);
  assert.match(darkCss, /--ink:\s*#e6edf3;/i);
  assert.match(darkCss, /--accent:\s*#2f81f7;/i);
});

test('OpenClaw light theme uses warm light cards and dark source buttons', () => {
  assert.match(lightCss, /--bg:\s*#fbfaf6;/i);
  assert.match(lightCss, /--surface:\s*#ffffff;/i);
  assert.match(lightCss, /--ink:\s*#111827;/i);
  assert.match(lightCss, /--button:\s*#1f2937;/i);
});
