# Product Registry Data Refresh Design

Date: 2026-05-31
Status: Approved for implementation planning

## Goal

Expand periodic data refresh from GoldenGate-only to every product included in
Oracle Release Delta.

The refresh pipeline must make this behavior explicit: if a product appears in
`data/index.json`, that product must have a registered refresh adapter. New
products cannot be added as static-only data without also adding a refresh path.

## Current State

The current refresh workflow is `.github/workflows/refresh-data.yml`. It runs on
Mondays at 06:00 UTC and can also be triggered manually. It installs Python
dependencies, runs Python tests, runs `python -m pipeline.build`, and opens a PR
with refreshed data.

The implementation is currently GoldenGate-specific:

- The workflow is named `Refresh GoldenGate data`.
- `pipeline/sources.py` has a single global `PRODUCT_ID` and `PRODUCT_LABEL`.
- `pipeline.build.main()` calls the GoldenGate release-note crawler and writes
  only GoldenGate outputs.
- Oracle Database and Oracle WebLogic Server records exist under `data/`, but
  they are curated seed records and are not rebuilt by the scheduled pipeline.

## Desired Behavior

The refresh pipeline becomes product-registry driven.

Each included product must declare:

- product id
- product label
- refresh adapter
- source definitions needed by that adapter

The first registry must include:

- `oracle-goldengate`: existing crawler-backed adapter.
- `oracle-database`: source-backed curated adapter.
- `oracle-weblogic-server`: source-backed curated adapter.

The scheduled workflow runs all registered product adapters, validates every
record, writes product JSON files, writes one combined `data/index.json`, and
opens one review PR.

## Adapter Model

Adapters expose one product-level build operation that returns validated version
records for that product.

GoldenGate keeps the current crawler behavior:

- resolves release-note section pages from Oracle `toc.js`
- parses release headings into per-release records
- includes the `19c` static baseline
- parses the `21c` legacy release-note baseline

Database and WebLogic use source-backed curated adapters in this phase:

- source definitions live in code and contain the curated record content plus the
  Oracle source URLs that justify that content
- source URLs must be Oracle-owned (`oracle.com` or subdomains)
- each referenced source URL is fetched during refresh to verify it is reachable
- records are regenerated from those definitions during each refresh
- current curated content and release order are preserved
- `last_updated` is stamped during refresh

This phase does not auto-discover new Database or WebLogic releases. Adding a new
release for those products still requires updating the source definitions, but
the periodic workflow will rebuild, validate, and PR those records consistently.

## Index Writing

`data/index.json` must be generated from all registered products.

For each product:

- versions are ordered from newest to oldest in the index
- `order` remains higher for newer releases
- `file` points to the generated product record JSON
- optional metadata such as `support_track` is preserved when the source
  definition provides it

The writer must not drop other products when refreshing one product. The normal
scheduled path must refresh all registered products together.

## Workflow Behavior

Rename the workflow and PR copy from GoldenGate-specific to all-product wording:

- workflow name: `Refresh Oracle Release Delta data`
- commit message: `data: refresh Oracle Release Delta data`
- PR title: `Data refresh: Oracle Release Delta`

The workflow remains weekly plus manual. It still opens a PR for human review and
does not auto-merge.

## Guardrails

Tests must enforce:

- every product in generated `data/index.json` has a registered refresh adapter
- every registered product is present in generated `data/index.json`
- Database and WebLogic refreshed records preserve their existing product ids,
  versions, labels, sections, and Oracle-owned source URLs
- Database and WebLogic refresh fails if a referenced Oracle source URL is no
  longer reachable
- no generated record violates `schema/version-record.schema.json`
- the all-product build does not drop GoldenGate crawler output

Existing JS source-host tests remain useful for curated Database/WebLogic data.

## Non-Goals

- No auto-discovery for new Database or WebLogic versions in this phase.
- No frontend UI behavior changes.
- No Supabase backend migration.
- No automatic PR merge.
- No switch away from static JSON files.

## Acceptance Criteria

- Running `python -m pipeline.build` rebuilds GoldenGate, Database, and WebLogic
  records.
- The generated `data/index.json` includes all three products.
- Tests fail if a product exists in `data/index.json` without a registered
  refresh adapter.
- The GitHub workflow refreshes all products and opens one review PR.
- README and handover docs no longer describe periodic refresh as GoldenGate-only.
