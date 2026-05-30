# Oracle Release Delta Product Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Oracle Database `19c -> 26ai` support and reframe the app as Oracle Release Delta.

**Architecture:** Keep the static JSON data model and existing range aggregation. Add a second product to `data/index.json`, add two Oracle Database records, and update `js/app.js` so product changes reload the current/target selectors and records.

**Tech Stack:** Vanilla JavaScript modules, static JSON, Node `node:test`, Python pytest.

---

### Task 1: Tests

**Files:**
- Modify: `tests/js/diff.test.mjs`
- Create: `tests/js/data.test.mjs`

- [x] Add tests for default product, directional copy, and Oracle Database data.
- [x] Run targeted tests and verify they fail before implementation.

### Task 2: Data

**Files:**
- Modify: `data/index.json`
- Create: `data/oracle-database/19c.json`
- Create: `data/oracle-database/26ai.json`

- [x] Add Oracle Database product metadata and curated release records.

### Task 3: UI

**Files:**
- Modify: `index.html`
- Modify: `js/app.js`
- Modify: `css/theme.css`

- [x] Rename the app to Oracle Release Delta.
- [x] Add product/current/target selectors.
- [x] Reload product records when the product changes.

### Task 4: Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/HANDOVER.md`

- [ ] Update docs.
- [ ] Run `npm test`.
- [ ] Run `.venv/bin/python -m pytest tests/python/ -q`.
- [ ] Run `git diff --check`.
- [ ] Commit and push.
