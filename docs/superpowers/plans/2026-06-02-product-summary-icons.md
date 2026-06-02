# Product Summary Icons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add compact original pixelated SVG product badges to the left side of the release delta summary, changing with the selected product.

**Architecture:** Product icons live in a small `js/productIcons.js` helper that returns deterministic inline SVG strings by product ID, with a generic fallback. `js/app.js` updates a dedicated summary icon host during the existing `refresh()` path. The three theme stylesheets provide a compact flex layout and theme-aware SVG color variables.

**Tech Stack:** Vanilla HTML, CSS, ES modules, Node.js `node:test`.

---

## File Structure

- Create: `js/productIcons.js`
  - Responsibility: Resolve product IDs to original inline SVG markup.
- Create: `tests/js/productIcons.test.mjs`
  - Responsibility: Unit-test known product icon markup, fallback behavior, and no external image references.
- Modify: `index.html`
  - Responsibility: Add the summary icon host and text wrapper.
- Modify: `js/app.js`
  - Responsibility: Import the helper and update the icon during summary refresh.
- Modify: `tests/js/theme.test.mjs`
  - Responsibility: Static tests for summary icon DOM and theme CSS layout contracts.
- Modify: `css/theme-pixel-dark.css`
  - Responsibility: Summary icon layout and Pixel Dark icon colors.
- Modify: `css/theme-supabase-light.css`
  - Responsibility: Summary icon layout and Supabase Light icon colors.
- Modify: `css/theme-github-dark.css`
  - Responsibility: Summary icon layout and GitHub Dark icon colors.

---

### Task 1: Product Icon Helper

**Files:**
- Create: `tests/js/productIcons.test.mjs`
- Create: `js/productIcons.js`

- [ ] **Step 1: Write the failing product icon helper tests**

Create `tests/js/productIcons.test.mjs`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { productIconSvg } from '../../js/productIcons.js';

const PRODUCT_IDS = [
  'oracle-database',
  'oracle-weblogic-server',
  'oracle-goldengate'
];

test('productIconSvg returns original inline SVG for known products', () => {
  PRODUCT_IDS.forEach((productId) => {
    const svg = productIconSvg(productId);

    assert.match(svg, /<svg[^>]+viewBox="0 0 32 32"/);
    assert.match(svg, new RegExp(`data-product-icon="${productId}"`));
    assert.match(svg, /class="product-icon-svg product-icon-svg--/);
    assert.match(svg, /shape-rendering="crispEdges"/);
    assert.doesNotMatch(svg, /<image|href=|https?:\/\//);
  });
});

test('productIconSvg uses concrete product metaphors', () => {
  assert.match(productIconSvg('oracle-database'), /product-icon-svg--database/);
  assert.match(productIconSvg('oracle-weblogic-server'), /product-icon-svg--weblogic/);
  assert.match(productIconSvg('oracle-goldengate'), /product-icon-svg--goldengate/);
});

test('productIconSvg returns fallback SVG for unknown products', () => {
  const svg = productIconSvg('unknown-product');

  assert.match(svg, /data-product-icon="default"/);
  assert.match(svg, /product-icon-svg--default/);
  assert.match(svg, /<svg[^>]+viewBox="0 0 32 32"/);
});
```

- [ ] **Step 2: Run the helper tests to verify they fail**

Run:

```bash
node --test tests/js/productIcons.test.mjs
```

Expected: FAIL because `../../js/productIcons.js` does not exist.

- [ ] **Step 3: Create the product icon helper**

Create `js/productIcons.js`:

```js
const ICONS = {
  'oracle-database': `<svg class="product-icon-svg product-icon-svg--database" data-product-icon="oracle-database" viewBox="0 0 32 32" width="40" height="40" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
  <rect width="32" height="32" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="7" y="5" width="18" height="4" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="5" y="9" width="22" height="5" fill="var(--product-icon-ink, #f0e2e2)"/>
  <rect x="7" y="14" width="18" height="9" fill="var(--product-icon-muted, #7a4d5e)"/>
  <rect x="5" y="23" width="22" height="5" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="9" y="16" width="14" height="2" fill="var(--product-icon-bg, #160f17)" opacity=".45"/>
  <rect x="9" y="20" width="14" height="2" fill="var(--product-icon-bg, #160f17)" opacity=".45"/>
</svg>`,
  'oracle-weblogic-server': `<svg class="product-icon-svg product-icon-svg--weblogic" data-product-icon="oracle-weblogic-server" viewBox="0 0 32 32" width="40" height="40" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
  <rect width="32" height="32" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="6" y="5" width="20" height="6" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="6" y="13" width="20" height="6" fill="var(--product-icon-muted, #7a4d5e)"/>
  <rect x="6" y="21" width="20" height="6" fill="var(--product-icon-ink, #f0e2e2)"/>
  <rect x="9" y="7" width="3" height="2" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="9" y="15" width="3" height="2" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="9" y="23" width="3" height="2" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="19" y="7" width="3" height="2" fill="var(--product-icon-ink, #f0e2e2)"/>
  <rect x="19" y="15" width="3" height="2" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="19" y="23" width="3" height="2" fill="var(--product-icon-accent, #e8001b)"/>
</svg>`,
  'oracle-goldengate': `<svg class="product-icon-svg product-icon-svg--goldengate" data-product-icon="oracle-goldengate" viewBox="0 0 32 32" width="40" height="40" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
  <rect width="32" height="32" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="4" y="12" width="8" height="8" fill="var(--product-icon-ink, #f0e2e2)"/>
  <rect x="20" y="12" width="8" height="8" fill="var(--product-icon-ink, #f0e2e2)"/>
  <rect x="11" y="14" width="10" height="4" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="14" y="9" width="4" height="14" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="7" y="15" width="2" height="2" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="23" y="15" width="2" height="2" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="14" y="14" width="4" height="4" fill="var(--product-icon-muted, #7a4d5e)"/>
</svg>`
};

const FALLBACK_ICON = `<svg class="product-icon-svg product-icon-svg--default" data-product-icon="default" viewBox="0 0 32 32" width="40" height="40" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
  <rect width="32" height="32" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="8" y="8" width="16" height="16" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="12" y="12" width="8" height="8" fill="var(--product-icon-ink, #f0e2e2)"/>
</svg>`;

export function productIconSvg(productId) {
  return ICONS[productId] || FALLBACK_ICON;
}
```

- [ ] **Step 4: Run helper tests to verify they pass**

Run:

```bash
node --test tests/js/productIcons.test.mjs
```

Expected: PASS with 3 product icon helper tests.

- [ ] **Step 5: Commit the helper**

Run:

```bash
git add js/productIcons.js tests/js/productIcons.test.mjs
git commit -m "feat: add product icon svg helper"
```

Expected: a commit containing only the helper and helper tests.

---

### Task 2: Summary DOM and Runtime Wiring

**Files:**
- Modify: `index.html`
- Modify: `js/app.js`
- Modify: `tests/js/theme.test.mjs`

- [ ] **Step 1: Add failing static DOM tests**

In `tests/js/theme.test.mjs`, add this test after `index uses pixel dark theme by default`:

```js
test('delta summary includes product icon host and text wrapper', () => {
  assert.match(html, /<div id="product-icon" class="delta-summary__icon" aria-hidden="true"><\/div>/);
  assert.match(html, /<div class="delta-summary__body">\s*<h2 id="delta-heading">Release delta<\/h2>\s*<p id="delta-subheading"><\/p>\s*<\/div>/);
});
```

- [ ] **Step 2: Run the static DOM test to verify it fails**

Run:

```bash
npm test
```

Expected: FAIL in `tests/js/theme.test.mjs` because `index.html` does not contain the icon host or summary body wrapper yet.

- [ ] **Step 3: Update the summary markup**

In `index.html`, replace:

```html
<section class="delta-summary" aria-live="polite">
  <h2 id="delta-heading">Release delta</h2>
  <p id="delta-subheading"></p>
</section>
```

with:

```html
<section class="delta-summary" aria-live="polite">
  <div id="product-icon" class="delta-summary__icon" aria-hidden="true"></div>
  <div class="delta-summary__body">
    <h2 id="delta-heading">Release delta</h2>
    <p id="delta-subheading"></p>
  </div>
</section>
```

- [ ] **Step 4: Wire the icon helper into app refresh**

In `js/app.js`, add this import:

```js
import { productIconSvg } from './productIcons.js';
```

Then, in `main()`, after:

```js
const deltaSubheading = document.getElementById('delta-subheading');
```

add:

```js
const productIcon = document.getElementById('product-icon');
```

Then, inside `refresh()`, after the selected `product` is resolved:

```js
const product = index.products.find(p => p.id === productSel.value) || index.products[0];
```

add:

```js
productIcon.innerHTML = productIconSvg(product.id);
```

- [ ] **Step 5: Run JavaScript tests**

Run:

```bash
npm test
```

Expected: PASS with all JavaScript tests.

- [ ] **Step 6: Commit DOM and runtime wiring**

Run:

```bash
git add index.html js/app.js tests/js/theme.test.mjs
git commit -m "feat: render product icon in delta summary"
```

Expected: a commit containing only summary markup, app wiring, and the static DOM test.

---

### Task 3: Theme Styling for Compact Product Badges

**Files:**
- Modify: `tests/js/theme.test.mjs`
- Modify: `css/theme-pixel-dark.css`
- Modify: `css/theme-supabase-light.css`
- Modify: `css/theme-github-dark.css`

- [ ] **Step 1: Add failing theme layout tests**

In `tests/js/theme.test.mjs`, add this helper after `assertResponsiveCardGrid(css)`:

```js
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

  const iconSvg = ruleBody(css, '.delta-summary__icon svg');
  assert.match(iconSvg, /width:\s*100%;/);
  assert.match(iconSvg, /height:\s*100%;/);
  assert.match(iconSvg, /image-rendering:\s*pixelated;/);

  const body = ruleBody(css, '.delta-summary__body');
  assert.match(body, /min-width:\s*0;/);
}
```

Then add this test after `themes use a responsive equal-height card grid`:

```js
test('themes define compact delta summary product icon layout', () => {
  assertDeltaSummaryIconLayout(lightCss);
  assertDeltaSummaryIconLayout(darkCss);
  assertDeltaSummaryIconLayout(pixelCss);
});
```

- [ ] **Step 2: Run theme tests to verify they fail**

Run:

```bash
npm test
```

Expected: FAIL in `tests/js/theme.test.mjs` because the three theme stylesheets do not yet define the new icon layout rules.

- [ ] **Step 3: Update Pixel Dark summary layout and icon styles**

In `css/theme-pixel-dark.css`, update the existing `.delta-summary` rule so it includes:

```css
  display: flex;
  align-items: center;
  gap: .85rem;
```

Then add these rules after `.delta-summary`:

```css
.delta-summary__icon {
  width: 2.5rem;
  height: 2.5rem;
  flex: 0 0 2.5rem;
  display: grid;
  place-items: center;
  color: var(--oracle-red);
  --product-icon-bg: var(--surface-soft);
  --product-icon-accent: var(--oracle-red);
  --product-icon-ink: var(--ink);
  --product-icon-muted: var(--border-strong);
}
.delta-summary__icon svg {
  width: 100%;
  height: 100%;
  image-rendering: pixelated;
  filter: drop-shadow(2px 2px 0 rgba(0, 0, 0, .75));
}
.delta-summary__body {
  min-width: 0;
}
```

- [ ] **Step 4: Update Supabase Light summary layout and icon styles**

In `css/theme-supabase-light.css`, update the existing `.delta-summary` rule so it includes:

```css
  display: flex;
  align-items: center;
  gap: .85rem;
```

Then add these rules after `.delta-summary`:

```css
.delta-summary__icon {
  width: 2.5rem;
  height: 2.5rem;
  flex: 0 0 2.5rem;
  display: grid;
  place-items: center;
  color: var(--oracle-red);
  --product-icon-bg: var(--surface-raised);
  --product-icon-accent: var(--oracle-red);
  --product-icon-ink: var(--ink);
  --product-icon-muted: var(--border-strong);
}
.delta-summary__icon svg {
  width: 100%;
  height: 100%;
  image-rendering: pixelated;
  filter: drop-shadow(1px 1px 0 rgba(16, 22, 20, .18));
}
.delta-summary__body {
  min-width: 0;
}
```

- [ ] **Step 5: Update GitHub Dark summary layout and icon styles**

In `css/theme-github-dark.css`, update the existing `.delta-summary` rule so it includes:

```css
  display: flex;
  align-items: center;
  gap: .85rem;
```

Then add these rules after `.delta-summary`:

```css
.delta-summary__icon {
  width: 2.5rem;
  height: 2.5rem;
  flex: 0 0 2.5rem;
  display: grid;
  place-items: center;
  color: var(--oracle-red);
  --product-icon-bg: var(--surface-raised);
  --product-icon-accent: var(--oracle-red);
  --product-icon-ink: var(--ink);
  --product-icon-muted: var(--border-strong);
}
.delta-summary__icon svg {
  width: 100%;
  height: 100%;
  image-rendering: pixelated;
  filter: drop-shadow(1px 1px 0 rgba(1, 4, 9, .8));
}
.delta-summary__body {
  min-width: 0;
}
```

- [ ] **Step 6: Run JavaScript tests**

Run:

```bash
npm test
```

Expected: PASS with all JavaScript tests.

- [ ] **Step 7: Run whitespace verification**

Run:

```bash
git diff --check
```

Expected: exit code 0 with no output.

- [ ] **Step 8: Commit theme styling**

Run:

```bash
git add css/theme-pixel-dark.css css/theme-supabase-light.css css/theme-github-dark.css tests/js/theme.test.mjs
git commit -m "style: add compact product summary icon layout"
```

Expected: a commit containing only the theme layout rules and CSS contract tests.

---

### Task 4: Full Verification and PR Branch Update

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run full JavaScript verification**

Run:

```bash
npm test
```

Expected: PASS with all JavaScript tests.

- [ ] **Step 2: Run whitespace verification**

Run:

```bash
git diff --check
```

Expected: exit code 0 with no output.

- [ ] **Step 3: Inspect branch status**

Run:

```bash
git status --short --branch
```

Expected: clean working tree on `feat/theme-switcher-pixel-dark`, ahead of `origin/feat/theme-switcher-pixel-dark`.

- [ ] **Step 4: Push the updated PR branch**

Run:

```bash
git push
```

Expected: PR #17 updates with the product summary icon commits.

---

## Self-Review

- Spec coverage: The plan covers original pixel SVG icons informed by Oracle-hosted references, product-specific runtime updates, fallback icon behavior, summary DOM integration, compact left-side badge styling across all three themes, and focused tests.
- Placeholder scan: The plan contains no deferred implementation instructions or unresolved sections.
- Type consistency: The helper name is consistently `productIconSvg(productId)`, the icon host is `#product-icon.delta-summary__icon`, and product IDs match `data/index.json`.
