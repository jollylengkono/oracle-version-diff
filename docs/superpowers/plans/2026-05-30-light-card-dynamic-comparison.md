# Light Card Dynamic Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved light card UI and make baseline-to-baseline comparisons useful.

**Architecture:** Keep the existing static frontend and JSON data model. Add curated 21c baseline items in `pipeline/sources.py`, regenerate JSON, and update rendering/CSS to show card-style release notes with large 30% opacity version labels and dark documentation buttons.

**Tech Stack:** Vanilla JavaScript modules, Node `node:test`, Python pytest, generated JSON under `data/`, CSS.

---

### Task 1: Baseline Range Behavior

**Files:**
- Modify: `tests/js/diff.test.mjs`
- Modify: `pipeline/sources.py`
- Regenerate: `data/oracle-goldengate/21c.json`

- [ ] **Step 1: Write the failing test**

Add a JS test proving `19c` to `21c` includes 21c baseline items.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- tests/js/diff.test.mjs`

- [ ] **Step 3: Add curated 21c baseline content**

Add official-doc-backed 21c baseline items to `LEGACY_BASELINES`.

- [ ] **Step 4: Regenerate data**

Run: `.venv/bin/python -m pipeline.build`

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test -- tests/js/diff.test.mjs`

### Task 2: Card Rendering

**Files:**
- Modify: `tests/js/render.test.mjs`
- Modify: `js/render.js`

- [ ] **Step 1: Write failing render tests**

Assert rendered items include a dedicated `.item__version` label using `introduced_version` and an `.item__source` button link.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- tests/js/render.test.mjs`

- [ ] **Step 3: Update renderer**

Render the version label outside the title, use `introduced_version` as the preferred display value, and keep source links as `Official doc`.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- tests/js/render.test.mjs`

### Task 3: Approved Light Card Theme

**Files:**
- Modify: `css/theme.css`
- Modify: `README.md`
- Modify: `docs/HANDOVER.md`

- [ ] **Step 1: Replace the dark theme with the approved light card styling**

Use soft gray page background, white cards, subtle shadows, large 30% opacity version labels, and dark gray source buttons with darker hover.

- [ ] **Step 2: Update docs**

Document the light card UI, dynamic arbitrary comparison behavior, and PR continuation notes.

- [ ] **Step 3: Run full verification**

Run `.venv/bin/python -m pytest tests/python/ -q`, `npm test`, and `git diff --check`.

- [ ] **Step 4: Commit and push**

Commit the implementation and push to the current PR branch.
