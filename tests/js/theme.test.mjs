import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync('css/theme.css', 'utf8');

test('hidden comparison panels stay hidden when tabs switch sections', () => {
  assert.match(css, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
});

test('theme uses GitHub dark palette', () => {
  assert.match(css, /--bg:\s*#0d1117;/i);
  assert.match(css, /--surface:\s*#161b22;/i);
  assert.match(css, /--surface-raised:\s*#21262d;/i);
  assert.match(css, /--border:\s*#30363d;/i);
  assert.match(css, /--ink:\s*#e6edf3;/i);
  assert.match(css, /--accent:\s*#2f81f7;/i);
});
