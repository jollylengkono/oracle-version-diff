# Oracle Release Delta

A static website that shows what changed after a current Oracle release through a
target release, using data sourced from Oracle-owned web properties.

## How it works

- **Front-end** (`index.html`, `css/`, `js/`): vanilla static site with a
  Supabase-inspired light card UI and a preserved GitHub dark fallback theme.
  Loads JSON from `data/` through a single data-access seam (`js/datasource.js`,
  configured in `js/config.js`) and renders one combined list of release-note
  items introduced after the current release through the target release. No backend.
- **Pipeline** (`pipeline/`): a Python crawler+parser run weekly by GitHub Actions.
  It fetches the public GoldenGate rolling release notes from Oracle docs, parses
  each release section, combines those records with a static `19c` anchor and a
  parsed `21c` legacy release-notes baseline, validates against
  `schema/version-record.schema.json`, and opens a pull request with the new
  `data/` JSON for human review.
- **Products**: Oracle GoldenGate data is crawler-backed. Oracle Database currently
  has curated seed records from `12c` through latest `26ai`, with source-backed
  support-track metadata for releases Oracle explicitly labels. Oracle WebLogic
  Server has curated seed records from `11g` through latest `15c`.
- **Release delta behavior**: selecting `Current release = 19c` and
  `Target release = 26ai` shows what was introduced after 19c through 26ai:
  what's new, behavior changes, and deprecated/desupported items.

## Local development

```bash
npm test                              # JS unit tests
python3 -m pip install -r pipeline/requirements.txt
python3 -m pytest tests/python/ -v    # pipeline unit tests
python3 -m http.server 8000           # serve the site at http://localhost:8000/
```

## Deploying (GitHub Pages)

1. Push this repo to GitHub.
2. Settings → Pages → Build and deployment → Source: **Deploy from a branch**,
   Branch: `master`, folder: `/ (root)`.
3. The site is served at `https://<user>.github.io/oracle-version-diff/`.

## Updating data

The `Refresh GoldenGate data` workflow runs weekly (and on demand via
"Run workflow"). It opens a PR; review the diff and merge. The modern GoldenGate
line is discovered from `pipeline/sources.py` (`RELEASE_NOTES_BASE`) and Oracle's
`toc.js`; update that base URL if Oracle moves the rolling release-note stream.
Legacy baselines live in `pipeline/sources.py`: `19c` is a static anchor, and
`21c` is parsed from the official 21c release-note pages listed in
`LEGACY_RELEASE_NOTE_SOURCES`.

Oracle Database seed records live under `data/oracle-database/`. Oracle WebLogic
Server seed records live under `data/oracle-weblogic-server/`. Expand these
records or add product-specific crawlers before treating them as exhaustive.
Release selectors intentionally show clean release names; support-track metadata
is kept in `data/index.json` only where Oracle documentation explicitly provides
that label.

Curated records may use any Oracle-owned source host (`oracle.com` or a subdomain
such as `docs.oracle.com` or `blogs.oracle.com`). Each record keeps its exact
`source_url` visible through the Official source button.

## Future backend (Supabase-ready)

v1 is intentionally static. All data loading is isolated in `js/datasource.js`, and
the JSON schema is relational-shaped, so a future move to Supabase (Postgres + Auth +
REST) only requires changing that one module — unlocking features like update-email
subscriptions, saved comparisons, community notes, and search.

> Oracle-inspired theme for an educational tool. Not affiliated with or endorsed by Oracle.
