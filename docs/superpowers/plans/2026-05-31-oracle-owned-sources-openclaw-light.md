# Oracle-Owned Sources And OpenClaw Light Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Oracle-owned domains valid content sources and switch the app to an OpenClaw-inspired light card theme while preserving the current GitHub dark theme as a fallback.

**Architecture:** Keep the app static and JSON-driven. Add source-host validation in JS tests, split CSS into one default light theme and one fallback dark theme, and update copy so the app says it uses Oracle-owned sources rather than only `docs.oracle.com`.

**Tech Stack:** Vanilla HTML/CSS/JS ES modules, Node test runner, Python JSON schema validation, static JSON data.

---

### Task 1: Source Policy Tests

**Files:**
- Modify: `tests/js/data.test.mjs`

- [ ] **Step 1: Add Oracle-owned host helpers and tests**

Add this helper and test after the `index` constant:

```js
function sourceHostsForProduct(productId) {
  const product = index.products.find(p => p.id === productId);
  assert.ok(product, `missing product ${productId}`);
  return product.versions.flatMap(version => {
    const record = JSON.parse(readFileSync(`data/${version.file}`, 'utf8'));
    return ['certification', 'whats_new', 'behavior_changes', 'deprecated', 'desupported']
      .flatMap(section => record.sections[section] || [])
      .map(item => new URL(item.source_url).hostname);
  });
}

function isOracleOwnedHost(hostname) {
  return hostname === 'oracle.com' || hostname.endsWith('.oracle.com');
}

test('curated Database and WebLogic records use Oracle-owned source hosts', () => {
  const hosts = [
    ...sourceHostsForProduct('oracle-database'),
    ...sourceHostsForProduct('oracle-weblogic-server')
  ];

  assert.ok(hosts.length > 0);
  assert.deepEqual(hosts.filter(host => !isOracleOwnedHost(host)), []);
});
```

- [ ] **Step 2: Run the focused test and verify it passes or fails for the right reason**

Run:

```bash
npm test
```

Expected at this point: the test should pass because current curated data already uses Oracle-owned hosts. If it fails, the failure must name a non-Oracle host and the next step is to replace that source URL with an Oracle-owned URL before continuing.

### Task 2: Theme File Split Tests

**Files:**
- Modify: `tests/js/theme.test.mjs`

- [ ] **Step 1: Replace single-theme assertions with explicit light/default and dark/fallback assertions**

Replace the current file body with:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const lightCss = readFileSync('css/theme-openclaw-light.css', 'utf8');
const darkCss = readFileSync('css/theme-github-dark.css', 'utf8');
const html = readFileSync('index.html', 'utf8');

test('hidden comparison panels stay hidden when tabs switch sections', () => {
  assert.match(lightCss, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
  assert.match(darkCss, /\.panel\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
});

test('index uses OpenClaw-inspired light theme by default', () => {
  assert.match(html, /href="css\/theme-openclaw-light\.css"/);
  assert.doesNotMatch(html, /href="css\/theme\.css"/);
});

test('fallback GitHub dark theme is preserved', () => {
  assert.match(darkCss, /--bg:\s*#0d1117;/i);
  assert.match(darkCss, /--surface:\s*#161b22;/i);
  assert.match(darkCss, /--surface-raised:\s*#21262d;/i);
  assert.match(darkCss, /--border:\s*#30363d;/i);
  assert.match(darkCss, /--ink:\s*#e6edf3;/i);
  assert.match(darkCss, /--accent:\s*#2f81f7;/i);
});

test('OpenClaw light theme uses warm light cards and dark source buttons', () => {
  assert.match(lightCss, /--bg:\s*#fbfaf6;/i);
  assert.match(lightCss, /--surface:\s*#ffffff;/i);
  assert.match(lightCss, /--ink:\s*#111827;/i);
  assert.match(lightCss, /--button:\s*#1f2937;/i);
});
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
npm test
```

Expected: FAIL because `css/theme-openclaw-light.css` and `css/theme-github-dark.css` do not exist yet and `index.html` still references `css/theme.css`.

### Task 3: Split And Apply Themes

**Files:**
- Create: `css/theme-github-dark.css`
- Create: `css/theme-openclaw-light.css`
- Modify: `index.html`
- Delete or leave unused: `css/theme.css`

- [ ] **Step 1: Preserve the current dark theme**

Copy the full current contents of `css/theme.css` into a new file named `css/theme-github-dark.css`.

- [ ] **Step 2: Create the OpenClaw-inspired light theme**

Create `css/theme-openclaw-light.css` using the same selectors as the current theme. Use these root tokens:

```css
:root {
  --oracle-red: #C74634;
  --accent: #111827;
  --ink: #111827;
  --muted: #6B6258;
  --muted-strong: #3F3A34;
  --surface: #FFFFFF;
  --surface-soft: #F3EFE7;
  --surface-raised: #FFFDF8;
  --bg: #FBFAF6;
  --border: #E6DFD4;
  --border-strong: #CFC5B8;
  --button: #1F2937;
  --button-hover: #111827;
  --focus: #C74634;
  --shadow: 0 18px 44px rgba(75, 63, 48, .10);
}
```

Keep the existing class structure, with these visual adjustments:

```css
body {
  background:
    radial-gradient(circle at top left, rgba(199, 70, 52, .08), transparent 28rem),
    var(--bg);
}

.masthead {
  padding-top: 2.75rem;
}

.masthead__title {
  color: var(--ink);
}

.picker,
.delta-summary,
.item,
.tab {
  background: var(--surface);
  border-color: var(--border);
  box-shadow: var(--shadow);
}

.picker,
.delta-summary,
.item {
  border-radius: 8px;
}

.picker__field select {
  background: var(--surface-raised);
  border-color: var(--border);
  color: var(--ink);
}

.tab {
  color: var(--muted);
}

.tab--active {
  color: #FFFFFF;
  background: var(--ink);
  border-color: var(--ink);
}

.item__version {
  color: rgba(17, 24, 39, .18);
}

.item__source {
  background: var(--button);
  border-color: var(--button);
  color: #FFFFFF;
}

.item__source:hover {
  background: var(--button-hover);
  border-color: var(--button-hover);
}
```

- [ ] **Step 3: Point the app to the light theme**

Change the stylesheet link in `index.html`:

```html
<link rel="stylesheet" href="css/theme-openclaw-light.css" />
```

- [ ] **Step 4: Update footer source copy**

Change the footer text in `index.html` to:

```html
Release delta data sourced from Oracle-owned web properties (oracle.com).
Oracle-inspired theme for an educational tool; not affiliated with or endorsed by Oracle.
```

- [ ] **Step 5: Run JS tests**

Run:

```bash
npm test
```

Expected: PASS.

### Task 4: README And Handover Copy

**Files:**
- Modify: `README.md`
- Modify: `docs/HANDOVER.md`

- [ ] **Step 1: Update README front-end and source wording**

Change the front-end bullet to say:

```md
- **Front-end** (`index.html`, `css/`, `js/`): vanilla static site with an
  OpenClaw-inspired light card UI and a preserved GitHub dark fallback theme.
  Loads JSON from `data/` through a single data-access seam (`js/datasource.js`,
  configured in `js/config.js`) and renders one combined list of release-note
  items introduced after the current release through the target release. No backend.
```

Change the opening sentence to:

```md
A static website that shows what changed after a current Oracle release through a
target release, using data sourced from Oracle-owned web properties.
```

Add this paragraph in `Updating data` after the seed-record paragraph:

```md
Curated records may use any Oracle-owned source host (`oracle.com` or a subdomain
such as `docs.oracle.com` or `blogs.oracle.com`). Each record keeps its exact
`source_url` visible through the Official source button.
```

- [ ] **Step 2: Update handover theme/source wording**

In `docs/HANDOVER.md`, replace the current theme bullet with:

```md
- OpenClaw-inspired light card theme is the default (`css/theme-openclaw-light.css`);
  the prior GitHub dark theme is preserved as `css/theme-github-dark.css` for a
  one-line fallback in `index.html`.
```

Add this source-policy bullet near the curated product notes:

```md
- Source policy is Oracle-owned web properties: `oracle.com` or any subdomain.
  Curated Database and WebLogic tests reject non-Oracle source hosts.
```

- [ ] **Step 3: Run JS tests**

Run:

```bash
npm test
```

Expected: PASS.

### Task 5: Verification And Commit

**Files:**
- All files touched above

- [ ] **Step 1: Run full JS test suite**

Run:

```bash
npm test
```

Expected: `pass 5`, `fail 0`.

- [ ] **Step 2: Run Python tests**

Run:

```bash
.venv/bin/python -m pytest tests/python/ -q
```

Expected: `23 passed`.

- [ ] **Step 3: Run data schema validation**

Run:

```bash
.venv/bin/python -c "import json, pathlib; from pipeline.validate import validate_record; [validate_record(json.loads(p.read_text())) for p in pathlib.Path('data').glob('*/*.json')]; print('validated data records')"
```

Expected: `validated data records`.

- [ ] **Step 4: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit code `0`.

- [ ] **Step 5: Run static smoke checks**

Run:

```bash
python3 -m http.server 8000
```

In another command, run:

```bash
curl -sSf http://127.0.0.1:8000/index.html | rg "theme-openclaw-light|Oracle-owned"
curl -sSf http://127.0.0.1:8000/css/theme-openclaw-light.css | rg "#FBFAF6|#1F2937"
curl -sSf http://127.0.0.1:8000/css/theme-github-dark.css | rg "#0D1117|#161B22"
```

Expected: each command prints matching lines.

- [ ] **Step 6: Commit**

Run:

```bash
git add index.html css/theme-openclaw-light.css css/theme-github-dark.css README.md docs/HANDOVER.md tests/js/data.test.mjs tests/js/theme.test.mjs
git commit -m "feat: apply oracle source policy and light theme"
```

- [ ] **Step 7: Push and PR check**

Run:

```bash
git push
gh pr view 9 --repo jollylengkono/oracle-version-diff --json number,state,mergeable,mergeStateStatus,url,headRefOid
```

Expected: if PR #9 is still open, it updates and becomes `MERGEABLE` / `CLEAN`. If PR #9 has already been merged, create a new PR from `feat/legacy-baselines-redwood-console` to `master`.
