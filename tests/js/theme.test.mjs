import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const lightCss = readFileSync('css/theme-supabase-light.css', 'utf8');
const darkCss = readFileSync('css/theme-github-dark.css', 'utf8');
const pixelCss = readFileSync('css/theme-pixel-dark.css', 'utf8');
const html = readFileSync('index.html', 'utf8');

function ruleBody(css, selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = css.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`));
  assert.ok(match, `Missing ${selector} rule`);
  return match[1];
}

function mediaBlockBody(css, query) {
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const startMatch = css.match(new RegExp(`@media\\s*\\(${escaped}\\)\\s*\\{`));
  assert.ok(startMatch, `Missing @media (${query}) block`);

  const start = startMatch.index + startMatch[0].length;
  let depth = 1;
  for (let i = start; i < css.length; i += 1) {
    if (css[i] === '{') depth += 1;
    if (css[i] === '}') depth -= 1;
    if (depth === 0) return css.slice(start, i);
  }
  assert.fail(`Unclosed @media (${query}) block`);
}

function assertResponsiveCardGrid(css) {
  const rangeList = ruleBody(css, '.range-list');
  assert.match(rangeList, /display:\s*grid;/);
  assert.match(rangeList, /grid-template-columns:\s*repeat\(3,\s*minmax\(0,\s*1fr\)\);/);
  assert.match(rangeList, /gap:\s*\.9rem;/);

  const tabletRangeList = ruleBody(mediaBlockBody(css, 'max-width: 959px'), '.range-list');
  assert.match(tabletRangeList, /grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\);/);

  const mobileRangeList = ruleBody(mediaBlockBody(css, 'max-width: 699px'), '.range-list');
  assert.match(mobileRangeList, /grid-template-columns:\s*1fr;/);

  const item = ruleBody(css, '.item');
  assert.match(item, /display:\s*flex;/);
  assert.match(item, /flex-direction:\s*column;/);

  const head = ruleBody(css, '.item__head');
  assert.match(head, /flex-wrap:\s*wrap;/);

  const title = ruleBody(css, '.item__title');
  assert.match(title, /min-width:\s*0;/);
  assert.match(title, /overflow-wrap:\s*anywhere;/);

  const source = ruleBody(css, '.item__source');
  assert.match(source, /align-self:\s*flex-start;/);
  assert.match(source, /margin-top:\s*auto;/);
}

function assertDeltaSummaryIconLayout(css) {
  const summary = ruleBody(css, '.delta-summary');
  assert.match(summary, /display:\s*flex;/);
  assert.match(summary, /align-items:\s*center;/);
  assert.match(summary, /gap:\s*\.85rem;/);

  const icon = ruleBody(css, '.delta-summary__icon');
  assert.match(icon, /width:\s*2\.5rem;/);
  assert.match(icon, /height:\s*2\.5rem;/);
  assert.match(icon, /flex:\s*0 0 2\.5rem;/);
  assert.match(icon, /display:\s*grid;/);
  assert.match(icon, /place-items:\s*center;/);
  assert.match(icon, /--product-icon-bg:/);
  assert.match(icon, /--product-icon-accent:/);
  assert.match(icon, /--product-icon-ink:/);
  assert.match(icon, /--product-icon-muted:/);

  const iconSvg = ruleBody(css, '.delta-summary__icon svg');
  assert.match(iconSvg, /width:\s*100%;/);
  assert.match(iconSvg, /height:\s*100%;/);
  assert.match(iconSvg, /image-rendering:\s*pixelated;/);

  const body = ruleBody(css, '.delta-summary__body');
  assert.match(body, /min-width:\s*0;/);
}

test('hidden comparison panels stay hidden when tabs switch sections', () => {
  assert.match(lightCss, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
  assert.match(darkCss, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
  assert.match(pixelCss, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
});

test('index uses pixel dark theme by default', () => {
  assert.match(html, /href="css\/theme-pixel-dark\.css"/);
  assert.match(html, /var DEFAULT_THEME = 'theme-pixel-dark';/);
  assert.doesNotMatch(html, /href="css\/theme\.css"/);
  assert.doesNotMatch(html, /href="css\/theme-openclaw-light\.css"/);
});

test('delta summary includes product icon host and text wrapper', () => {
  assert.match(html, /<div id="product-icon" class="delta-summary__icon" aria-hidden="true"><\/div>/);
  assert.match(html, /<div class="delta-summary__body">\s*<h2 id="delta-heading">Release delta<\/h2>\s*<p id="delta-subheading"><\/p>\s*<\/div>/);
});

test('theme restoration only loads whitelisted stored values', () => {
  assert.match(html, /var THEMES = \['theme-supabase-light', 'theme-github-dark', 'theme-pixel-dark'\];/);
  assert.match(html, /THEMES\.indexOf\(t\) !== -1 \? t : DEFAULT_THEME/);
  assert.doesNotMatch(html, /if \(t\) document\.getElementById\('themeLink'\)\.href = 'css\/' \+ t \+ '\.css';/);
});

test('theme preference is saved only after explicit button clicks', () => {
  assert.doesNotMatch(html, /function apply\(name\) \{[\s\S]*?localStorage\.setItem\('oracle-diff-theme', name\);[\s\S]*?\}/);
  assert.match(html, /btn\.addEventListener\('click', function \(\) \{[\s\S]*?apply\(btn\.dataset\.theme\);[\s\S]*?localStorage\.setItem\('oracle-diff-theme', btn\.dataset\.theme\);[\s\S]*?\}\);/);
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

test('Supabase light product icon muted color uses stronger contrast token', () => {
  const icon = ruleBody(lightCss, '.delta-summary__icon');
  assert.match(icon, /--product-icon-muted:\s*var\(--muted-strong\);/);
});

test('themes use a responsive equal-height card grid', () => {
  assertResponsiveCardGrid(lightCss);
  assertResponsiveCardGrid(darkCss);
  assertResponsiveCardGrid(pixelCss);
});

test('themes define compact delta summary product icon layout', () => {
  assertDeltaSummaryIconLayout(lightCss);
  assertDeltaSummaryIconLayout(darkCss);
  assertDeltaSummaryIconLayout(pixelCss);
});
