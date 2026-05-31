# Oracle-Owned Sources And OpenClaw Light Theme Design

## Goal

Update Oracle Release Delta so it treats Oracle-owned web properties as valid sources, not only `docs.oracle.com`, and make an OpenClaw-inspired light card theme the default while preserving the current GitHub dark theme as an easy fallback.

## Source Policy

The app will define an Oracle-owned source as any URL whose host is `oracle.com` or ends with `.oracle.com`. This includes `docs.oracle.com`, `blogs.oracle.com`, `www.oracle.com`, and other Oracle subdomains. The existing `source_url` field remains the source of truth for each item; no schema expansion is required for this change.

The footer and README copy will change from “official Oracle documentation (docs.oracle.com)” to broader Oracle-owned sources. Curated data can use Oracle blog posts when they are the best source for a release feature, announcement, behavior change, or upgrade-impact detail.

## Validation

Tests will enforce that curated Oracle Database and WebLogic source URLs point to Oracle-owned hosts. Existing schema validation remains unchanged because `source_url` is already required and URI-validated.

The validation should be scoped to static curated product records under `data/oracle-database/` and `data/oracle-weblogic-server/`. GoldenGate crawler output already comes from Oracle docs and should continue through the existing pipeline tests.

## Theme Architecture

The current `css/theme.css` GitHub dark theme will be preserved as `css/theme-github-dark.css`. A new `css/theme-openclaw-light.css` will become the default stylesheet referenced by `index.html`.

Fallback remains simple: switching back to the dark theme is a one-line stylesheet change in `index.html`. No runtime theme toggle is in scope for this iteration.

## Visual Direction

Use the approved “OpenClaw Landing-Light” direction:

- warm off-white page background
- sharp near-black headings
- pill-like selectors and tabs
- card-based result list
- subtle borders and soft shadows
- muted large version numbers on cards
- compact dark source buttons

The app remains a usable tool on the first screen. The design should not become a marketing landing page; the selector, tabs, and cards stay central.

## Testing

Implementation must include:

- JS tests that verify version option labels remain clean.
- JS data tests that reject non-Oracle source hosts for curated Database and WebLogic records.
- A smoke check that `index.html` references the light theme by default.
- Existing JS, Python, schema validation, and whitespace checks before completion.
