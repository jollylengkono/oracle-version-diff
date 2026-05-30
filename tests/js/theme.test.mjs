import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync('css/theme.css', 'utf8');

test('hidden comparison panels stay hidden when tabs switch sections', () => {
  assert.match(css, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
});
