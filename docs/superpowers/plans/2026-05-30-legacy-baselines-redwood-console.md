# Legacy Baselines and Redwood Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add curated GoldenGate `19c`/`21c` baseline records so comparisons like `19c -> 23.26.2.0.0` work, and replace the current light UI with the selected dark Redwood Console style.

**Architecture:** Keep the static JSON architecture. Baseline records live in `pipeline/sources.py` as curated public-doc-backed records and are emitted by `pipeline.build` alongside parsed rolling release records. The front end continues to load all JSON records and uses `aggregateRange()` over index order/date order, then renders the same aggregated sections in a dark console UI.

**Tech Stack:** Vanilla ES modules, CSS custom properties, JSON schema draft-07, Python pipeline with pytest, Node `node:test`.

---

## File Structure

- Modify `schema/version-record.schema.json`: require/allow `record_type` with values `baseline` and `release`.
- Modify `pipeline/sources.py`: add `LEGACY_BASELINES` for `19c` and `21c`.
- Modify `pipeline/build.py`: stamp parsed records with `record_type: "release"` and include baselines in `write_release_outputs()`.
- Modify generated data:
  - `data/index.json`
  - `data/oracle-goldengate/19c.json`
  - `data/oracle-goldengate/21c.json`
  - existing generated release JSON files, each gaining `record_type`.
- Modify `js/diff.js`: make `aggregateRange()` use record/index order explicitly for baseline-to-release ranges.
- Modify `js/app.js`: default older version should prefer latest baseline when available and latest release as newer.
- Modify `js/render.js`: render baseline/release badges cleanly in the aggregated list.
- Replace `css/theme.css`: dark Redwood Console tokens and layout polish.
- Modify `index.html`: compact console header/command copy.
- Tests:
  - `tests/python/test_validate.py`
  - `tests/python/test_release_build.py`
  - `tests/js/diff.test.mjs`
  - `tests/js/render.test.mjs`

## Task 1: Schema and Curated Baseline Data

**Files:**
- Modify: `schema/version-record.schema.json`
- Modify: `pipeline/sources.py`
- Modify: `pipeline/build.py`
- Test: `tests/python/test_validate.py`
- Test: `tests/python/test_release_build.py`

- [ ] **Step 1: Write the failing schema test**

Add this to `tests/python/test_validate.py`:

```python
def test_missing_record_type_fails():
    rec = _good_record()
    del rec["record_type"]
    with pytest.raises(ValidationFailed):
        validate_record(rec)

def test_bad_record_type_fails():
    rec = _good_record()
    rec["record_type"] = "snapshot"
    with pytest.raises(ValidationFailed):
        validate_record(rec)
```

Also update `_good_record()` to include:

```python
"record_type": "release",
```

- [ ] **Step 2: Run schema tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/python/test_validate.py -q
```

Expected: FAIL because `record_type` is not required or validated yet.

- [ ] **Step 3: Update schema**

In `schema/version-record.schema.json`, add `record_type` to `required`:

```json
"required": ["product", "version", "release_label", "record_type", "released", "last_updated", "sections"]
```

Add the property:

```json
"record_type": { "type": "string", "enum": ["baseline", "release"] },
```

- [ ] **Step 4: Run schema tests to verify pass**

Run:

```bash
.venv/bin/python -m pytest tests/python/test_validate.py -q
```

Expected: PASS.

- [ ] **Step 5: Write failing build test for legacy baselines**

Add this to `tests/python/test_release_build.py`:

```python
def test_build_records_includes_curated_legacy_baselines():
    recs = build_records(fake_fetch_factory(), BASE, today="2026-05-30")
    versions = [r["version"] for r in recs]

    assert versions[-2:] == ["21c", "19c"]
    assert next(r for r in recs if r["version"] == "19c")["record_type"] == "baseline"
    assert next(r for r in recs if r["version"] == "23.26.2.0.0")["record_type"] == "release"
```

- [ ] **Step 6: Run build test to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/python/test_release_build.py::test_build_records_includes_curated_legacy_baselines -q
```

Expected: FAIL because baselines are not emitted yet.

- [ ] **Step 7: Add curated baselines**

In `pipeline/sources.py`, add:

```python
LEGACY_BASELINES = [
    {
        "product": PRODUCT_ID,
        "version": "19c",
        "release_label": "Oracle GoldenGate 19c",
        "record_type": "baseline",
        "released": "2019-01-01",
        "sections": {
            "certification": [],
            "whats_new": [],
            "behavior_changes": [],
            "deprecated": [],
            "desupported": [],
        },
    },
    {
        "product": PRODUCT_ID,
        "version": "21c",
        "release_label": "Oracle GoldenGate 21c",
        "record_type": "baseline",
        "released": "2021-01-01",
        "sections": {
            "certification": [],
            "whats_new": [],
            "behavior_changes": [],
            "deprecated": [],
            "desupported": [],
        },
    },
]
```

- [ ] **Step 8: Emit `record_type` and baselines**

In `pipeline/build.py`, add `record_type: "release"` to parsed records:

```python
record = {
    "product": sources_mod.PRODUCT_ID,
    "version": version,
    "release_label": labels[version],
    "record_type": "release",
    "released": released[version],
    "last_updated": today,
    "sections": sections,
}
```

At the end of `build_records()`, merge sorted release records with baselines:

```python
release_records = sorted(records, key=lambda r: r["released"], reverse=True)
baselines = []
for baseline in sources_mod.LEGACY_BASELINES:
    record = {**baseline, "last_updated": today}
    validate_record(record)
    baselines.append(record)
return release_records + sorted(baselines, key=lambda r: r["released"], reverse=True)
```

In `write_release_outputs()`, add `record_type` to index entries:

```python
"record_type": record["record_type"],
```

- [ ] **Step 9: Run targeted Python tests**

Run:

```bash
.venv/bin/python -m pytest tests/python/test_validate.py tests/python/test_release_build.py -q
```

Expected: PASS.

## Task 2: Front-End Range Defaults and Baseline Aggregation

**Files:**
- Modify: `js/app.js`
- Modify: `js/diff.js`
- Test: `tests/js/diff.test.mjs`

- [ ] **Step 1: Write failing default-selection test**

Add this to `tests/js/diff.test.mjs` near the existing `pickDefaultVersions` tests:

```js
test('pickDefaultVersions chooses latest baseline as older and latest release as newer', () => {
  const versions = [
    { version: '23.26.2.0.0', order: 18, record_type: 'release' },
    { version: '23.26.1.0.0', order: 17, record_type: 'release' },
    { version: '21c', order: 2, record_type: 'baseline' },
    { version: '19c', order: 1, record_type: 'baseline' }
  ];

  const [older, newer] = pickDefaultVersions(versions);

  assert.equal(older.version, '21c');
  assert.equal(newer.version, '23.26.2.0.0');
});
```

- [ ] **Step 2: Run JS tests to verify failure**

Run:

```bash
node tests/js/diff.test.mjs
```

Expected: FAIL because current default selects previous release, not latest baseline.

- [ ] **Step 3: Update `pickDefaultVersions()`**

Replace `pickDefaultVersions()` in `js/app.js` with:

```js
export function pickDefaultVersions(versions) {
  const sorted = [...versions].sort((a, b) => b.order - a.order);
  const newer = sorted.find(v => v.record_type === 'release') || sorted[0];
  const older = sorted.find(v => v.record_type === 'baseline') || sorted[1] || sorted[0];
  return [older, newer];
}
```

- [ ] **Step 4: Write baseline range aggregation test**

Add this to `tests/js/diff.test.mjs`:

```js
test('aggregateRange includes release items between baseline and modern release', () => {
  const records = [
    { version: '23.6', release_label: 'Release 23.6', record_type: 'release', released: '2024-10-01', sections: { whats_new: [{ title: '23.6 item' }], behavior_changes: [], deprecated: [] } },
    { version: '23.5', release_label: 'Release 23.5', record_type: 'release', released: '2024-07-01', sections: { whats_new: [{ title: '23.5 item' }], behavior_changes: [], deprecated: [] } },
    { version: '21c', release_label: 'Oracle GoldenGate 21c', record_type: 'baseline', released: '2021-01-01', sections: { whats_new: [], behavior_changes: [], deprecated: [] } },
    { version: '19c', release_label: 'Oracle GoldenGate 19c', record_type: 'baseline', released: '2019-01-01', sections: { whats_new: [], behavior_changes: [], deprecated: [] } }
  ];

  assert.deepEqual(aggregateRange(records, '19c', '23.6').whats_new.map(i => i.title), ['23.5 item', '23.6 item']);
});
```

- [ ] **Step 5: Run JS tests**

Run:

```bash
npm test
```

Expected: PASS. Existing `aggregateRange()` should already satisfy this once default selection is updated.

## Task 3: Regenerate Data

**Files:**
- Modify: `data/index.json`
- Create: `data/oracle-goldengate/19c.json`
- Create: `data/oracle-goldengate/21c.json`
- Modify: existing `data/oracle-goldengate/*.json`

- [ ] **Step 1: Rebuild generated data**

Run:

```bash
.venv/bin/python -m pipeline.build
```

Expected: writes `19c.json`, `21c.json`, adds `record_type` to every record, and includes baselines in `data/index.json`.

- [ ] **Step 2: Validate generated data**

Run:

```bash
.venv/bin/python -c "import json, pathlib; from pipeline.validate import validate_record; [validate_record(json.loads(p.read_text())) for p in pathlib.Path('data/oracle-goldengate').glob('*.json')]; print('validated data records')"
```

Expected: prints `validated data records`.

## Task 4: Redwood Console UI

**Files:**
- Modify: `index.html`
- Replace/update: `css/theme.css`
- Modify: `js/render.js`
- Test: `tests/js/render.test.mjs`

- [ ] **Step 1: Write failing render test for record-type badge class**

Add this to `tests/js/render.test.mjs`:

```js
test('renderAggregated marks release badges for dark console styling', () => {
  const html = renderAggregated('whats_new', [
    {
      title: 'ConsoleFeature',
      description: 'visible in console',
      source_url: 'https://docs.oracle.com/c',
      introduced_label: 'Release 23.6',
      introduced_version: '23.6'
    }
  ]);

  assert.match(html, /item__badge/);
  assert.match(html, /Release 23\.6/);
});
```

- [ ] **Step 2: Run render tests**

Run:

```bash
node tests/js/render.test.mjs
```

Expected: PASS if existing badge rendering remains compatible.

- [ ] **Step 3: Update `index.html` structure**

Change the masthead subtitle to:

```html
<p class="masthead__subtitle">Oracle GoldenGate upgrade range intelligence</p>
```

Keep the same IDs: `older`, `newer`, `tabs`, `panels`, and `updated`.

- [ ] **Step 4: Replace light theme with dark Redwood Console CSS**

Update `:root` in `css/theme.css` to dark tokens:

```css
:root {
  --oracle-red: #C74634;
  --oracle-red-bright: #F06A59;
  --ink: #F5F2ED;
  --muted: #B8AEA6;
  --surface: #181514;
  --surface-2: #211D1B;
  --bg: #0F0D0C;
  --border: #3A302C;
  --focus: #F6B4AA;
}
```

Then restyle body, masthead, picker, tabs, cards, badges, and footer so the app reads as a compact dark console. Preserve all current class names used by HTML/JS.

- [ ] **Step 5: Mobile check**

Ensure selectors stack on narrow screens:

```css
@media (max-width: 700px) {
  .picker { grid-template-columns: 1fr; }
  .picker__vs { padding: 0; }
}
```

## Task 5: Docs and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/HANDOVER.md`
- Modify: `docs/superpowers/specs/2026-05-30-oracle-version-diff-design.md`

- [ ] **Step 1: Update docs**

Document:

- `19c`/`21c` are curated baseline records.
- The current UI is dark Redwood Console.
- The pipeline emits both baseline and release records.

- [ ] **Step 2: Run full verification**

Run:

```bash
.venv/bin/python -m pytest tests/python/ -q
npm test
git diff --check
```

Expected:

- Python tests pass.
- JS tests pass.
- `git diff --check` prints no whitespace errors.

- [ ] **Step 3: Local smoke test**

Run:

```bash
python3 -m http.server 8000
curl -sSf http://localhost:8000/
curl -sSf http://localhost:8000/data/index.json
```

Expected:

- `index.html` is served.
- `data/index.json` includes `19c`, `21c`, and latest `23.x`/`26ai` release entries.

---

## Self-Review

**Spec coverage:** Tasks cover curated baselines, schema metadata, baseline-to-modern aggregation, default selection, dark Redwood Console UI, docs, and verification.

**Placeholder scan:** No TBD/TODO placeholders. Legacy public-doc-backed baseline records are intentionally empty section baselines for this increment; full legacy parsing remains out of scope.

**Type consistency:** Uses `record_type` consistently in schema, record JSON, index entries, Python build code, and JS selection logic. Existing `released` and `order` continue to drive range ordering.
