# Handover — Oracle Release Delta

**Date:** 2026-05-30
**Live site:** https://jollylengkono.github.io/oracle-version-diff/
**Repo:** public, GitHub Pages from repo root on `master`.

---

## TL;DR — current status

The product has pivoted from a **side-by-side viewer** to **Oracle Release Delta**.
When a user picks **Current release** and **Target release**, the app shows the
**combined set of all changes introduced after the current release through the
target release** — i.e. "what's new / what behavior changed / what's deprecated
if I upgrade from A to B."
Grouped per section, each item shows a large muted version number for the release
that introduced it.

This is computed from the data we already crawl (each release record holds "what
changed in *that* release"). It is **not** an item-level snapshot diff.

Implemented continuation:
1. Records and index now carry `released` ISO dates.
2. `data/index.json` is chronologically ordered and includes `21c`/`19c`
   baseline records.
3. `js/diff.js` exposes `aggregateRange()`.
4. `js/app.js` loads all records and renders aggregated range results.
5. UI defaults to a Supabase-inspired light card theme, with the prior GitHub
   dark theme preserved as a fallback.
6. `README.md` and the design spec have been updated to reflect the range model.

---

## CURRENT STATE (working & deployed)

- Static site: vanilla HTML/CSS/JS ES modules, no framework, served from repo root.
- Supabase-inspired light card theme is the default (`css/theme-supabase-light.css`);
  the prior GitHub dark theme is preserved as `css/theme-github-dark.css` for a
  one-line fallback in `index.html`.
- Data-access seam: `js/config.js` (`DATA_BASE`) + `js/datasource.js` (only place
  data is fetched) — kept intact for a future Supabase swap.
- Current UI = **range aggregation** (`js/diff.js` → `aggregateRange`,
  `js/render.js` → `renderAggregated`, driven by `js/app.js`).
- Product selector supports Oracle GoldenGate, Oracle Database, and Oracle
  WebLogic Server.
- Version selector labels intentionally show clean release names only. Database
  support-track metadata is stored in `data/index.json` only where Oracle
  explicitly labels the release, for example `Long Term Support Release` or
  `Innovation Release`; WebLogic entries do not carry guessed LTS metadata.
- Current/target release selectors are directional. `19c -> 21c` shows items after
  19c through 21c, and future releases work once the product data adds their JSON
  records.
- `js/diff.js` still contains the older snapshot-style `diffRecords`/`diffSection`
  helpers for tests/backward compatibility, but the app uses `aggregateRange()`.
- Python pipeline (`pipeline/`): product-registry refresh. GoldenGate is crawler-backed
  from Oracle release notes; Oracle Database and Oracle WebLogic Server are
  source-backed curated adapters regenerated from maintained Oracle-owned source
  definitions.
- GitHub Action `.github/workflows/refresh-data.yml`: weekly (Mon 06:00 UTC) +
  manual; runs pytest, `python -m pipeline.build`, refreshes all registered products,
  and opens a review PR.
- GitHub Action `.github/workflows/ai-refresh-data.yml`
  (`AI Assist Oracle Release Delta data`): manual-only AI-assisted refresh for
  Oracle Database and Oracle WebLogic Server curated source definitions. It
  requires `OPENAI_API_KEY` in GitHub Actions secrets, updates
  `pipeline/curated_sources/`, runs `python -m pipeline.build`, and opens a
  review PR. The deployed Vercel site remains static and never receives the
  OpenAI API key.
- Tests: JS (`node --test`) and Python (`pytest`) suites cover range aggregation,
  schema validation, release parsing, and legacy baselines.
- Oracle Database and Oracle WebLogic Server are not auto-discovered yet; adding
  a new release requires updating their curated source definitions.
- Source policy is Oracle-owned web properties: `oracle.com` or any subdomain.
  Curated Database and WebLogic tests reject non-Oracle source hosts.

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
- The `desupported` JSON section is currently empty. Oracle's release-note page
  groups "Deprecated and Desupported" together, and the app displays those entries
  through the `deprecated` section/tab.

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
- `renderItem()` shows the raw source version as a large, 30% opacity card label
  when aggregation metadata is present.
- `renderSideBySide()` remains as unused compatibility/fallback code.

### 4. App wiring (`js/app.js`)
- `main()` loads records for the selected product.
- `renderComparison()` calls `aggregateRange()` and `renderAggregated()`.
- Default selection uses Oracle Database when present, with the latest baseline as
  current release and latest release as target release.
- The 3-tab layout remains: What's New, Behavior Changes, Deprecated & Desupported.

### 5. UI copy (`index.html`)
- App name is Oracle Release Delta.
- Subtitle and delta summary reflect the directional release-delta model.
- Theme defaults to the Supabase-inspired light card UI, with the GitHub dark
  theme preserved as a fallback.

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
- No customer data, Oracle-owned public sources only, no live browser fetching (CORS) —
  all crawling happens in the Action.
- Design spec: `docs/superpowers/specs/2026-05-30-oracle-version-diff-design.md`
  records the current range-aggregation model.
- Original plan: `docs/superpowers/plans/2026-05-30-oracle-version-diff.md` (stale
  re: this pivot).

## Definition of done
A user picks current + target → sees one combined, deduped, correctly-ordered list per
section of everything introduced after the current release through the target
release, each item linking to its Oracle-owned source and showing its source version
prominently. Auto-crawler still produces correct ordered/deduped data weekly via PR.
Live and verified.
