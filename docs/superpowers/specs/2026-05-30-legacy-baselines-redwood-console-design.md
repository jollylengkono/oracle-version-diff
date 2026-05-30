# Legacy Baselines and Redwood Console Design

**Date:** 2026-05-30  
**Status:** Approved for implementation  
**Scope:** Oracle GoldenGate legacy-version support plus dark Redwood Console UI

## Goal

Extend Oracle Version Diff so users can compare older GoldenGate generations, such
as `19c`, against modern rolling releases such as `23.26.2.0.0`, then present the
result in a modern, restrained Oracle dark theme.

The comparison remains an upgrade-range view: the user chooses an older and newer
release, and the app shows the release-note items introduced after the older
selection through the newer selection.

## Data Approach

Use curated legacy baseline records for `19c` and `21c` in v1 of this feature.
Each baseline record is a normal JSON record in `data/oracle-goldengate/`, backed
by public Oracle documentation links. The record represents a generation-level
starting point rather than a parsed rolling release-note increment.

Modern `23.x` and `26ai` records remain generated from the rolling release-note
stream. The index mixes both kinds of records in chronological display order:
legacy baselines first by release date, then modern rolling release records.

Add lightweight metadata to version records and index entries:

- `released`: existing ISO month-start date used for ordering.
- `record_type`: `baseline` for curated generation baselines, `release` for parsed
  rolling release-note records.

The schema must allow this metadata and tests must validate it.

## Comparison Behavior

For baseline-to-modern comparisons, the baseline acts as the exclusive lower
bound. Example: selecting `19c` as older and `23.26.2.0.0` as newer returns every
modern release-note item after the `19c` baseline through `23.26.2.0.0`.

For modern-to-modern comparisons, behavior stays the same as the current
range-aggregation model.

For same-version selection, the app shows that selected record's own items. For a
baseline, this can show baseline context items if present, or an empty state if the
baseline contains no release-note increments.

Reversed selections are normalized by index order, not by string sorting.

## User Interface

Adopt the selected **Redwood Console** direction:

- Dark charcoal page background with dark elevated panels.
- Oracle red as the primary accent for focus states, active tabs, links, and range
  affordances.
- Compact command area at the top: product title, short subtitle, older/newer
  selectors, and concise metadata.
- One aggregated list per section with refined cards and release badges.
- Avoid marketing/hero treatment. The app opens directly into the comparison tool.
- Keep the layout dense enough for technical scanning, with cleaner spacing,
  typography, and hover/focus states than the current warm light UI.

The UI must remain static HTML/CSS/vanilla JS and responsive down to mobile
widths. Cards must keep an 8px-or-less radius and avoid nested-card styling.

## Tests

Add or update tests for:

- Schema validation accepts `record_type`.
- Index/data generation includes curated baselines.
- Default selection chooses a meaningful older/newer pair with the latest modern
  release as newer.
- Range aggregation works for a baseline older version and modern newer version.
- Rendered aggregated cards still escape text and show release badges.

Run full Python and JS suites before completion.

## Out of Scope

- Full parser support for older legacy documentation systems.
- MOS certification matrix data.
- Accounts, saved comparisons, subscriptions, or backend persistence.
- A theme toggle; this feature replaces the current light theme with the dark
  Redwood Console style.
