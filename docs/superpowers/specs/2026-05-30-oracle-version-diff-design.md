# Oracle Version Diff — Design Spec

**Date:** 2026-05-30
**Status:** Approved (pending written-spec review)
**First product:** Oracle GoldenGate

## 1. Purpose & Single Job

A website that does exactly one thing: let a user pick **two versions of an Oracle
product** (defaulting to *latest vs. previous*) and see a structured **head-to-head
comparison** built **only from official Oracle documentation**.

The first and only product in v1 is **Oracle GoldenGate**. The GoldenGate data
pipeline is built to be the template for adding other products later — but other
products are explicitly **out of scope for v1**.

### Success criteria
- A visitor can select any two available GoldenGate versions and see the five
  comparison sections populated.
- Every data item links back to the exact official Oracle doc URL it came from.
- Data refreshes happen via an automated, human-reviewed pipeline — no manual
  data entry required for routine updates.
- The whole thing runs on free, secure hosting with no backend server.

## 2. Constraints

- **Official sources only.** All displayed data must originate from public
  Oracle documentation (docs.oracle.com release notes, "What's New", new-features,
  deprecated/desupported pages, and public GoldenGate certification sources).
  The full My Oracle Support (MOS) certification matrix is behind login and is
  **not** used; only publicly available certification data is used.
- **No customer data, ever.** The site deals exclusively with public Oracle docs.
  There is nothing sensitive to leak.
- **Free + secure hosting.** Static front-end on GitHub Pages (HTTPS), data
  pipeline on GitHub Actions in the same repo.
- **No live browser scraping.** The visitor's browser never fetches Oracle docs
  (CORS + reliability). All fetching happens at build time in the Action.

## 3. Architecture

Two cleanly separated halves that share state **only** through committed JSON
data files:

### 3a. Data pipeline (build-time, GitHub Actions)
- A scheduled (e.g. weekly) crawler+parser, written in **Python**.
- Steps: detect available GoldenGate versions from Oracle's docs index →
  fetch the relevant public doc pages for each version → parse them into the
  data model (§4) → validate against a JSON schema → write versioned JSON files
  → **open a pull request** with the diff.
- **Auto-detect latest version** = the job noticing a version present in Oracle's
  docs index that is not yet in our data set, and including it in the PR.
- A human (the maintainer) reviews and merges the PR. This review gate prevents a
  broken parse (e.g. after Oracle restyles a page) from publishing bad data.

### 3b. Front-end (static, runs in the browser)
- Plain static site: vanilla HTML/CSS/JS, no framework.
- Loads the committed JSON files and renders the comparison entirely client-side.
- No backend, no server-side state, no live external fetches.

**Isolation:** the parser and the UI meet only at the JSON files. Either can change
without breaking the other, and each is testable independently.

## 4. Data Model

One JSON record per product version. Indicative shape:

```json
{
  "product": "oracle-goldengate",
  "version": "23ai",
  "release_label": "Oracle GoldenGate 23ai",
  "last_updated": "2026-05-30",
  "sections": {
    "certification": [
      { "category": "Database", "value": "Oracle Database 23ai",
        "source_url": "https://docs.oracle.com/..." }
    ],
    "whats_new": [
      { "title": "...", "description": "...", "source_url": "https://docs.oracle.com/..." }
    ],
    "behavior_changes": [
      { "title": "...", "description": "...", "source_url": "..." }
    ],
    "deprecated": [
      { "title": "...", "description": "...", "source_url": "..." }
    ],
    "desupported": [
      { "title": "...", "description": "...", "source_url": "..." }
    ]
  }
}
```

The comparison view derives Added / Changed / Removed by diffing the two selected
versions' records.

## 5. Comparison Sections (all five in v1)

1. **Certification** — supported databases / OS / platforms, from public GG
   certification sources.
2. **What's New** — features added in the newer version relative to the older.
3. **Behavior Changes** — changed defaults / behaviors.
4. **Deprecated** — features marked deprecated.
5. **Desupported / Removed** — features dropped.

Every item shows its originating Oracle doc URL (provenance = trust).

## 6. Front-End UX

- Two version dropdowns at the top. Default selection = latest vs. previous.
  User may choose **any two** available versions (e.g. 19c vs 23ai).
- Below: the five sections as tabs (or stacked panels), each rendered as a
  diff-style list with **Added / Changed / Removed** color coding.
- A "Sources & last updated" footer listing the doc pages used and the data
  refresh date.
- Responsive and lightweight.
- Styled with the Oracle Redwood-inspired theme (see §6a).

## 6a. Visual Design & Theme (Oracle Redwood-inspired)

The site uses an Oracle-branded look inspired by Oracle's **Redwood** design
language: Oracle Red as the primary accent over clean neutral surfaces.

**Color palette (CSS custom properties):**

| Token | Hex | Use |
|-------|-----|-----|
| `--oracle-red` | `#C74634` | Primary brand accent: header bar, active tab, links, buttons |
| `--oracle-red-dark` | `#A23824` | Hover/active states for red elements |
| `--ink` | `#1A1A1A` | Primary text |
| `--slate` | `#3A3F44` | Secondary text / labels |
| `--surface` | `#FFFFFF` | Cards / panels |
| `--bg` | `#F5F4F2` | Page background (warm neutral) |
| `--border` | `#E0DED9` | Dividers / card borders |
| `--added` | `#3C7A3C` | "Added" diff items (green) |
| `--changed` | `#B5760A` | "Changed" diff items (amber) |
| `--removed` | `#C74634` | "Removed" diff items (Oracle red) |

**Treatment:**
- Top header: Oracle-red band with the product title in white, Oracle-style
  clean sans-serif (system stack: `"Helvetica Neue", Arial, sans-serif` — close
  to Oracle Sans without bundling licensed fonts).
- Version dropdowns and tabs styled with the red accent; active tab underlined
  in Oracle red.
- Comparison items rendered as white cards on the warm-neutral background, with
  a thin left color bar (green/amber/red) indicating Added/Changed/Removed.
- Accessible contrast (WCAG AA) for all text on colored backgrounds.
- All theme values centralized as CSS custom properties so the palette can be
  tuned in one place.

> Note: this is an Oracle-*inspired* theme using public brand colors for a
> personal/educational tool. It does not use Oracle's proprietary fonts or imply
> official Oracle endorsement.

## 7. Hosting & Security

- **GitHub Pages** for the static site (free, HTTPS), in the same repo as the
  Action so the pipeline lives beside the site.
- Parser runs in **GitHub Actions** (Python).
- No customer data; only public Oracle docs. No secrets required beyond the
  default `GITHUB_TOKEN` for opening PRs.

## 8. Testing

- **Parser unit tests** run against saved sample doc HTML **fixtures**, so tests
  don't depend on the live Oracle site and don't break when it's unavailable.
- **Schema validation** step: a malformed parse fails the Action (and the PR)
  rather than publishing bad data.
- **Front-end** rendered/tested against a sample JSON fixture.

## 9a. Extensibility & Future Backend (Supabase-ready)

v1 ships on the static JSON architecture (free, nothing to break), but is
deliberately built so a future backend (e.g. **Supabase** Postgres + Auth + REST)
slots in without a rewrite:

- **Single data-access seam.** The front-end never calls `fetch` directly in UI
  code. All data loading goes through one module (`js/datasource.js`) with a
  `js/config.js` base setting. Switching from "load a static JSON file" to
  "call a REST/Supabase API" means changing only `datasource.js`.
- **DB-shaped schema.** `version-record.schema.json` maps 1:1 to relational tables
  (`products`, `versions`, `section_items`), so the same data model serves files
  today and a database later.
- **Pure logic stays portable.** `diff.js`/`render.js` are framework- and
  source-agnostic; they work unchanged under any future front-end framework.
- **Pipeline is backend-independent.** `build.py` writes JSON today; it could
  additionally (or instead) insert rows into a database with no change to parsers.

Adopting Supabase later would unlock: version-update email subscriptions,
user accounts / saved comparisons, community notes, full-text search across
products, and a public API. None of these are built in v1.

## 9b. Out of Scope (v1)

- Products other than Oracle GoldenGate.
- The gated MOS certification matrix.
- Live in-browser fetching of Oracle docs.
- User accounts, saved comparisons, or any server-side persistence.
