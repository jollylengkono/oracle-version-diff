# Handover — oracle-version-diff

**Date:** 2026-05-30
**Live site:** https://jollylengkono.github.io/oracle-version-diff/
**Repo:** public, GitHub Pages from repo root on `master`.

---

## TL;DR — current status

The product has pivoted from a **side-by-side viewer** to a **range-aggregation diff**.
When a user picks **older** and **newer**, the app shows the
**combined set of all changes introduced in the releases *between* them** —
i.e. "what's new / what behavior changed / what's deprecated if I upgrade from A to B."
Grouped per section, each item badged with the release that introduced it.

This is computed from the data we already crawl (each release record holds "what
changed in *that* release"). It is **not** an item-level snapshot diff.

Implemented continuation:
1. Records and index now carry `released` ISO dates.
2. `data/index.json` is chronologically ordered and includes curated `21c`/`19c`
   baseline records.
3. `js/diff.js` exposes `aggregateRange()`.
4. `js/app.js` loads all records and renders aggregated range results.
5. UI is a dark Redwood Console style.
6. `README.md` and the design spec have been updated to reflect the range model.

---

## CURRENT STATE (working & deployed)

- Static site: vanilla HTML/CSS/JS ES modules, no framework, served from repo root.
- Dark Oracle Redwood Console theme (`css/theme.css`), Oracle Red `#C74634`.
- Data-access seam: `js/config.js` (`DATA_BASE`) + `js/datasource.js` (only place
  data is fetched) — kept intact for a future Supabase swap.
- Current UI = **range aggregation** (`js/diff.js` → `aggregateRange`,
  `js/render.js` → `renderAggregated`, driven by `js/app.js`).
- `js/diff.js` still contains the older snapshot-style `diffRecords`/`diffSection`
  helpers for tests/backward compatibility, but the app uses `aggregateRange()`.
- Python pipeline (`pipeline/`): crawls Oracle GoldenGate release notes via `toc.js`,
  splits each section page on `<h3 class="sect3">` release headings into per-release
  records, merges curated `LEGACY_BASELINES` for `21c` and `19c`, validates against
  `schema/version-record.schema.json`, writes `data/index.json` +
  `data/oracle-goldengate/<version>.json`.
- GitHub Action `.github/workflows/refresh-data.yml`: weekly (Mon 06:00 UTC) +
  manual; runs pytest, `python -m pipeline.build`, opens a review PR.
- Tests: JS (`node --test`) and Python (`pytest`) suites cover range aggregation,
  schema validation, release parsing, and legacy baselines.

---

## DATA QUALITY STATUS

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

The previous first-appearance ordering has been fixed. `release_date()` extracts
month/year headings into ISO month-start dates, `build_records()` sorts by
`released` descending, and `write_release_outputs()` emits `released` into both
records and index entries.

Canonicalization is intentionally conservative: exact release tokens are merged
across pages, but patch releases such as `23.7.1.25.02` and `23.7.0.25.01` remain
distinct because the real headings show distinct release months.

### Notes
- Same-month releases are possible (`23.26.1.0.0` and `23.10` are both January
  2026 in the current data). Front-end aggregation uses the ordered record list as
  a tie-breaker, not date filtering alone.
- The parser still uses month-start dates because Oracle headings provide month
  granularity, not exact day-level release dates.

> Investigation command that worked:
> `grep -oE 'sect3"[^>]*>[^<]+' tests/python/fixtures/real/<page>.html | sed 's/sect3"[^>]*>//'`
> Run it for `default-behaviour` and `deprecated-features` to see their real label
> format — that determines the canonicalization rule.

---

## IMPLEMENTATION STATUS (range-aggregation diff)

Implemented with TDD. Relevant files:

### 1. Pipeline — ordering & dedupe (`pipeline/parse.py`, `pipeline/build.py`)
- `release_date()` parses month/year headings.
- Records include `released`; schema validation requires it.
- `build_records()` sorts by `released` descending.
- Data regenerated from Oracle docs.

### 2. Front-end diff logic
- `aggregateRange(records, olderVersion, newerVersion)` returns combined section
  items for the selected range.
- Each item gets `introduced_version`, `introduced_label`, and `introduced_released`.
- Same-version and reversed selections are covered by tests.

### 3. Render (`js/render.js`)
- `renderAggregated(section, items)` renders one combined list.
- `renderItem()` shows a release badge when aggregation metadata is present.
- `renderSideBySide()` remains as unused compatibility/fallback code.

### 4. App wiring (`js/app.js`)
- `main()` loads all small release records up front.
- `renderComparison()` calls `aggregateRange()` and `renderAggregated()`.
- Default selection uses the latest baseline as older and latest release as newer.
- The 3-tab layout remains: What's New, Behavior Changes, Deprecated & Desupported.

### 5. UI copy (`index.html`)
- Subtitle reflects upgrade range intelligence.
- Theme is dark Redwood Console: charcoal surfaces, Oracle-red accents, compact
  controls, and refined release badges.

### 6. Tests + finish
- Run full JS + Python tests before completion.
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
  records the current range-aggregation model.
- Original plan: `docs/superpowers/plans/2026-05-30-oracle-version-diff.md` (stale
  re: this pivot).

## Definition of done
A user picks older + newer → sees one combined, deduped, correctly-ordered list per
section of everything introduced between those releases, each item linking to its
official Oracle doc and badged with its release. Auto-crawler still produces correct
ordered/deduped data weekly via PR. Live and verified.
