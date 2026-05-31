# Responsive Card Grid Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change aggregated release items from a single vertical list into a responsive 3/2/1 equal-height card grid.

**Architecture:** This is a CSS-first layout change. `renderAggregated()` already wraps cards in `.range-list`, so the grid can be implemented by updating theme CSS while leaving JavaScript rendering and data flow unchanged. Both the Supabase light theme and GitHub dark fallback get the same layout-only grid rules.

**Tech Stack:** Static HTML, vanilla CSS, JavaScript ES modules, Node test runner, pytest.

---

## File Structure

- `tests/js/theme.test.mjs`: Add tests that assert both light and dark themes define the responsive grid contract: 3 desktop columns, 2 tablet columns, 1 mobile column, and equal-height card flex behavior.
- `css/theme-supabase-light.css`: Change `.range-list` to a responsive card grid, make `.item` an equal-height flex column, and keep existing Supabase styling tokens unchanged.
- `css/theme-github-dark.css`: Apply the same layout-only grid rules to the preserved dark fallback without changing its color tokens.

No JavaScript, data, crawler, README, or handover changes are planned.

## Task 1: Responsive Grid Test Contract

**Files:**
- Modify: `tests/js/theme.test.mjs`

- [ ] **Step 1: Add helper assertions for the card grid contract**

Add this helper near the top of `tests/js/theme.test.mjs`, after the `html` constant:

```js
function assertResponsiveCardGrid(css) {
  assert.match(css, /\.range-list\s*\{\s*display:\s*grid;\s*grid-template-columns:\s*repeat\(3,\s*minmax\(0,\s*1fr\)\);[\s\S]*gap:\s*\.9rem;/);
  assert.match(css, /@media\s*\(max-width:\s*959px\)\s*\{[\s\S]*\.range-list\s*\{\s*grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\);/);
  assert.match(css, /@media\s*\(max-width:\s*699px\)\s*\{[\s\S]*\.range-list\s*\{\s*grid-template-columns:\s*1fr;/);
  assert.match(css, /\.item\s*\{[\s\S]*display:\s*flex;[\s\S]*flex-direction:\s*column;/);
  assert.match(css, /\.item__source\s*\{[\s\S]*margin-top:\s*auto;/);
}
```

- [ ] **Step 2: Add a failing test for both themes**

Add this test to the end of `tests/js/theme.test.mjs`:

```js
test('themes use a responsive equal-height card grid', () => {
  assertResponsiveCardGrid(lightCss);
  assertResponsiveCardGrid(darkCss);
});
```

- [ ] **Step 3: Run the JS tests to verify the new contract fails**

Run:

```bash
npm test
```

Expected: FAIL in `tests/js/theme.test.mjs` because `.range-list` is still a single-column grid and `.item` is not yet a flex column with an auto-margin source button.

- [ ] **Step 4: Commit the red test contract**

```bash
git add tests/js/theme.test.mjs
git commit -m "test: cover responsive card grid"
```

## Task 2: Theme Grid Implementation

**Files:**
- Modify: `css/theme-supabase-light.css`
- Modify: `css/theme-github-dark.css`
- Test: `tests/js/theme.test.mjs`

- [ ] **Step 1: Update `.range-list` in both themes**

In both `css/theme-supabase-light.css` and `css/theme-github-dark.css`, replace the current `.range-list` rule:

```css
.range-list {
  display: grid;
  gap: .8rem;
}
```

with:

```css
.range-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .9rem;
}
```

- [ ] **Step 2: Update `.item` in both themes for equal-height cards**

In both `css/theme-supabase-light.css` and `css/theme-github-dark.css`, add `display: flex;` and `flex-direction: column;` to the existing `.item` rule so the full rule has this shape:

```css
.item {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.15rem 1.25rem;
  box-shadow: var(--shadow);
}
```

Keep each theme's existing colors and shadows intact.

- [ ] **Step 3: Update `.item__source` in both themes**

In both `css/theme-supabase-light.css` and `css/theme-github-dark.css`, add `margin-top: auto;` to the existing `.item__source` rule:

```css
.item__source {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  align-self: flex-start;
  margin-top: auto;
  min-height: 2.15rem;
  padding: .55rem .85rem;
  border: 1px solid var(--button);
  border-radius: 4px;
  background: var(--button);
  color: #FFFFFF;
  font-size: .82rem;
  font-weight: 700;
  line-height: 1;
  text-decoration: none;
  box-shadow: 0 8px 18px rgba(0, 0, 0, .12);
  transition: background .16s ease, border-color .16s ease, transform .16s ease;
}
```

If the dark theme currently uses `border: 1px solid var(--border);` for `.item__source`, preserve that existing border value instead of changing it to `var(--button)`. The required changes are `align-self: flex-start;` and `margin-top: auto;`.

- [ ] **Step 4: Add tablet and mobile grid rules to both themes**

In both `css/theme-supabase-light.css` and `css/theme-github-dark.css`, add this media query before the existing mobile media block:

```css
@media (max-width: 959px) {
  .range-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
```

Then change the existing mobile media block from `@media (max-width: 700px)` to `@media (max-width: 699px)`, and ensure it contains this rule:

```css
  .range-list {
    grid-template-columns: 1fr;
  }
```

If the existing mobile block already has `.range-list`, replace only that rule. Leave existing mobile picker, tabs, columns, and item layout rules intact.

- [ ] **Step 5: Run JS tests to verify the contract passes**

Run:

```bash
npm test
```

Expected: PASS for all JS tests.

- [ ] **Step 6: Commit the CSS grid implementation**

```bash
git add css/theme-supabase-light.css css/theme-github-dark.css tests/js/theme.test.mjs
git commit -m "style: use responsive card grid"
```

## Task 3: Final Verification

**Files:**
- Verify: `css/theme-supabase-light.css`
- Verify: `css/theme-github-dark.css`
- Verify: `tests/js/theme.test.mjs`

- [ ] **Step 1: Run JS tests**

```bash
npm test
```

Expected: all JS tests pass.

- [ ] **Step 2: Run Python tests**

```bash
.venv/bin/python -m pytest tests/python/ -q
```

Expected: all Python tests pass.

- [ ] **Step 3: Check whitespace**

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 4: Confirm no JavaScript or data behavior changed**

```bash
git diff --name-only HEAD~4..HEAD
```

Expected output is limited to:

```text
css/theme-github-dark.css
css/theme-supabase-light.css
docs/superpowers/plans/2026-05-31-responsive-card-grid.md
docs/superpowers/specs/2026-05-31-responsive-card-grid-design.md
tests/js/theme.test.mjs
```

- [ ] **Step 5: Inspect final state**

```bash
git status --short
git log --oneline -6
```

Expected: clean working tree after the task commits, with recent commits for the responsive grid spec, plan, test contract, and CSS implementation.
