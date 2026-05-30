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

## 9. Out of Scope (v1)

- Products other than Oracle GoldenGate.
- The gated MOS certification matrix.
- Live in-browser fetching of Oracle docs.
- User accounts, saved comparisons, or any server-side persistence.
