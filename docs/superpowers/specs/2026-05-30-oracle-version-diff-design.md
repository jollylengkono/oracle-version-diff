# Oracle Version Diff — Design Spec

**Date:** 2026-05-30
**Status:** Approved
**First product:** Oracle GoldenGate

---

## REVISION (2026-05-30, post-calibration): Range-Aggregation Upgrade Diff

Investigating the **live** Oracle GoldenGate docs invalidated two original assumptions:

1. **Not discrete major versions.** GoldenGate now publishes a single *rolling*
   release-notes stream (`database/goldengate/core/26/release-notes/`, branded
   "26ai / 23.26.x"), with a machine-readable `toc.js` listing the section pages
   (New Features, Default Behavior Changes, Deprecated & Desupported). Each page is
   organised **per release** via `<h3>` headings; individual items inside are loose
   `<div>/<p>` blocks (not reliably headed).
2. **No item-level snapshot delta exists.** Release notes describe what changed *in
   that release only*; Oracle publishes no complete "state of version A vs state of
   version B" inventory. Set-differencing two release-note records is therefore not
   meaningful.

**Revised model — range aggregation, not snapshot set-diff:**
- A "version" is either a **release record** holding the release-note items
  introduced in that release, or a curated **baseline record** for legacy
  generations such as `19c` and `21c`. All records include a `released` date for
  chronological ordering and `record_type` metadata.
- When the user chooses an older and newer release, comparison means showing the
  combined set of all release-note items introduced in `(older, newer]`, grouped by
  section. Each item is badged with the release that introduced it.
- Same-version selection shows that release's own items. Reversed selections are
  normalized so users can choose either dropdown order.
- **v1 data source:** auto-crawl the modern rolling stream via `toc.js`, splitting
  each section page on its `<h3>` release headings into per-release records. Legacy
  generations `19c` and `21c` are curated baseline records; full legacy parsers are
  a later add-on.

The sections below are amended by this revision where they conflict: §1 job becomes
"upgrade changes introduced across a selected release range"; §3a pipeline is
`toc.js`-driven and release-based; §6 UX is one aggregated list per section, with
release badges instead of Added/Changed/Removed groups. Provenance links, hosting
(§7), and Supabase-readiness (§9a) are unchanged.

---

## 1. Purpose & Single Job

A website that does exactly one thing: let a user pick **two Oracle GoldenGate
releases** (defaulting to *latest vs. previous*) and see the structured set of
changes introduced when upgrading across that range, built **only from official
Oracle documentation**.

The first and only product in v1 is **Oracle GoldenGate**. The GoldenGate data
pipeline is built to be the template for adding other products later — but other
products are explicitly **out of scope for v1**.

### Success criteria
- A visitor can select any two available GoldenGate releases and see the available
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
  "record_type": "release",
  "released": "2026-01-01",
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

The comparison view aggregates records by `released` date across the selected
upgrade range.

## 5. Comparison Sections

1. **Certification** — supported databases / OS / platforms, from public GG
   certification sources. Reserved in the schema; not shown in the rolling
   release-notes v1 UI.
2. **What's New** — features introduced in releases within the selected range.
3. **Behavior Changes** — changed defaults / behaviors introduced in the range.
4. **Deprecated** — features marked deprecated.
5. **Desupported / Removed** — features dropped. The current rolling release page
   combines deprecated and desupported content, so v1 displays this with
   Deprecated.

Every item shows its originating Oracle doc URL (provenance = trust).

## 6. Front-End UX

- Two version dropdowns at the top. Default selection = latest curated baseline vs.
  latest modern release. User may choose **any two** available versions (e.g.
  19c vs 23.26).
- Below: the comparison sections as tabs, each rendered as one aggregated list of
  release-note items. Each item shows the release that introduced it.
- A "Sources & last updated" footer listing the doc pages used and the data
  refresh date.
- Responsive and lightweight.
- Styled with the Oracle Redwood-inspired theme (see §6a).

## 6a. Visual Design & Theme (Dark Oracle Redwood Console)

The site uses a restrained dark console look inspired by Oracle's **Redwood**
design language: Oracle Red as the primary accent over charcoal work surfaces.

**Color palette (CSS custom properties):**

| Token | Hex | Use |
|-------|-----|-----|
| `--oracle-red` | `#C74634` | Primary brand accent: active tab, links, range affordances |
| `--oracle-red-bright` | `#F06A59` | High-emphasis accent and hover states |
| `--ink` | `#F5F2ED` | Primary text |
| `--muted` | `#B8AEA6` | Secondary text / labels |
| `--surface` | `#181514` | Cards / panels |
| `--surface-2` | `#211D1B` | Elevated panels |
| `--bg` | `#0F0D0C` | Page background |
| `--border` | `#3A302C` | Dividers / card borders |
| `--added` | `#3C7A3C` | Reserved for future status styling |
| `--changed` | `#B5760A` | Reserved for future status styling |
| `--removed` | `#C74634` | Reserved for future status styling |

**Treatment:**
- Top header: compact product title and subtitle on the dark page surface.
- Version dropdowns live in an elevated command panel with red range accent.
- Tabs use dark console styling with an Oracle-red active indicator.
- Comparison items render as dark elevated cards with release badges and Oracle-red
  left accents.
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
  source-agnostic; range aggregation and rendering work unchanged under any future
  front-end framework.
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
