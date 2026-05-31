# Oracle Release Delta

A static website that shows what changed after a current Oracle release through a
target release, using data sourced from Oracle-owned web properties.

## How it works

- **Front-end** (`index.html`, `css/`, `js/`): vanilla static site with a
  Supabase-inspired light card UI and a preserved GitHub dark fallback theme.
  Loads JSON from `data/` through a single data-access seam (`js/datasource.js`,
  configured in `js/config.js`) and renders one combined list of release-note
  items introduced after the current release through the target release. No backend.
- **Pipeline** (`pipeline/`): a product-registry data refresh run weekly by GitHub Actions.
  GoldenGate is crawler-backed. Oracle Database and Oracle WebLogic Server are
  source-backed curated adapters: their release records are regenerated from
  maintained Oracle-owned source definitions, source URLs are checked during
  refresh, records are schema-validated, and the workflow opens a pull request
  with the refreshed `data/` JSON for human review.
- **Products**: all registered products are rebuilt by the refresh workflow.
  Database and WebLogic records come from source-backed curated adapters, while
  GoldenGate records come from the crawler-backed adapter.
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

The `Refresh Oracle Release Delta data` workflow runs weekly (and on demand via
"Run workflow"). It rebuilds all registered products and opens a PR; review the
diff and merge. A product must have a refresh adapter before it can be included
in `data/index.json`.

Oracle Database source definitions are maintained in
`pipeline/curated_sources/oracle-database.json`. Oracle WebLogic Server source
definitions are maintained in
`pipeline/curated_sources/oracle-weblogic-server.json`. Expand those curated
source definitions, or add product-specific crawlers, before treating a product
as exhaustive. The `data/` tree is generated refresh output for review and
publication. Release selectors intentionally show clean release names;
support-track metadata is kept in `data/index.json` only where Oracle
documentation explicitly provides that label.

Curated records may use any Oracle-owned source host (`oracle.com` or a subdomain
such as `docs.oracle.com` or `blogs.oracle.com`). Each record keeps its exact
`source_url` visible through the Official source button.

### AI-assisted data refresh

The `AI Assist Oracle Release Delta data` workflow is manual-only. It runs from
GitHub Actions, reads `OPENAI_API_KEY` from GitHub Actions secrets, asks OpenAI
to assist with Oracle Database and Oracle WebLogic Server curated-source updates,
then runs the deterministic `pipeline.build` step and opens or updates a review
PR when changes are produced. The browser UI and deployed Vercel site never
receive the OpenAI API key.

## Future backend (Supabase-ready)

v1 is intentionally static. All data loading is isolated in `js/datasource.js`, and
the JSON schema is relational-shaped, so a future move to Supabase (Postgres + Auth +
REST) only requires changing that one module — unlocking features like update-email
subscriptions, saved comparisons, community notes, and search.

> Oracle-inspired theme for an educational tool. Not affiliated with or endorsed by Oracle.
