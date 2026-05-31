# Supabase Light Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the OpenClaw-inspired default light theme with a Supabase-inspired light theme while preserving the GitHub dark fallback.

**Architecture:** This is a CSS-first theme swap. The app keeps its existing static HTML/JS data flow, card rendering, and tab behavior; only the default stylesheet, theme tests, and documentation change. The preserved fallback remains `css/theme-github-dark.css` and should not be restyled.

**Tech Stack:** Static HTML, vanilla CSS, JavaScript ES modules, Node test runner, pytest.

---

## File Structure

- `tests/js/theme.test.mjs`: Updates the theme contract so tests expect `css/theme-supabase-light.css`, Supabase green tokens, white cards, near-white background, and unchanged GitHub dark fallback tokens.
- `css/theme-supabase-light.css`: New default light theme derived from the current light stylesheet but restyled around Supabase-like green, white surfaces, fine borders, compact card UI, and dark source buttons.
- `css/theme-openclaw-light.css`: Removed from active use. Delete this file after the new Supabase stylesheet exists.
- `index.html`: Points to `css/theme-supabase-light.css`.
- `README.md`: Changes default theme wording from OpenClaw-inspired to Supabase-inspired.
- `docs/HANDOVER.md`: Changes current state and implementation notes from OpenClaw-inspired to Supabase-inspired.

## Task 1: Theme Test Contract

**Files:**
- Modify: `tests/js/theme.test.mjs`

- [ ] **Step 1: Write the failing theme contract**

Replace `tests/js/theme.test.mjs` with:

```js
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
npm test
```

Expected: FAIL because `css/theme-supabase-light.css` does not exist yet and `index.html` still references `theme-openclaw-light.css`.

- [ ] **Step 3: Commit the red test contract**

```bash
git add tests/js/theme.test.mjs
git commit -m "test: cover Supabase light theme"
```

## Task 2: Default Supabase Light Theme

**Files:**
- Create: `css/theme-supabase-light.css`
- Delete: `css/theme-openclaw-light.css`
- Modify: `index.html`
- Test: `tests/js/theme.test.mjs`

- [ ] **Step 1: Create the new Supabase light stylesheet**

Copy the current light theme as the starting point:

```bash
cp css/theme-openclaw-light.css css/theme-supabase-light.css
```

Then edit `css/theme-supabase-light.css` so these blocks match exactly:

```css
:root {
  --oracle-red: #C74634;
  --accent: #3ECF8E;
  --accent-strong: #249361;
  --accent-soft: rgba(62, 207, 142, .14);
  --ink: #111817;
  --muted: #5F6F69;
  --muted-strong: #2F3D38;
  --surface: #FFFFFF;
  --surface-soft: #F1F5F3;
  --surface-raised: #FBFDFC;
  --bg: #F8FAF9;
  --border: #D8E0DC;
  --border-strong: #AEBDB6;
  --button: #101614;
  --button-hover: #050807;
  --focus: #3ECF8E;
  --shadow: 0 14px 34px rgba(24, 38, 35, .08);
}
```

```css
.tab--active {
  color: #062D1F;
  background: var(--accent-soft);
  border-color: var(--accent);
  box-shadow: 0 8px 24px rgba(62, 207, 142, .12);
}
```

```css
.picker__field select:focus {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
  border-color: var(--accent);
}
```

```css
.item__version {
  flex: 0 0 auto;
  color: rgba(17, 24, 23, .30);
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: 0;
  line-height: .92;
  white-space: nowrap;
}
```

Keep the existing card layout, responsive media query, `.panel[hidden]`, and dark source button structure. Do not add gradients or viewport-width font sizing.

- [ ] **Step 2: Update the default stylesheet link**

In `index.html`, change:

```html
<link rel="stylesheet" href="css/theme-openclaw-light.css" />
```

to:

```html
<link rel="stylesheet" href="css/theme-supabase-light.css" />
```

- [ ] **Step 3: Delete the old OpenClaw default stylesheet**

```bash
git rm css/theme-openclaw-light.css
```

- [ ] **Step 4: Run tests to verify the theme contract passes**

Run:

```bash
npm test
```

Expected: PASS for all JS tests.

- [ ] **Step 5: Commit the default theme change**

```bash
git add css/theme-supabase-light.css index.html tests/js/theme.test.mjs
git commit -m "style: apply Supabase light theme"
```

## Task 3: Documentation Wording

**Files:**
- Modify: `README.md`
- Modify: `docs/HANDOVER.md`

- [ ] **Step 1: Update README theme wording**

In `README.md`, replace:

```markdown
OpenClaw-inspired light card UI and a preserved GitHub dark fallback theme.
```

with:

```markdown
Supabase-inspired light card UI and a preserved GitHub dark fallback theme.
```

- [ ] **Step 2: Update handover theme wording**

In `docs/HANDOVER.md`, replace these two phrases:

```markdown
OpenClaw-inspired light card theme is the default
```

```markdown
OpenClaw-inspired light card theme
```

with:

```markdown
Supabase-inspired light card theme is the default
```

```markdown
Supabase-inspired light card theme
```

- [ ] **Step 3: Verify stale OpenClaw default-theme wording is gone**

Run:

```bash
rg -n "OpenClaw-inspired|theme-openclaw-light" README.md docs/HANDOVER.md index.html tests/js/theme.test.mjs
```

Expected: no output and exit code 1.

- [ ] **Step 4: Commit documentation updates**

```bash
git add README.md docs/HANDOVER.md
git commit -m "docs: update default theme wording"
```

## Task 4: Final Verification

**Files:**
- Verify: `index.html`
- Verify: `css/theme-supabase-light.css`
- Verify: `css/theme-github-dark.css`
- Verify: `README.md`
- Verify: `docs/HANDOVER.md`

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

- [ ] **Step 4: Confirm fallback theme was not modified in this implementation**

```bash
git diff HEAD~3 -- css/theme-github-dark.css
```

Expected: no output. If this command shows changes, inspect them and revert only accidental edits to `css/theme-github-dark.css`.

- [ ] **Step 5: Inspect final changed files**

```bash
git status --short
git log --oneline -5
```

Expected: clean working tree after the task commits, with recent commits for the theme test contract, Supabase theme, docs update, and the already committed spec/plan.
