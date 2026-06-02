# Pixel Theme Default Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `theme-pixel-dark` the default theme for first-time visitors while preserving saved theme preferences.

**Architecture:** The static page uses a stylesheet link for the initial render and inline JavaScript for saved theme restoration and theme switching. The implementation updates both default sources so first-time visitors render Pixel immediately, while `localStorage.oracle-diff-theme` continues to override the default for returning visitors.

**Tech Stack:** Vanilla HTML, CSS, browser `localStorage`, Node.js `node:test`.

---

## File Structure

- Modify: `index.html`
  - Responsibility: Initial HTML shell, theme stylesheet link, theme switcher markup, and inline theme persistence script.
- Modify: `tests/js/theme.test.mjs`
  - Responsibility: Static contract tests for theme file references and theme CSS behavior.

---

### Task 1: Make Pixel Dark the No-Preference Default

**Files:**
- Modify: `index.html`
- Modify: `tests/js/theme.test.mjs`

- [ ] **Step 1: Write the failing default-theme contract test**

In `tests/js/theme.test.mjs`, replace the current default-theme test:

```js
test('index uses Supabase-inspired light theme by default', () => {
  assert.match(html, /href="css\/theme-supabase-light\.css"/);
  assert.doesNotMatch(html, /href="css\/theme\.css"/);
  assert.doesNotMatch(html, /href="css\/theme-openclaw-light\.css"/);
});
```

with:

```js
test('index uses pixel dark theme by default', () => {
  assert.match(html, /href="css\/theme-pixel-dark\.css"/);
  assert.match(html, /localStorage\.getItem\('oracle-diff-theme'\) \|\| 'theme-pixel-dark'/);
  assert.doesNotMatch(html, /href="css\/theme\.css"/);
  assert.doesNotMatch(html, /href="css\/theme-openclaw-light\.css"/);
});
```

- [ ] **Step 2: Run the targeted test and verify it fails**

Run:

```bash
npm test
```

Expected: FAIL in `tests/js/theme.test.mjs` because `index.html` still points the default stylesheet and runtime fallback at `theme-supabase-light`.

- [ ] **Step 3: Update the initial stylesheet default**

In `index.html`, replace:

```html
<link id="themeLink" rel="stylesheet" href="css/theme-supabase-light.css" />
```

with:

```html
<link id="themeLink" rel="stylesheet" href="css/theme-pixel-dark.css" />
```

- [ ] **Step 4: Update the runtime fallback default**

In `index.html`, replace:

```js
var current = localStorage.getItem('oracle-diff-theme') || 'theme-supabase-light';
```

with:

```js
var current = localStorage.getItem('oracle-diff-theme') || 'theme-pixel-dark';
```

- [ ] **Step 5: Run JavaScript verification**

Run:

```bash
npm test
```

Expected: PASS with 5 passing JavaScript tests.

- [ ] **Step 6: Run whitespace verification**

Run:

```bash
git diff --check
```

Expected: exit code 0 with no output.

- [ ] **Step 7: Commit the implementation**

Run:

```bash
git add index.html tests/js/theme.test.mjs
git commit -m "feat: default to pixel dark theme"
```

Expected: a new commit on `feat/theme-switcher-pixel-dark` containing only the default-theme implementation and test update.

- [ ] **Step 8: Push the updated PR branch**

Run:

```bash
git push
```

Expected: `origin/feat/theme-switcher-pixel-dark` receives the new commits and PR #17 updates automatically.

---

## Self-Review

- Spec coverage: The plan updates the initial stylesheet default, runtime fallback default, and HTML contract test described by the approved spec.
- Placeholder scan: No placeholders, TODOs, or deferred implementation steps remain.
- Type consistency: Theme names match the existing `data-theme` value and stylesheet name: `theme-pixel-dark`.
