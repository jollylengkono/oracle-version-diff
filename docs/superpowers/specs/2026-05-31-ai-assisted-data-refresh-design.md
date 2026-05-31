# AI-Assisted Data Refresh Design

Date: 2026-05-31
Status: Approved for implementation planning

## Goal

Add a manual GitHub Actions workflow that uses OpenAI to assist Oracle Release
Delta data generation from Oracle-owned sources.

The refresh must run from repository automation, not from the deployed browser
UI and not from a developer laptop. The OpenAI API key must be stored as a
GitHub Actions secret and must never be written to the repository, generated
JSON, or workflow logs.

## Current State

The repository has a product-registry refresh pipeline:

- GoldenGate uses a deterministic crawler-backed adapter.
- Oracle Database and Oracle WebLogic Server use source-backed curated adapter
  definitions under `pipeline/curated_sources/`.
- `python -m pipeline.build` rebuilds all registered products and writes
  generated files under `data/`.
- `.github/workflows/refresh-data.yml` runs the deterministic refresh and opens
  a PR.

Database and WebLogic still require humans to update curated source definitions
when a new release appears. The existing deterministic refresh validates and
regenerates those records, but it does not discover or extract new versions.

## Desired Behavior

Add a second, manual-only workflow named `AI Assist Oracle Release Delta data`.

When triggered, the workflow:

1. Reads product refresh targets from checked-in configuration.
2. Uses OpenAI from the GitHub Actions runner to propose updates for supported
   source-backed products.
3. Searches and fetches only Oracle-owned URLs (`oracle.com` and subdomains).
4. Extracts candidate release records as strict JSON matching
   `schema/version-record.schema.json`.
5. Updates curated source definitions, not generated `data/` directly.
6. Runs the deterministic `python -m pipeline.build`.
7. Runs validation and tests.
8. Opens a PR for human review.

The existing deterministic weekly refresh remains available and does not require
OpenAI.

## Product Scope

Version 1 supports AI-assisted discovery and extraction for:

- `oracle-database`
- `oracle-weblogic-server`

GoldenGate stays on the existing crawler-backed adapter. The AI-assisted
workflow must not replace or weaken the GoldenGate crawler.

## OpenAI Boundary

OpenAI is an extraction and reasoning layer inside a controlled pipeline. It does
not receive permission to write files directly, run shell commands, access
non-Oracle sites, or merge PRs.

The Python pipeline owns:

- search query construction
- Oracle-only URL filtering
- page fetching
- prompt construction
- schema validation
- source URL validation
- file writes
- PR creation through the workflow

OpenAI owns:

- identifying likely release/version pages from supplied Oracle search results
- extracting concise release record candidates from supplied Oracle page content
- returning structured JSON only

## Secrets And Runtime

The workflow uses `OPENAI_API_KEY` from GitHub Actions secrets:

```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

If `OPENAI_API_KEY` is missing, the AI-assisted workflow fails before making any
network calls or file changes.

The deployed Vercel site remains a static finished product that serves generated
JSON. The browser UI must not call OpenAI and must not receive the OpenAI API
key.

## Pipeline Components

Add these Python modules:

- `pipeline/ai_refresh.py`: command-line orchestration for AI-assisted refresh.
- `pipeline/openai_extract.py`: OpenAI client wrapper and structured extraction
  request/response handling.
- `pipeline/oracle_discovery.py`: Oracle-only discovery, URL allowlisting, and
  page fetching helpers.

The CLI is:

```bash
python -m pipeline.ai_refresh --products oracle-database oracle-weblogic-server
```

The CLI must update only `pipeline/curated_sources/*.json`. Generated `data/`
changes must come from the subsequent deterministic `python -m pipeline.build`.

## Data Contract

OpenAI responses must be parsed into a strict internal candidate object before
any file write.

Each candidate release record must include:

- `product`
- `version`
- `release_label`
- `record_type`
- `released`
- `sections.certification`
- `sections.whats_new`
- `sections.behavior_changes`
- `sections.deprecated`
- `sections.desupported`

Every section item must include an Oracle-owned `source_url`. Items without
source URLs are rejected. Non-Oracle URLs are rejected. Records that fail
`schema/version-record.schema.json` are rejected.

The source definition `index` metadata may include only keys already accepted by
the deterministic writer, such as `label` and `support_track`.

## Discovery Rules

The workflow may use OpenAI to rank and interpret Oracle source candidates, but
the Python pipeline must enforce these rules:

- Search candidates must resolve to `oracle.com` or a subdomain.
- Redirects must still end on `oracle.com` or a subdomain.
- Fetched page content must come from an allowed Oracle host.
- The final `source_url` stored for each item must be the Oracle URL used as
  evidence.
- Duplicate URLs and duplicate section items are deduplicated deterministically.

If no reliable Oracle source is found for a proposed release, the workflow fails
with a clear message and does not write partial data for that release.

## Merge Strategy For Curated Sources

The AI-assisted refresh updates source-backed curated definitions. It must:

- preserve existing versions unless the generated candidate intentionally
  replaces the same product/version
- add newly discovered versions at the top of the source definition
- preserve existing `index` metadata when a version already exists
- preserve existing product ids and product labels
- stamp `last_updated` only through `python -m pipeline.build`

If OpenAI proposes a record for an existing version, the workflow replaces that
version only when the candidate validates and has at least one sourced item or
explicit sourced evidence for each populated section.

## Workflow Behavior

Add `.github/workflows/ai-refresh-data.yml`.

The workflow is manual-only:

```yaml
on:
  workflow_dispatch:
```

It installs dependencies, verifies `OPENAI_API_KEY`, runs the AI-assisted
refresh, runs the deterministic build, runs tests, and opens a PR.

Suggested PR copy:

- branch: `data/ai-refresh`
- title: `AI data refresh: Oracle Release Delta`
- commit message: `data: AI-assisted Oracle Release Delta refresh`
- label: `data-refresh`

The workflow must not auto-merge.

## Guardrails

Tests must cover:

- missing `OPENAI_API_KEY` fails before file writes
- non-Oracle discovery URLs are rejected
- OpenAI responses with invalid schema are rejected
- OpenAI responses with non-Oracle `source_url` values are rejected
- generated candidates update curated source definitions, not `data/` directly
- existing curated versions are preserved when no valid replacement exists
- new versions are inserted into source definitions in newest-first order
- the AI-assisted workflow remains manual-only
- the workflow uses `secrets.OPENAI_API_KEY`
- the deterministic `python -m pipeline.build` still validates all generated
  records after AI-assisted source updates

## Non-Goals

- No browser UI integration.
- No Vercel API route in this phase.
- No automatic scheduled AI refresh in this phase.
- No automatic PR merge.
- No direct writes from OpenAI to repository files.
- No non-Oracle source usage.
- No replacement of the existing deterministic refresh workflow.
- No AI-assisted GoldenGate extraction in this phase.

## Acceptance Criteria

- A maintainer can manually run `AI Assist Oracle Release Delta data` from
  GitHub Actions.
- The workflow uses `secrets.OPENAI_API_KEY` and does not expose the key.
- The workflow creates a PR with updated curated sources and generated `data/`.
- Database and WebLogic can receive newly discovered Oracle-sourced versions
  through the AI-assisted path.
- Invalid AI output fails closed with no partial generated data committed.
- Full Python and JavaScript test suites pass after an AI-assisted refresh.
