# Oracle Version Diff Implementation Plan

> **Status:** Historical v1 build plan. The product pivoted after calibration from
> snapshot/side-by-side comparison to range aggregation. Use `docs/HANDOVER.md`
> and `docs/superpowers/specs/2026-05-30-oracle-version-diff-design.md` as the
> current source of truth for new work.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a free, static website that shows a head-to-head comparison of two Oracle GoldenGate versions (certification, what's new, behavior changes, deprecated, desupported), fed by a human-reviewed GitHub Actions data pipeline that parses official Oracle docs.

**Architecture:** Two cleanly separated halves that meet only at committed JSON files. (1) A Python pipeline (run in GitHub Actions) fetches public Oracle GoldenGate doc pages, parses them into per-version JSON, validates against a schema, and opens a PR. (2) A vanilla HTML/CSS/JS static site (GitHub Pages, served from repo root) loads that JSON and renders an Added/Changed/Removed diff in an Oracle Redwood-inspired theme.

**Tech Stack:** Front-end: vanilla ES-module JS, CSS custom properties, no framework, with a single data-access seam (`datasource.js`) for a future Supabase/REST backend. Tests: Node's built-in `node:test` for pure JS. Pipeline: Python 3.11, `requests`, `beautifulsoup4`, `jsonschema`; tests with `pytest` against saved HTML fixtures. CI: GitHub Actions + `peter-evans/create-pull-request`. Hosting: GitHub Pages (static).

**Spec:** `docs/superpowers/specs/2026-05-30-oracle-version-diff-design.md`

---

## File Structure

```
oracle-version-diff/
├── index.html                        # static site entry (served at Pages root)
├── css/theme.css                     # Oracle Redwood theme (CSS custom properties)
├── js/diff.js                        # PURE: diff two version records → added/changed/removed
├── js/render.js                      # PURE: diff result → HTML strings
├── js/config.js                      # data-source base setting (single place to repoint)
├── js/datasource.js                  # the ONLY data-access seam (swap to Supabase here later)
├── js/app.js                         # bootstrap: wire dropdowns/tabs (DOM); data via datasource.js
├── data/index.json                   # product + versions registry (with display order)
├── data/oracle-goldengate/23ai.json  # one record per version
├── data/oracle-goldengate/21c.json
├── schema/version-record.schema.json # JSON Schema (draft-07) for a version record
├── pipeline/requirements.txt
├── pipeline/sources.py               # ordered registry: version → doc page URLs
├── pipeline/parse.py                 # PURE: HTML → section item lists
├── pipeline/detect.py                # PURE: docs-index HTML → candidate version labels
├── pipeline/validate.py              # validate a record dict against the schema
├── pipeline/build.py                 # orchestrator: fetch → parse → validate → write JSON
├── tests/js/diff.test.mjs            # node:test for diff.js
├── tests/js/render.test.mjs          # node:test for render.js
├── tests/python/conftest.py
├── tests/python/fixtures/*.html      # saved representative Oracle doc HTML
├── tests/python/test_parse.py
├── tests/python/test_detect.py
├── tests/python/test_validate.py
├── tests/python/test_build.py
├── package.json                      # JS test runner script
└── .github/workflows/refresh-data.yml
```

Responsibilities are split so each unit is independently testable: `diff.js`/`render.js`/`parse.py`/`detect.py`/`validate.py` are pure (no I/O, no DOM, no network); `app.js` and `build.py` are the only units that touch DOM/network/filesystem, and both take their pure dependencies as plain function calls.

**Future-backend seam:** `js/datasource.js` is the single place the front-end loads data. Today it fetches static JSON under the base set in `js/config.js`. To move to a Supabase/REST backend later, only `datasource.js` changes — `app.js` and all pure logic stay untouched. The JSON schema (Task 1) is intentionally relational-shaped so it maps 1:1 to future DB tables.

---

## Task 1: Repo config, JSON schema, and sample data

**Files:**
- Create: `package.json`
- Create: `schema/version-record.schema.json`
- Create: `data/oracle-goldengate/21c.json`
- Create: `data/oracle-goldengate/23ai.json`
- Create: `data/index.json`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "oracle-version-diff",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test tests/js/"
  }
}
```

- [ ] **Step 2: Create `schema/version-record.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Oracle product version record",
  "type": "object",
  "additionalProperties": false,
  "required": ["product", "version", "release_label", "last_updated", "sections"],
  "properties": {
    "product": { "type": "string" },
    "version": { "type": "string" },
    "release_label": { "type": "string" },
    "last_updated": { "type": "string", "format": "date" },
    "sections": {
      "type": "object",
      "additionalProperties": false,
      "required": ["certification", "whats_new", "behavior_changes", "deprecated", "desupported"],
      "properties": {
        "certification": { "type": "array", "items": { "$ref": "#/definitions/cert" } },
        "whats_new": { "type": "array", "items": { "$ref": "#/definitions/feature" } },
        "behavior_changes": { "type": "array", "items": { "$ref": "#/definitions/feature" } },
        "deprecated": { "type": "array", "items": { "$ref": "#/definitions/feature" } },
        "desupported": { "type": "array", "items": { "$ref": "#/definitions/feature" } }
      }
    }
  },
  "definitions": {
    "cert": {
      "type": "object",
      "additionalProperties": false,
      "required": ["category", "value", "source_url"],
      "properties": {
        "category": { "type": "string" },
        "value": { "type": "string" },
        "source_url": { "type": "string", "format": "uri" }
      }
    },
    "feature": {
      "type": "object",
      "additionalProperties": false,
      "required": ["title", "description", "source_url"],
      "properties": {
        "title": { "type": "string" },
        "description": { "type": "string" },
        "source_url": { "type": "string", "format": "uri" }
      }
    }
  }
}
```

- [ ] **Step 3: Create `data/oracle-goldengate/21c.json`**

```json
{
  "product": "oracle-goldengate",
  "version": "21c",
  "release_label": "Oracle GoldenGate 21c",
  "last_updated": "2026-05-30",
  "sections": {
    "certification": [
      { "category": "Oracle Database", "value": "Oracle Database 19c", "source_url": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/" }
    ],
    "whats_new": [
      { "title": "Microservices-only architecture", "description": "Classic Architecture deprecated in favor of Microservices.", "source_url": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html" }
    ],
    "behavior_changes": [
      { "title": "Default deployment is Microservices", "description": "New installs default to the Microservices Architecture.", "source_url": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html" }
    ],
    "deprecated": [
      { "title": "Classic Architecture", "description": "Classic Architecture is deprecated.", "source_url": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html" }
    ],
    "desupported": []
  }
}
```

- [ ] **Step 4: Create `data/oracle-goldengate/23ai.json`**

```json
{
  "product": "oracle-goldengate",
  "version": "23ai",
  "release_label": "Oracle GoldenGate 23ai",
  "last_updated": "2026-05-30",
  "sections": {
    "certification": [
      { "category": "Oracle Database", "value": "Oracle Database 23ai", "source_url": "https://docs.oracle.com/en/middleware/goldengate/core/23/" }
    ],
    "whats_new": [
      { "title": "AI vector replication", "description": "Support for replicating vector data types.", "source_url": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html" },
      { "title": "Microservices-only architecture", "description": "Classic Architecture deprecated in favor of Microservices.", "source_url": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html" }
    ],
    "behavior_changes": [
      { "title": "Default deployment is Microservices", "description": "Installs default to the Microservices Architecture; classic install paths removed.", "source_url": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html" }
    ],
    "deprecated": [],
    "desupported": [
      { "title": "Classic Architecture", "description": "Classic Architecture is desupported and removed.", "source_url": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html" }
    ]
  }
}
```

- [ ] **Step 5: Create `data/index.json`**

`order` is an integer; higher = newer. The front-end uses it to choose the default pair (latest vs. previous) without parsing version strings.

```json
{
  "products": [
    {
      "id": "oracle-goldengate",
      "label": "Oracle GoldenGate",
      "versions": [
        { "version": "23ai", "label": "23ai", "order": 2, "file": "oracle-goldengate/23ai.json" },
        { "version": "21c", "label": "21c", "order": 1, "file": "oracle-goldengate/21c.json" }
      ]
    }
  ]
}
```

- [ ] **Step 6: Commit**

```bash
git add package.json schema/ data/
git commit -m "chore: add JSON schema, sample GoldenGate data, and index"
```

---

## Task 2: Pure diff core (`js/diff.js`)

**Files:**
- Create: `js/diff.js`
- Test: `tests/js/diff.test.mjs`

The diff treats each section as a list of items keyed by a stable identity. `certification` is keyed by `category::value`; all other sections are keyed by `title`. An item is **changed** when its key exists in both records but its `description` differs (certification has no description, so it only ever produces added/removed).

- [ ] **Step 1: Write the failing test**

```js
// tests/js/diff.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { keyFor, diffSection, diffRecords, SECTIONS } from '../../js/diff.js';

test('keyFor uses title for feature sections', () => {
  assert.equal(keyFor('whats_new', { title: 'A', description: 'x' }), 'A');
});

test('keyFor uses category::value for certification', () => {
  assert.equal(keyFor('certification', { category: 'DB', value: 'v19' }), 'DB::v19');
});

test('diffSection classifies added, removed, changed, unchanged', () => {
  const older = [
    { title: 'keep', description: 'same' },
    { title: 'mod', description: 'old' },
    { title: 'gone', description: 'x' }
  ];
  const newer = [
    { title: 'keep', description: 'same' },
    { title: 'mod', description: 'new' },
    { title: 'fresh', description: 'y' }
  ];
  const r = diffSection('whats_new', older, newer);
  assert.deepEqual(r.added.map(i => i.title), ['fresh']);
  assert.deepEqual(r.removed.map(i => i.title), ['gone']);
  assert.deepEqual(r.changed.map(i => i.title), ['mod']);
  assert.deepEqual(r.unchanged.map(i => i.title), ['keep']);
});

test('diffRecords covers all five sections', () => {
  const empty = { certification: [], whats_new: [], behavior_changes: [], deprecated: [], desupported: [] };
  const older = { sections: { ...empty } };
  const newer = { sections: { ...empty, whats_new: [{ title: 'n', description: 'd' }] } };
  const r = diffRecords(older, newer);
  assert.deepEqual(SECTIONS, ['certification', 'whats_new', 'behavior_changes', 'deprecated', 'desupported']);
  assert.equal(r.whats_new.added.length, 1);
  assert.equal(r.certification.added.length, 0);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL — `Cannot find module '../../js/diff.js'`.

- [ ] **Step 3: Write minimal implementation**

```js
// js/diff.js
export const SECTIONS = ['certification', 'whats_new', 'behavior_changes', 'deprecated', 'desupported'];

export function keyFor(section, item) {
  if (section === 'certification') return `${item.category}::${item.value}`;
  return item.title;
}

export function diffSection(section, olderItems, newerItems) {
  const olderByKey = new Map(olderItems.map(i => [keyFor(section, i), i]));
  const newerByKey = new Map(newerItems.map(i => [keyFor(section, i), i]));
  const added = [], removed = [], changed = [], unchanged = [];

  for (const [key, item] of newerByKey) {
    if (!olderByKey.has(key)) { added.push(item); continue; }
    const prev = olderByKey.get(key);
    if ((prev.description || '') !== (item.description || '')) changed.push(item);
    else unchanged.push(item);
  }
  for (const [key, item] of olderByKey) {
    if (!newerByKey.has(key)) removed.push(item);
  }
  return { added, removed, changed, unchanged };
}

export function diffRecords(older, newer) {
  const result = {};
  for (const section of SECTIONS) {
    result[section] = diffSection(
      section,
      older.sections[section] || [],
      newer.sections[section] || []
    );
  }
  return result;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add js/diff.js tests/js/diff.test.mjs
git commit -m "feat: add pure version-diff core"
```

---

## Task 3: Pure HTML rendering (`js/render.js`)

**Files:**
- Create: `js/render.js`
- Test: `tests/js/render.test.mjs`

Render functions return HTML **strings** (no DOM dependency) so they are unit-testable under `node:test`. `app.js` injects them via `innerHTML`. All user-facing text is HTML-escaped.

- [ ] **Step 1: Write the failing test**

```js
// tests/js/render.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { escapeHtml, renderItem, renderSection } from '../../js/render.js';

test('escapeHtml neutralizes angle brackets and ampersands', () => {
  assert.equal(escapeHtml('<a>&"'), '&lt;a&gt;&amp;&quot;');
});

test('renderItem includes status class, title, description, and source link', () => {
  const html = renderItem('added', 'certification',
    { category: 'DB', value: 'v23', source_url: 'https://docs.oracle.com/x' });
  assert.match(html, /item--added/);
  assert.match(html, /DB/);
  assert.match(html, /href="https:\/\/docs\.oracle\.com\/x"/);
});

test('renderSection emits added, changed and removed groups and skips empty groups', () => {
  const diff = {
    added: [{ title: 'A', description: 'd', source_url: 'https://docs.oracle.com/a' }],
    changed: [],
    removed: [{ title: 'R', description: 'd', source_url: 'https://docs.oracle.com/r' }],
    unchanged: []
  };
  const html = renderSection('whats_new', diff);
  assert.match(html, /item--added/);
  assert.match(html, /item--removed/);
  assert.doesNotMatch(html, /item--changed/);
});

test('renderSection shows an empty-state message when nothing differs', () => {
  const html = renderSection('deprecated', { added: [], changed: [], removed: [], unchanged: [] });
  assert.match(html, /No differences/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL — `Cannot find module '../../js/render.js'`.

- [ ] **Step 3: Write minimal implementation**

```js
// js/render.js
export function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

export function renderItem(status, section, item) {
  const heading = section === 'certification'
    ? `${escapeHtml(item.category)}: ${escapeHtml(item.value)}`
    : escapeHtml(item.title);
  const desc = item.description ? `<p class="item__desc">${escapeHtml(item.description)}</p>` : '';
  return `<article class="item item--${status}">
  <h4 class="item__title">${heading}</h4>
  ${desc}
  <a class="item__source" href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener">Official doc</a>
</article>`;
}

const GROUPS = [['added', 'Added'], ['changed', 'Changed'], ['removed', 'Removed']];

export function renderSection(section, diff) {
  const blocks = [];
  for (const [status, label] of GROUPS) {
    const items = diff[status];
    if (!items.length) continue;
    blocks.push(`<div class="group group--${status}">
  <h3 class="group__label">${label} <span class="group__count">${items.length}</span></h3>
  ${items.map(i => renderItem(status, section, i)).join('\n')}
</div>`);
  }
  if (!blocks.length) return `<p class="empty">No differences in this section.</p>`;
  return blocks.join('\n');
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS (all diff + render tests).

- [ ] **Step 5: Commit**

```bash
git add js/render.js tests/js/render.test.mjs
git commit -m "feat: add pure HTML rendering for diff sections"
```

---

## Task 4: Data-access seam + default-version helper + app bootstrap

**Files:**
- Create: `js/config.js`
- Create: `js/datasource.js`
- Create: `js/app.js`
- Test: `tests/js/datasource.test.mjs`
- Test: `tests/js/diff.test.mjs` (append the `pickDefaultVersions` tests)

`datasource.js` is the **single seam** for all data loading — the only file that
changes when migrating to a Supabase/REST backend later. Its pure path-builders
are unit-tested; the `fetch`-based loaders and `app.js` DOM wiring are verified by
opening the site in Task 5. `pickDefaultVersions` is pure and tested.

- [ ] **Step 1: Create `js/config.js`**

```js
// js/config.js
// Single place to repoint the data source. For a future Supabase/REST backend,
// change DATA_BASE (and the loader bodies in datasource.js) here only.
export const DATA_BASE = 'data';
```

- [ ] **Step 2: Write the failing datasource test**

```js
// tests/js/datasource.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { indexPath, recordPath } from '../../js/datasource.js';

test('indexPath points at the index under the data base', () => {
  assert.equal(indexPath(), 'data/index.json');
});

test('recordPath joins the data base with the record file', () => {
  assert.equal(recordPath('oracle-goldengate/23ai.json'), 'data/oracle-goldengate/23ai.json');
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `npm test`
Expected: FAIL — `Cannot find module '../../js/datasource.js'`.

- [ ] **Step 4: Write `js/datasource.js`**

```js
// js/datasource.js
// The ONLY data-access seam. To move to Supabase/REST later, replace the bodies
// of loadIndex/loadRecord with API calls — app.js and pure logic stay unchanged.
import { DATA_BASE } from './config.js';

export function indexPath() { return `${DATA_BASE}/index.json`; }
export function recordPath(file) { return `${DATA_BASE}/${file}`; }

async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

export async function loadIndex() { return fetchJson(indexPath()); }
export async function loadRecord(file) { return fetchJson(recordPath(file)); }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test`
Expected: PASS (the two datasource path tests).

- [ ] **Step 6: Append the failing `pickDefaultVersions` tests to `tests/js/diff.test.mjs`**

Add this import line at the top of the file (next to the existing import) and the tests below the others:

```js
import { pickDefaultVersions } from '../../js/app.js';

test('pickDefaultVersions returns [previous, latest] by order desc', () => {
  const versions = [
    { version: '21c', order: 1 },
    { version: '23ai', order: 2 },
    { version: '19c', order: 0 }
  ];
  const [older, newer] = pickDefaultVersions(versions);
  assert.equal(newer.version, '23ai');
  assert.equal(older.version, '21c');
});

test('pickDefaultVersions handles a single version', () => {
  const [older, newer] = pickDefaultVersions([{ version: '23ai', order: 2 }]);
  assert.equal(older.version, '23ai');
  assert.equal(newer.version, '23ai');
});
```

- [ ] **Step 7: Run test to verify it fails**

Run: `npm test`
Expected: FAIL — `Cannot find module '../../js/app.js'`.

- [ ] **Step 8: Write `js/app.js`**

```js
// js/app.js
import { diffRecords, SECTIONS } from './diff.js';
import { renderSection } from './render.js';
import { loadIndex, loadRecord } from './datasource.js';

const SECTION_LABELS = {
  certification: 'Certification',
  whats_new: "What's New",
  behavior_changes: 'Behavior Changes',
  deprecated: 'Deprecated',
  desupported: 'Desupported / Removed'
};

export function pickDefaultVersions(versions) {
  const sorted = [...versions].sort((a, b) => b.order - a.order);
  const newer = sorted[0];
  const older = sorted[1] || sorted[0];
  return [older, newer];
}

function fillSelect(select, versions, selectedVersion) {
  select.innerHTML = versions
    .map(v => `<option value="${v.version}" ${v.version === selectedVersion ? 'selected' : ''}>${v.label}</option>`)
    .join('');
}

function renderTabs(container, panels) {
  container.innerHTML = SECTIONS
    .map((s, i) => `<button class="tab ${i === 0 ? 'tab--active' : ''}" data-section="${s}">${SECTION_LABELS[s]}</button>`)
    .join('');
  container.addEventListener('click', (e) => {
    const btn = e.target.closest('.tab');
    if (!btn) return;
    container.querySelectorAll('.tab').forEach(t => t.classList.remove('tab--active'));
    btn.classList.add('tab--active');
    Object.entries(panels).forEach(([section, el]) => {
      el.hidden = section !== btn.dataset.section;
    });
  });
}

async function loadVersion(product, version) {
  const meta = product.versions.find(v => v.version === version);
  return loadRecord(meta.file);
}

function renderComparison(panelsHost, older, newer) {
  const diff = diffRecords(older, newer);
  panelsHost.innerHTML = '';
  const panels = {};
  SECTIONS.forEach((section, i) => {
    const panel = document.createElement('section');
    panel.className = 'panel';
    panel.hidden = i !== 0;
    panel.innerHTML = renderSection(section, diff[section]);
    panelsHost.appendChild(panel);
    panels[section] = panel;
  });
  return panels;
}

async function main() {
  const index = await loadIndex();
  const product = index.products[0]; // v1: GoldenGate only
  const olderSel = document.getElementById('older');
  const newerSel = document.getElementById('newer');
  const tabsHost = document.getElementById('tabs');
  const panelsHost = document.getElementById('panels');
  const updated = document.getElementById('updated');

  const [defOlder, defNewer] = pickDefaultVersions(product.versions);
  fillSelect(olderSel, product.versions, defOlder.version);
  fillSelect(newerSel, product.versions, defNewer.version);

  async function refresh() {
    const [older, newer] = await Promise.all([
      loadVersion(product, olderSel.value),
      loadVersion(product, newerSel.value)
    ]);
    const panels = renderComparison(panelsHost, older, newer);
    renderTabs(tabsHost, panels);
    updated.textContent = `Data last updated: ${newer.last_updated}`;
  }

  olderSel.addEventListener('change', refresh);
  newerSel.addEventListener('change', refresh);
  await refresh();
}

if (typeof document !== 'undefined') {
  main().catch(err => {
    const host = document.getElementById('panels');
    if (host) host.innerHTML = `<p class="error">${err.message}</p>`;
  });
}
```

- [ ] **Step 9: Run test to verify it passes**

Run: `npm test`
Expected: PASS (the two new `pickDefaultVersions` tests plus all prior tests).

- [ ] **Step 10: Commit**

```bash
git add js/config.js js/datasource.js js/app.js tests/js/datasource.test.mjs tests/js/diff.test.mjs
git commit -m "feat: add data-access seam, app bootstrap, and default-version selection"
```

---

## Task 5: HTML shell + Oracle Redwood theme

**Files:**
- Create: `index.html`
- Create: `css/theme.css`

- [ ] **Step 1: Create `index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Oracle Version Diff — GoldenGate</title>
  <link rel="stylesheet" href="css/theme.css" />
</head>
<body>
  <header class="masthead">
    <h1 class="masthead__title">Oracle Version Diff</h1>
    <p class="masthead__subtitle">Oracle GoldenGate — head-to-head release comparison</p>
  </header>

  <main class="container">
    <section class="picker">
      <label class="picker__field">Older
        <select id="older"></select>
      </label>
      <span class="picker__vs">vs</span>
      <label class="picker__field">Newer
        <select id="newer"></select>
      </label>
    </section>

    <nav id="tabs" class="tabs" aria-label="Comparison sections"></nav>
    <div id="panels"></div>
    <p id="updated" class="updated"></p>
  </main>

  <footer class="footer">
    Data sourced from official Oracle documentation (docs.oracle.com).
    Oracle-inspired theme for an educational tool; not affiliated with or endorsed by Oracle.
  </footer>

  <script type="module" src="js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create `css/theme.css`**

```css
:root {
  --oracle-red: #C74634;
  --oracle-red-dark: #A23824;
  --ink: #1A1A1A;
  --slate: #3A3F44;
  --surface: #FFFFFF;
  --bg: #F5F4F2;
  --border: #E0DED9;
  --added: #3C7A3C;
  --changed: #B5760A;
  --removed: #C74634;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: "Helvetica Neue", Arial, sans-serif;
  color: var(--ink);
  background: var(--bg);
  line-height: 1.5;
}

.masthead {
  background: var(--oracle-red);
  color: #fff;
  padding: 1.25rem 1.5rem;
}
.masthead__title { margin: 0; font-size: 1.5rem; font-weight: 700; }
.masthead__subtitle { margin: .25rem 0 0; opacity: .9; font-size: .95rem; }

.container { max-width: 960px; margin: 0 auto; padding: 1.5rem; }

.picker {
  display: flex; align-items: flex-end; gap: 1rem; flex-wrap: wrap;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem;
}
.picker__field { display: flex; flex-direction: column; font-size: .8rem; color: var(--slate); gap: .25rem; }
.picker__field select {
  font-size: 1rem; padding: .4rem .6rem; border: 1px solid var(--border);
  border-radius: 6px; background: #fff; min-width: 8rem;
}
.picker__vs { color: var(--oracle-red); font-weight: 700; padding-bottom: .5rem; }

.tabs { display: flex; flex-wrap: wrap; gap: .25rem; border-bottom: 2px solid var(--border); margin-bottom: 1rem; }
.tab {
  border: none; background: none; padding: .6rem .9rem; cursor: pointer;
  font-size: .95rem; color: var(--slate); border-bottom: 3px solid transparent; margin-bottom: -2px;
}
.tab:hover { color: var(--oracle-red); }
.tab--active { color: var(--oracle-red); border-bottom-color: var(--oracle-red); font-weight: 600; }

.panel { display: block; }
.group { margin-bottom: 1.5rem; }
.group__label { font-size: .85rem; text-transform: uppercase; letter-spacing: .04em; color: var(--slate); margin: 0 0 .5rem; }
.group__count {
  display: inline-block; min-width: 1.4rem; text-align: center; font-size: .75rem;
  background: var(--border); border-radius: 999px; padding: 0 .4rem; margin-left: .25rem; color: var(--ink);
}

.item {
  background: var(--surface); border: 1px solid var(--border); border-left-width: 4px;
  border-radius: 6px; padding: .75rem 1rem; margin-bottom: .5rem;
}
.item--added { border-left-color: var(--added); }
.item--changed { border-left-color: var(--changed); }
.item--removed { border-left-color: var(--removed); }
.item__title { margin: 0 0 .25rem; font-size: 1rem; }
.item__desc { margin: 0 0 .4rem; color: var(--slate); font-size: .92rem; }
.item__source { font-size: .8rem; color: var(--oracle-red); text-decoration: none; }
.item__source:hover { color: var(--oracle-red-dark); text-decoration: underline; }

.empty { color: var(--slate); font-style: italic; }
.error { color: var(--oracle-red-dark); font-weight: 600; }
.updated { color: var(--slate); font-size: .8rem; margin-top: 1.5rem; }
.footer { max-width: 960px; margin: 0 auto; padding: 1.5rem; color: var(--slate); font-size: .78rem; }
```

- [ ] **Step 3: Manual verification**

Run a local static server from the repo root and open it:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/`. Expected: Oracle-red masthead; two dropdowns defaulting to **21c** (older) and **23ai** (newer); five tabs; the "What's New" tab shows "AI vector replication" as an **Added** (green left bar) item with an "Official doc" link; switching tabs works; "Data last updated" line shows at the bottom. Stop the server with Ctrl-C.

- [ ] **Step 4: Commit**

```bash
git add index.html css/theme.css
git commit -m "feat: add HTML shell and Oracle Redwood theme"
```

---

## Task 6: Python pipeline scaffold + schema validation (`pipeline/validate.py`)

**Files:**
- Create: `pipeline/requirements.txt`
- Create: `pipeline/__init__.py` (empty)
- Create: `tests/python/__init__.py` (empty)
- Create: `tests/python/conftest.py`
- Create: `pipeline/validate.py`
- Test: `tests/python/test_validate.py`

- [ ] **Step 1: Create `pipeline/requirements.txt`**

```
requests==2.32.3
beautifulsoup4==4.12.3
jsonschema==4.23.0
pytest==8.3.3
```

- [ ] **Step 2: Install deps and create empty package files**

```bash
python3 -m pip install -r pipeline/requirements.txt
touch pipeline/__init__.py tests/python/__init__.py
```

- [ ] **Step 3: Create `tests/python/conftest.py`**

```python
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

@pytest.fixture
def repo_root():
    return REPO_ROOT

@pytest.fixture
def fixtures_dir():
    return FIXTURES

def read_fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")
```

- [ ] **Step 4: Write the failing test**

```python
# tests/python/test_validate.py
import json
import pytest
from pipeline.validate import validate_record, ValidationFailed

def _good_record():
    return {
        "product": "oracle-goldengate",
        "version": "23ai",
        "release_label": "Oracle GoldenGate 23ai",
        "last_updated": "2026-05-30",
        "sections": {
            "certification": [{"category": "DB", "value": "23ai", "source_url": "https://docs.oracle.com/x"}],
            "whats_new": [], "behavior_changes": [], "deprecated": [], "desupported": []
        },
    }

def test_valid_record_passes():
    validate_record(_good_record())  # must not raise

def test_missing_section_fails():
    rec = _good_record()
    del rec["sections"]["deprecated"]
    with pytest.raises(ValidationFailed):
        validate_record(rec)

def test_bad_source_url_fails():
    rec = _good_record()
    rec["sections"]["certification"][0]["source_url"] = "not-a-url"
    with pytest.raises(ValidationFailed):
        validate_record(rec)
```

- [ ] **Step 5: Run test to verify it fails**

Run: `python3 -m pytest tests/python/test_validate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.validate'`.

- [ ] **Step 6: Write `pipeline/validate.py`**

```python
import json
import pathlib
from jsonschema import Draft7Validator, FormatChecker

SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[1] / "schema" / "version-record.schema.json"

class ValidationFailed(Exception):
    pass

def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

def validate_record(record):
    validator = Draft7Validator(_load_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(record), key=lambda e: e.path)
    if errors:
        messages = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
        raise ValidationFailed(messages)
```

- [ ] **Step 7: Run test to verify it passes**

Run: `python3 -m pytest tests/python/test_validate.py -v`
Expected: PASS (3 tests).

- [ ] **Step 8: Commit**

```bash
git add pipeline/requirements.txt pipeline/__init__.py pipeline/validate.py tests/python/
git commit -m "feat: add pipeline scaffold and JSON schema validation"
```

---

## Task 7: HTML parsers (`pipeline/parse.py`)

**Files:**
- Create: `tests/python/fixtures/whats_new.html`
- Create: `tests/python/fixtures/certification.html`
- Create: `pipeline/parse.py`
- Test: `tests/python/test_parse.py`

Oracle doc pages for features follow a heading-then-paragraph pattern; certification appears in a table. The fixtures below encode that representative structure. **Selector calibration against the live pages happens in Task 11** — when real HTML is saved over these fixtures, only the CSS selectors in `parse.py` may need adjusting; the tested contract (what the functions return) stays the same.

- [ ] **Step 1: Create `tests/python/fixtures/whats_new.html`**

```html
<html><body>
<div class="sect1" id="whats-new">
  <h2>What's New</h2>
  <div class="sect2">
    <h3>AI vector replication</h3>
    <p>Support for replicating vector data types.</p>
  </div>
  <div class="sect2">
    <h3>Parallel Replicat improvements</h3>
    <p>Better throughput for large transactions.</p>
  </div>
</div>
</body></html>
```

- [ ] **Step 2: Create `tests/python/fixtures/certification.html`**

```html
<html><body>
<table class="certmatrix">
  <thead><tr><th>Component</th><th>Supported</th></tr></thead>
  <tbody>
    <tr><td>Oracle Database</td><td>Oracle Database 23ai</td></tr>
    <tr><td>Operating System</td><td>Oracle Linux 8, 9</td></tr>
  </tbody>
</table>
</body></html>
```

- [ ] **Step 3: Write the failing test**

```python
# tests/python/test_parse.py
from conftest import read_fixture
from pipeline.parse import parse_feature_list, parse_certification

SRC = "https://docs.oracle.com/x"

def test_parse_feature_list_extracts_title_and_description():
    items = parse_feature_list(read_fixture("whats_new.html"), source_url=SRC)
    assert items[0] == {
        "title": "AI vector replication",
        "description": "Support for replicating vector data types.",
        "source_url": SRC,
    }
    assert len(items) == 2

def test_parse_certification_extracts_category_value_rows():
    items = parse_certification(read_fixture("certification.html"), source_url=SRC)
    assert {"category": "Oracle Database", "value": "Oracle Database 23ai", "source_url": SRC} in items
    assert len(items) == 2
```

- [ ] **Step 4: Run test to verify it fails**

Run: `python3 -m pytest tests/python/test_parse.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.parse'`.

- [ ] **Step 5: Write `pipeline/parse.py`**

```python
from bs4 import BeautifulSoup

def _text(node):
    return " ".join(node.get_text(" ", strip=True).split())

def parse_feature_list(html, source_url, heading="h3"):
    """Extract feature items: each `heading` is a title, the next <p> its description."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for h in soup.find_all(heading):
        title = _text(h)
        if not title:
            continue
        desc_node = h.find_next("p")
        description = _text(desc_node) if desc_node else ""
        items.append({"title": title, "description": description, "source_url": source_url})
    return items

def parse_certification(html, source_url):
    """Extract certification rows from the first 2-column table body."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    table = soup.find("table")
    if not table:
        return items
    body = table.find("tbody") or table
    for row in body.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        items.append({
            "category": _text(cells[0]),
            "value": _text(cells[1]),
            "source_url": source_url,
        })
    return items
```

- [ ] **Step 6: Run test to verify it passes**

Run: `python3 -m pytest tests/python/test_parse.py -v`
Expected: PASS (2 tests).

- [ ] **Step 7: Commit**

```bash
git add pipeline/parse.py tests/python/test_parse.py tests/python/fixtures/whats_new.html tests/python/fixtures/certification.html
git commit -m "feat: add Oracle doc HTML parsers with fixtures"
```

---

## Task 8: Version detection (`pipeline/detect.py`)

**Files:**
- Create: `tests/python/fixtures/docs_index.html`
- Create: `pipeline/detect.py`
- Test: `tests/python/test_detect.py`

`detect_versions` reads the GoldenGate docs landing page and extracts version labels from links, so the pipeline can flag a version that isn't yet in our data.

- [ ] **Step 1: Create `tests/python/fixtures/docs_index.html`**

```html
<html><body>
<ul>
  <li><a href="/en/middleware/goldengate/core/23/">Oracle GoldenGate 23ai</a></li>
  <li><a href="/en/middleware/goldengate/core/21.3/">Oracle GoldenGate 21c</a></li>
  <li><a href="/en/middleware/goldengate/core/19.1/">Oracle GoldenGate 19c</a></li>
  <li><a href="/some/other/link">Documentation Home</a></li>
</ul>
</body></html>
```

- [ ] **Step 2: Write the failing test**

```python
# tests/python/test_detect.py
from conftest import read_fixture
from pipeline.detect import detect_versions

def test_detect_versions_extracts_goldengate_labels():
    found = detect_versions(read_fixture("docs_index.html"))
    assert found == ["23ai", "21c", "19c"]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m pytest tests/python/test_detect.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.detect'`.

- [ ] **Step 4: Write `pipeline/detect.py`**

```python
import re
from bs4 import BeautifulSoup

# Matches "Oracle GoldenGate 23ai" / "... 21c" / "... 19c" and captures the version token.
_VER_RE = re.compile(r"Oracle GoldenGate\s+(\d+[a-z]+)", re.IGNORECASE)

def detect_versions(html):
    """Return version tokens (e.g. '23ai') in document order, de-duplicated."""
    soup = BeautifulSoup(html, "html.parser")
    seen = []
    for a in soup.find_all("a"):
        m = _VER_RE.search(a.get_text(" ", strip=True))
        if m and m.group(1) not in seen:
            seen.append(m.group(1))
    return seen
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest tests/python/test_detect.py -v`
Expected: PASS (1 test).

- [ ] **Step 6: Commit**

```bash
git add pipeline/detect.py tests/python/test_detect.py tests/python/fixtures/docs_index.html
git commit -m "feat: add GoldenGate version detection from docs index"
```

---

## Task 9: Source registry + build orchestrator (`pipeline/sources.py`, `pipeline/build.py`)

**Files:**
- Create: `pipeline/sources.py`
- Create: `pipeline/build.py`
- Test: `tests/python/test_build.py`

`build_record` and `write_outputs` take an injected `fetch(url) -> html` function so they are testable without network. `sources.py` is the ordered registry the maintainer edits when a new version's URLs are known.

- [ ] **Step 1: Create `pipeline/sources.py`**

```python
# Ordered oldest -> newest. `order` for index.json is derived from this list position.
PRODUCT_ID = "oracle-goldengate"
PRODUCT_LABEL = "Oracle GoldenGate"
DOCS_INDEX_URL = "https://docs.oracle.com/en/middleware/goldengate/index.html"

# version -> { release_label, urls: { section: url } }
SOURCES = {
    "21c": {
        "release_label": "Oracle GoldenGate 21c",
        "urls": {
            "certification": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/certification.html",
            "whats_new": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html",
            "behavior_changes": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html",
            "deprecated": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html",
            "desupported": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html",
        },
    },
    "23ai": {
        "release_label": "Oracle GoldenGate 23ai",
        "urls": {
            "certification": "https://docs.oracle.com/en/middleware/goldengate/core/23/certification.html",
            "whats_new": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html",
            "behavior_changes": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html",
            "deprecated": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html",
            "desupported": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html",
        },
    },
}

VERSION_ORDER = list(SOURCES.keys())  # position == display order (higher index = newer)
```

> Note: the four feature sections currently point at the same `whats-new` page; calibration (Task 11) splits "behavior changes / deprecated / desupported" onto their real pages and tunes the `heading` selector per page. The contract and tests do not change.

- [ ] **Step 2: Write the failing test**

```python
# tests/python/test_build.py
import json
from conftest import read_fixture
from pipeline.build import build_record, write_outputs

def fake_fetch_factory():
    pages = {
        "cert": read_fixture("certification.html"),
        "feat": read_fixture("whats_new.html"),
    }
    def fetch(url):
        return pages["cert"] if "cert" in url else pages["feat"]
    return fetch

def _sources_one():
    return {
        "23ai": {
            "release_label": "Oracle GoldenGate 23ai",
            "urls": {
                "certification": "https://docs.oracle.com/cert",
                "whats_new": "https://docs.oracle.com/feat",
                "behavior_changes": "https://docs.oracle.com/feat",
                "deprecated": "https://docs.oracle.com/feat",
                "desupported": "https://docs.oracle.com/feat",
            },
        }
    }

def test_build_record_produces_valid_structure():
    rec = build_record("23ai", _sources_one()["23ai"], fetch=fake_fetch_factory(), today="2026-05-30")
    assert rec["product"] == "oracle-goldengate"
    assert rec["version"] == "23ai"
    assert rec["last_updated"] == "2026-05-30"
    assert len(rec["sections"]["certification"]) == 2
    assert rec["sections"]["whats_new"][0]["title"] == "AI vector replication"

def test_write_outputs_writes_records_and_index(tmp_path):
    sources = _sources_one()
    write_outputs(sources, ["23ai"], fetch=fake_fetch_factory(), data_dir=tmp_path, today="2026-05-30")
    rec_file = tmp_path / "oracle-goldengate" / "23ai.json"
    index_file = tmp_path / "index.json"
    assert rec_file.exists()
    index = json.loads(index_file.read_text())
    versions = index["products"][0]["versions"]
    assert versions[0]["version"] == "23ai"
    assert versions[0]["order"] == 0
    assert versions[0]["file"] == "oracle-goldengate/23ai.json"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m pytest tests/python/test_build.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.build'`.

- [ ] **Step 4: Write `pipeline/build.py`**

```python
import datetime
import json
import pathlib

import requests

from pipeline import sources as sources_mod
from pipeline.parse import parse_feature_list, parse_certification
from pipeline.validate import validate_record

FEATURE_SECTIONS = ("whats_new", "behavior_changes", "deprecated", "desupported")

def http_fetch(url):
    resp = requests.get(url, timeout=30, headers={"User-Agent": "oracle-version-diff/0.1"})
    resp.raise_for_status()
    return resp.text

def build_record(version, source_entry, fetch=http_fetch, today=None):
    today = today or datetime.date.today().isoformat()
    urls = source_entry["urls"]
    sections = {
        "certification": parse_certification(fetch(urls["certification"]), urls["certification"]),
    }
    for section in FEATURE_SECTIONS:
        sections[section] = parse_feature_list(fetch(urls[section]), urls[section])
    record = {
        "product": sources_mod.PRODUCT_ID,
        "version": version,
        "release_label": source_entry["release_label"],
        "last_updated": today,
        "sections": sections,
    }
    validate_record(record)
    return record

def write_outputs(sources, version_order, fetch=http_fetch, data_dir=None, today=None):
    data_dir = pathlib.Path(data_dir)
    product_dir = data_dir / sources_mod.PRODUCT_ID
    product_dir.mkdir(parents=True, exist_ok=True)

    versions_index = []
    # newest first in the index; order int: higher = newer
    for order, version in enumerate(version_order):
        record = build_record(version, sources[version], fetch=fetch, today=today)
        (product_dir / f"{version}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        versions_index.append({
            "version": version,
            "label": version,
            "order": order,
            "file": f"{sources_mod.PRODUCT_ID}/{version}.json",
        })
    versions_index.sort(key=lambda v: v["order"], reverse=True)

    index = {"products": [{
        "id": sources_mod.PRODUCT_ID,
        "label": sources_mod.PRODUCT_LABEL,
        "versions": versions_index,
    }]}
    (data_dir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

def main():
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    write_outputs(
        sources_mod.SOURCES,
        sources_mod.VERSION_ORDER,
        data_dir=repo_root / "data",
    )

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest tests/python/test_build.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Run the full suites**

Run: `python3 -m pytest tests/python/ -v && npm test`
Expected: all Python and JS tests PASS.

- [ ] **Step 7: Commit**

```bash
git add pipeline/sources.py pipeline/build.py tests/python/test_build.py
git commit -m "feat: add source registry and build orchestrator"
```

---

## Task 10: Scheduled GitHub Action (fetch → PR)

**Files:**
- Create: `.github/workflows/refresh-data.yml`

- [ ] **Step 1: Create `.github/workflows/refresh-data.yml`**

```yaml
name: Refresh GoldenGate data

on:
  schedule:
    - cron: "0 6 * * 1"   # Mondays 06:00 UTC
  workflow_dispatch: {}

permissions:
  contents: write
  pull-requests: write

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: python -m pip install -r pipeline/requirements.txt

      - name: Run test suite
        run: python -m pytest tests/python/ -q

      - name: Rebuild data from official docs
        run: python -m pipeline.build

      - name: Open pull request with refreshed data
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "data: refresh GoldenGate comparison data"
          branch: data/refresh
          title: "Data refresh: GoldenGate comparison"
          body: |
            Automated refresh of GoldenGate comparison data from official Oracle docs.
            Review the diff before merging — a parser/selector drift would show up here.
          labels: data-refresh
```

- [ ] **Step 2: Verify the workflow is valid YAML**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/refresh-data.yml')); print('valid yaml')"`
Expected: prints `valid yaml`. (If `yaml` is missing: `python3 -m pip install pyyaml` first.)

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/refresh-data.yml
git commit -m "ci: add scheduled data-refresh workflow that opens a PR"
```

> Manual verification (after the repo is pushed to GitHub): trigger the workflow via the Actions tab → "Run workflow" (workflow_dispatch) and confirm it opens a PR. This requires the live repo and is done in Task 11.

---

## Task 11: README, GitHub Pages enablement, and live calibration

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

````markdown
# Oracle Version Diff

A static website that compares two Oracle GoldenGate versions head-to-head —
certification, what's new, behavior changes, deprecated, and desupported features —
using data parsed from official Oracle documentation.

## How it works

- **Front-end** (`index.html`, `css/`, `js/`): vanilla static site. Loads JSON from
  `data/` through a single data-access seam (`js/datasource.js`, configured in
  `js/config.js`) and renders an Added/Changed/Removed diff. No backend.

## Future backend (Supabase-ready)

v1 is intentionally static. All data loading is isolated in `js/datasource.js`, and
the JSON schema is relational-shaped, so a future move to Supabase (Postgres + Auth +
REST) only requires changing that one module — unlocking features like update-email
subscriptions, saved comparisons, community notes, and search. See the design spec
§9a for details.
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

> Oracle-inspired theme for an educational tool. Not affiliated with or endorsed by Oracle.
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with dev, deploy, and update instructions"
```

- [ ] **Step 3: Live calibration (requires the pushed repo + network)**

This step replaces the representative fixtures with real saved HTML and tunes the
selectors. Do this once the repo is on GitHub:

1. For each URL in `pipeline/sources.py`, open it and **Save Page As → HTML**, then
   copy the relevant section into the matching fixture
   (`tests/python/fixtures/whats_new.html`, `certification.html`, `docs_index.html`).
2. Re-run `python3 -m pytest tests/python/ -v`. If a parser test fails, adjust **only**
   the CSS selectors / `heading` level in `pipeline/parse.py` and `detect.py` until the
   tests pass against the real markup. The function contracts (return shapes) stay fixed.
3. Split the feature-section URLs in `sources.py` onto their real pages (the live
   "behavior changes", "deprecated", and "desupported" sections may live on separate
   pages or anchors rather than the single `whats-new` page).
4. Run `python3 -m pipeline.build` locally and open the site to confirm real data renders.
5. Push, then in the GitHub Actions tab use **Run workflow** on "Refresh GoldenGate data"
   and confirm it opens a PR.

- [ ] **Step 4: Commit any calibration changes**

```bash
git add tests/python/fixtures/ pipeline/parse.py pipeline/detect.py pipeline/sources.py
git commit -m "chore: calibrate parsers and fixtures against live Oracle docs"
```

---

## Self-Review

**Spec coverage:**
- §1 single job (pick two versions → comparison): Tasks 4, 5 (UX), 2 (diff). ✔
- §2 official sources only / no live browser fetch: Tasks 7, 9 (build-time fetch), 5 (front-end only reads local JSON). ✔
- §3a pipeline (detect → fetch → parse → validate → PR): Tasks 6–10. ✔
- §3b static front-end reads JSON: Tasks 4, 5. ✔
- §4 data model: Task 1 (schema + sample), enforced in Tasks 6, 9. ✔
- §5 five sections: Task 1 schema, Task 2 `SECTIONS`, Task 4 labels. ✔
- §6 UX (two dropdowns, default latest-vs-previous, tabs, Added/Changed/Removed, sources, last-updated footer): Tasks 4, 5. ✔
- §6a Oracle Redwood theme + provenance links: Task 5 (`theme.css`), Task 3 (source links). ✔
- §7 GitHub Pages + Actions, no secrets beyond default token: Tasks 10, 11. ✔
- §8 testing (parser fixtures, schema validation gate, front-end fixture render): Tasks 2–3 (JS), 6 (schema), 7–9 (Python). ✔
- §9 out of scope honored (GoldenGate only, no MOS, no live fetch, no accounts). ✔

**Placeholder scan:** No TBD/TODO; every code step includes complete code; the "calibration" step is a deliberate, explicit live-tuning task, not a placeholder.

**Type consistency:** Data loading goes only through `datasource.js` (`loadIndex`/`loadRecord`, with pure `indexPath`/`recordPath`); `app.js` wraps it as `loadVersion(product, version)` and no longer defines its own `fetchJson`. `SECTIONS` order is identical in `diff.js` (Task 2) and `app.js` labels (Task 4). Record shape (`product`/`version`/`release_label`/`last_updated`/`sections`) matches across schema (Task 1), `build_record` (Task 9), and JS consumers. `keyFor`/`diffSection`/`diffRecords`/`renderSection`/`renderItem`/`pickDefaultVersions` signatures are consistent between definitions and call sites. Index record fields (`version`/`label`/`order`/`file`) match between `index.json` (Task 1), `write_outputs` (Task 9), and `app.js` (Task 4).
