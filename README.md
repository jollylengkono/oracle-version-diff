# Oracle Version Diff

A static website that compares two Oracle GoldenGate versions head-to-head —
certification, what's new, behavior changes, deprecated, and desupported features —
using data parsed from official Oracle documentation.

## How it works

- **Front-end** (`index.html`, `css/`, `js/`): vanilla static site. Loads JSON from
  `data/` through a single data-access seam (`js/datasource.js`, configured in
  `js/config.js`) and renders an Added/Changed/Removed diff. No backend.
- **Pipeline** (`pipeline/`): a Python crawler+parser run weekly by GitHub Actions.
  It fetches public Oracle docs, parses them, validates against
  `schema/version-record.schema.json`, and opens a pull request with the new
  `data/` JSON for human review.

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
   Branch: `main`, folder: `/ (root)`.
3. The site is served at `https://<user>.github.io/oracle-version-diff/`.

## Updating data

The `Refresh GoldenGate data` workflow runs weekly (and on demand via
"Run workflow"). It opens a PR; review the diff and merge. To add a newly released
version, add its doc URLs to `pipeline/sources.py` (append to `SOURCES`; the list
order is the display order).

## Future backend (Supabase-ready)

v1 is intentionally static. All data loading is isolated in `js/datasource.js`, and
the JSON schema is relational-shaped, so a future move to Supabase (Postgres + Auth +
REST) only requires changing that one module — unlocking features like update-email
subscriptions, saved comparisons, community notes, and search.

> Oracle-inspired theme for an educational tool. Not affiliated with or endorsed by Oracle.
