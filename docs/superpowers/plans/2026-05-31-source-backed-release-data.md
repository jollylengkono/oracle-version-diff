# Source-Backed Release Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove inaccurate LTS/non-LTS dropdown labels and expand Oracle Database and WebLogic Server release-delta data using Oracle documentation.

**Architecture:** Keep the static JSON-driven app model. Store source-backed support-track metadata only where Oracle explicitly labels it, keep selectors clean, and expand curated release records without adding a crawler.

**Tech Stack:** Vanilla ES modules, static JSON records, Node test runner, Python schema validation.

---

### Task 1: Selector Support Metadata

**Files:**
- Modify: `js/app.js`
- Modify: `tests/js/diff.test.mjs`
- Modify: `tests/js/data.test.mjs`

- [ ] Write tests that selector labels do not append support-track text.
- [ ] Write tests that Database support metadata uses Oracle wording only where documented.
- [ ] Remove `supportTrackLabel()` and return raw version labels from `versionOptionLabel()`.
- [ ] Replace `is_lts` metadata with `support_track` where source-backed, and omit support metadata for WebLogic.

### Task 2: Curated Product Data

**Files:**
- Modify: `data/index.json`
- Modify: `data/oracle-database/*.json`
- Modify: `data/oracle-weblogic-server/*.json`

- [ ] Expand Oracle Database 12c, 19c, 21c, and 26ai section entries from Oracle docs.
- [ ] Expand WebLogic Server 12c, 14c, and 15c section entries from Oracle docs.
- [ ] Keep all records schema-valid and keep `desupported` arrays present.

### Task 3: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/HANDOVER.md`

- [ ] Update docs to say support labels are source-backed metadata, not dropdown text.
- [ ] Run `npm test`.
- [ ] Run `.venv/bin/python -m pytest tests/python/ -q`.
- [ ] Run data schema validation with `pipeline.validate`.
- [ ] Run `git diff --check`.
- [ ] Commit and push; if the existing PR was merged, create a new PR.
