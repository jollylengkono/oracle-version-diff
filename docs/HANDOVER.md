# Handover — oracle-version-diff

**Date:** 2026-05-30
**Live site:** https://jollylengkono.github.io/oracle-version-diff/
**Repo:** public, GitHub Pages from repo root on `master`.

---

## TL;DR — what to do next

The product is pivoting from a **side-by-side viewer** to a **range-aggregation diff**.
User decision (confirmed): when a user picks **older** and **newer**, show the
**combined set of all changes introduced in the releases *between* them** —
i.e. "what's new / what behavior changed / what's deprecated if I upgrade from A to B."
Grouped per section, each item badged with the release that introduced it.

This is computable from the data we already crawl (each release record already
holds "what changed in *that* release"). It is **not** an item-level snapshot diff
(that doesn't work for rolling release notes — set-differencing produces noise).

**Two prerequisites before the diff is correct:**
1. **Correct chronological ordering** of releases.
2. **De-duplication / reconciliation** of release labels (see data-quality problem below).

---

## CURRENT STATE (working & deployed)

- Static site: vanilla HTML/CSS/JS ES modules, no framework, served from repo root.
- Oracle Redwood theme (`css/theme.css`), Oracle Red `#C74634`.
- Data-access seam: `js/config.js` (`DATA_BASE`) + `js/datasource.js` (only place
  data is fetched) — kept intact for a future Supabase swap.
- Current UI = **side-by-side two-column** view (`js/render.js` → `renderSideBySide`,
  driven by `js/app.js`). This is what's live now.
- `js/diff.js` exists (snapshot-style `diffRecords`/`diffSection`) but is **unused**
  by app.js. It implements the WRONG model for this product (snapshot set-diff).
  The new range-aggregation logic should be a new function, not this.
- Python pipeline (`pipeline/`): crawls Oracle GoldenGate release notes via `toc.js`,
  splits each section page on `<h3 class="sect3">` release headings into per-release
  records, validates against `schema/version-record.schema.json`, writes
  `data/index.json` + `data/oracle-goldengate/<version>.json`.
- GitHub Action `.github/workflows/refresh-data.yml`: weekly (Mon 06:00 UTC) +
  manual; runs pytest, `python -m pipeline.build`, opens a review PR.
- Tests: 13 JS (`node --test`), 14 Python (`pytest`). All green at last run.

---

## THE DATA-QUALITY PROBLEM (must fix for the diff to be meaningful)

`data/index.json` lists **16 "versions"** but they are really ~10 real releases
under **two different label conventions mixed across the three section pages**:

- **New Features page** uses clean headings *with dates*, e.g.:
  - `Release 26ai (23.26.1.0.0)`
  - `Release 23.10: January …`
  - `Release 23.9: September …`
  - `Release 23.7: January 2025`
  - `Release 23.6: October 2024`
  - `Release 23.5.2: August …`
  - `Release 23.5: July 2024`
  - `Release 23.4.2: June 2024`
  - `Release 23.4.1: June 2024`
  - `Release 23.4: May 2024`
- **Default Behavior Changes** and **Deprecated & Desupported** pages apparently
  use a **different long-form label** (date-encoded), which is where the extra
  records come from: `23.10.0.25.10`, `23.8.0.25.04`, `23.7.1.25.02`,
  `23.6.0.25.05`, `23.7.0.25.01`, `23.26.2.0.0`. (The `.25.MM` tail ≈ year.month.)

So `release_version()` in `pipeline/parse.py` is extracting two different keys for
what may be the same release, causing **double-counting** and a nonsensical order
(the current `order` field is just first-appearance across pages, not chronological).

### Recommended fix
1. **Capture the date** from the New Features `<h3>` heading (the heading text after
   the colon, e.g. "January 2025"). Add a `released` field (ISO date) to each record.
   This is the **reliable chronological sort key** — far more trustworthy than trying
   to semver-sort the mixed numbering.
2. **Canonicalize the release key** so the long-form and short-form labels for the
   same release merge into one record. Likely: derive a canonical `release` (e.g.
   `23.7`) and keep the full label for display. Verify by reading the actual
   `<h3>` headings in `tests/python/fixtures/real/default-behaviour.html` and
   `deprecated-features.html` (NOT yet inspected — do this first).
3. Re-emit `data/index.json` ordered by `released` descending.

> Investigation command that worked:
> `grep -oE 'sect3"[^>]*>[^<]+' tests/python/fixtures/real/<page>.html | sed 's/sect3"[^>]*>//'`
> Run it for `default-behaviour` and `deprecated-features` to see their real label
> format — that determines the canonicalization rule.

---

## IMPLEMENTATION PLAN (range-aggregation diff)

Follow TDD. Files and the order to touch them:

### 1. Pipeline — ordering & dedupe (`pipeline/parse.py`, `pipeline/build.py`)
- Parse release date from heading; add `released` (ISO) to each record.
- Canonicalize release key across the 3 pages so one release = one record with
  merged sections. Update `build_records()` accordingly.
- `write_release_outputs()`: set `order` by `released` desc (or emit `released` and
  let the front-end sort).
- Update/extend Python tests in `tests/python/` against the real fixtures.
- Re-run `python -m pipeline.build` to regenerate `data/`.

### 2. Front-end diff logic (new function — do NOT reuse `js/diff.js`)
- New pure function, e.g. `aggregateRange(records, olderVersion, newerVersion)`:
  - Given the full ordered records list + the two selected versions,
  - return, per section (`whats_new`, `behavior_changes`, `deprecated`), the
    concatenation of items from every release with `released` in
    `(older, newer]` (exclusive of older, inclusive of newer).
  - Tag each item with the release/version it came from (for the badge).
  - Handle older==newer (single release) and reversed selection gracefully.
- Unit-test it in `tests/js/` with `node:test`.

### 3. Render (`js/render.js`)
- Add `renderAggregated(section, items)` rendering one combined list, each item
  showing a version badge (the introducing release). Keep `escapeHtml`/`renderItem`.
- Keep `renderSideBySide` if you want it as a fallback/toggle (user chose
  aggregation-only, so a toggle is optional — confirm before adding scope).

### 4. App wiring (`js/app.js`)
- `main()` must now **load all records in the selected range** (not just two).
  Cheapest path: load the two selected metas to get their `order`/`released`, then
  load every record whose order is in the range. Or load all records up front
  (16 small files) — simpler, fine for this size.
- Replace `renderComparison` to call `aggregateRange` + `renderAggregated`.
- Section labels already exist; keep the 3-tab layout.

### 5. UI copy (`index.html`)
- Subtitle currently: "Oracle GoldenGate — release notes, two versions side by side".
  Change to reflect "what changes when upgrading from A to B".

### 6. Tests + finish
- All JS + Python tests green.
- Use `superpowers:finishing-a-development-branch` to merge.
- Wait for Pages redeploy; verify live (the existing verify pattern: curl the live
  index.json + a record + index.html).

---

## GOTCHAS / CONTEXT
- Env: Node v24.15.0, Python 3.14.4. Use **current** dep versions (already pinned in
  `pipeline/requirements.txt`); 3.11-era pins lack wheels here.
- `jsonschema` needs `rfc3986-validator` + `rfc3339-validator` for `uri`/`date`
  format checks (already in requirements.txt).
- pytest: do NOT create `tests/python/__init__.py`; `conftest.py` inserts REPO_ROOT
  into sys.path.
- No customer data, official Oracle docs only, no live browser fetching (CORS) —
  all crawling happens in the Action.
- Design spec: `docs/superpowers/specs/2026-05-30-oracle-version-diff-design.md`
  (has a post-calibration revision section). **Update it** to record this second
  pivot to range-aggregation before/while implementing.
- Original plan: `docs/superpowers/plans/2026-05-30-oracle-version-diff.md` (stale
  re: this pivot).

## Definition of done
A user picks older + newer → sees one combined, deduped, correctly-ordered list per
section of everything introduced between those releases, each item linking to its
official Oracle doc and badged with its release. Auto-crawler still produces correct
ordered/deduped data weekly via PR. Live and verified.
