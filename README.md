# Oracle Version Diff

A static website that shows what Oracle GoldenGate changes are introduced when
upgrading across a selected release range, using data parsed from official Oracle
documentation.

## How it works

- **Front-end** (`index.html`, `css/`, `js/`): vanilla static site with a light,
  card-based Oracle style. Loads JSON from `data/` through a single data-access
  seam (`js/datasource.js`, configured in `js/config.js`) and renders one combined
  list of release-note items introduced between any two selected versions. No
  backend.
- **Pipeline** (`pipeline/`): a Python crawler+parser run weekly by GitHub Actions.
  It fetches the public GoldenGate rolling release notes from Oracle docs, parses
  each release section, combines those records with a static `19c` anchor and a
  parsed `21c` legacy release-notes baseline, validates against
  `schema/version-record.schema.json`, and opens a pull request with the new
  `data/` JSON for human review.
- **Comparison behavior**: the selectors are independent. Comparing `19c` to `21c`
  shows curated 21c baseline cards, while comparing `19c` to a modern or future
  release includes every generated release record after 19c up through the selected
  newer version.

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

## Future backend (Supabase-ready)

v1 is intentionally static. All data loading is isolated in `js/datasource.js`, and
the JSON schema is relational-shaped, so a future move to Supabase (Postgres + Auth +
REST) only requires changing that one module — unlocking features like update-email
subscriptions, saved comparisons, community notes, and search.

> Oracle-inspired theme for an educational tool. Not affiliated with or endorsed by Oracle.
