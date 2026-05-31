import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const lightCss = readFileSync('css/theme-supabase-light.css', 'utf8');
const darkCss = readFileSync('css/theme-github-dark.css', 'utf8');
const html = readFileSync('index.html', 'utf8');

test('hidden comparison panels stay hidden when tabs switch sections', () => {
  assert.match(lightCss, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
  assert.match(darkCss, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
});

test('index uses Supabase-inspired light theme by default', () => {
  assert.match(html, /href="css\/theme-supabase-light\.css"/);
  assert.doesNotMatch(html, /href="css\/theme\.css"/);
  assert.doesNotMatch(html, /href="css\/theme-openclaw-light\.css"/);
});

test('fallback GitHub dark theme is preserved', () => {
  assert.match(darkCss, /--bg:\s*#0d1117;/i);
  assert.match(darkCss, /--surface:\s*#161b22;/i);
  assert.match(darkCss, /--surface-raised:\s*#21262d;/i);
  assert.match(darkCss, /--border:\s*#30363d;/i);
  assert.match(darkCss, /--ink:\s*#e6edf3;/i);
  assert.match(darkCss, /--accent:\s*#2f81f7;/i);
});

test('Supabase light theme uses green accent and white cards', () => {
  assert.match(lightCss, /--bg:\s*#f8faf9;/i);
  assert.match(lightCss, /--surface:\s*#ffffff;/i);
  assert.match(lightCss, /--surface-raised:\s*#fbfdfc;/i);
  assert.match(lightCss, /--ink:\s*#111817;/i);
  assert.match(lightCss, /--accent:\s*#3ecf8e;/i);
  assert.match(lightCss, /--focus:\s*#3ecf8e;/i);
  assert.match(lightCss, /--button:\s*#101614;/i);
});

test('Supabase light theme keeps source buttons dark and active tabs green', () => {
  assert.match(lightCss, /\.item__source\s*\{[\s\S]*background:\s*var\(--button\);/);
  assert.match(lightCss, /\.item__source:hover\s*\{[\s\S]*background:\s*var\(--button-hover\);/);
  assert.match(lightCss, /\.tab--active\s*\{[\s\S]*border-color:\s*var\(--accent\);/);
  assert.match(lightCss, /\.tab--active\s*\{[\s\S]*background:\s*var\(--accent-soft\);/);
});
