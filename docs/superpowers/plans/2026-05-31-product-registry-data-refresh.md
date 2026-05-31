# Product Registry Data Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the scheduled data refresh rebuild every included Oracle Release Delta product through a registered refresh adapter.

**Architecture:** Refactor the pipeline from a GoldenGate-only build into a product registry. GoldenGate keeps its crawler-backed adapter; Oracle Database and Oracle WebLogic Server get source-backed curated adapters whose source definitions live under `pipeline/curated_sources/`, are validated, and verify each referenced Oracle source URL during refresh. The all-product writer emits product JSON and a combined `data/index.json`; tests fail if checked-in data contains a product without a registered adapter.

**Tech Stack:** Python pipeline, JSON schema validation, pytest, GitHub Actions, static JSON frontend data.

---

## File Structure

- Create `pipeline/product_registry.py`: owns the product registry, adapter interface, registry/data consistency checks, and all-product build orchestration.
- Create `pipeline/curated.py`: builds source-backed curated products from JSON source definitions and verifies Oracle-owned source URLs are reachable.
- Create `pipeline/curated_sources/oracle-database.json`: source definitions for existing Oracle Database records.
- Create `pipeline/curated_sources/oracle-weblogic-server.json`: source definitions for existing Oracle WebLogic Server records.
- Modify `pipeline/build.py`: keep existing GoldenGate functions available for tests, add `build_goldengate_product()`, add `write_product_outputs()`, and make `main()` build all registered products.
- Modify `.github/workflows/refresh-data.yml`: rename workflow and PR copy from GoldenGate-only to all-product wording.
- Modify `README.md` and `docs/HANDOVER.md`: describe all-product periodic refresh and clarify Database/WebLogic are source-backed curated refresh adapters, not auto-discovery.
- Add/modify Python tests under `tests/python/`: cover registry completeness, curated source building, all-product output writing, and workflow naming.

## Task 1: Product Registry Contract

**Files:**
- Create: `tests/python/test_product_registry.py`
- Create: `pipeline/product_registry.py`
- Modify: `pipeline/build.py`

- [ ] **Step 1: Write failing registry tests**

Create `tests/python/test_product_registry.py`:

```python
import json
from urllib.parse import urlparse

import pytest

from pipeline.product_registry import (
    ProductAdapter,
    build_all_products,
    ensure_data_products_registered,
    registered_product_ids,
)


def _record(product, version):
    return {
        "product": product,
        "version": version,
        "release_label": f"{product} {version}",
        "record_type": "release",
        "released": "2026-01-01",
        "last_updated": "2026-05-31",
        "sections": {
            "certification": [],
            "whats_new": [],
            "behavior_changes": [],
            "deprecated": [],
            "desupported": [],
        },
    }


def test_registered_products_include_all_site_products(repo_root):
    index = json.loads((repo_root / "data" / "index.json").read_text())
    site_product_ids = {product["id"] for product in index["products"]}

    assert site_product_ids <= registered_product_ids()
    assert {"oracle-goldengate", "oracle-database", "oracle-weblogic-server"} <= registered_product_ids()


def test_registry_check_rejects_unregistered_data_product():
    index = {
        "products": [
            {"id": "oracle-goldengate", "label": "Oracle GoldenGate", "versions": []},
            {"id": "not-registered", "label": "Missing", "versions": []},
        ]
    }

    with pytest.raises(AssertionError, match="not-registered"):
        ensure_data_products_registered(index, {"oracle-goldengate"})


def test_build_all_products_runs_each_registered_adapter():
    calls = []

    def build_one(fetch, today):
        calls.append(("one", today))
        return [_record("one", "1")]

    def build_two(fetch, today):
        calls.append(("two", today))
        return [_record("two", "2")]

    adapters = [
        ProductAdapter("one", "One", build_one),
        ProductAdapter("two", "Two", build_two),
    ]

    products = build_all_products(adapters, fetch=lambda url: "ok", today="2026-05-31")

    assert [product.product_id for product in products] == ["one", "two"]
    assert [product.label for product in products] == ["One", "Two"]
    assert [product.records[0]["version"] for product in products] == ["1", "2"]
    assert calls == [("one", "2026-05-31"), ("two", "2026-05-31")]
```

- [ ] **Step 2: Run the registry tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/python/test_product_registry.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.product_registry'`.

- [ ] **Step 3: Implement the registry module**

Create `pipeline/product_registry.py`:

```python
from dataclasses import dataclass
from typing import Callable

from pipeline.validate import validate_record


@dataclass(frozen=True)
class ProductAdapter:
    product_id: str
    label: str
    build: Callable


@dataclass(frozen=True)
class ProductBuild:
    product_id: str
    label: str
    records: list[dict]
    index_metadata: dict[str, dict] | None = None


def registered_adapters():
    from pipeline import build
    from pipeline import curated

    return [
        ProductAdapter("oracle-goldengate", "Oracle GoldenGate", build.build_goldengate_product),
        ProductAdapter("oracle-database", "Oracle Database", curated.build_oracle_database_product),
        ProductAdapter("oracle-weblogic-server", "Oracle WebLogic Server", curated.build_oracle_weblogic_product),
    ]


def registered_product_ids(adapters=None):
    adapters = adapters or registered_adapters()
    return {adapter.product_id for adapter in adapters}


def ensure_data_products_registered(index, registered_ids=None):
    registered_ids = set(registered_ids or registered_product_ids())
    data_ids = {product["id"] for product in index.get("products", [])}
    missing = sorted(data_ids - registered_ids)
    if missing:
        raise AssertionError(f"Products missing refresh adapters: {', '.join(missing)}")


def build_all_products(adapters=None, fetch=None, today=None):
    adapters = adapters or registered_adapters()
    products = []
    for adapter in adapters:
        result = adapter.build(fetch=fetch, today=today)
        if isinstance(result, ProductBuild):
            product_build = result
        else:
            product_build = ProductBuild(adapter.product_id, adapter.label, result, {})
        if product_build.product_id != adapter.product_id:
            raise AssertionError(
                f"{adapter.product_id} adapter returned {product_build.product_id} product"
            )
        for record in product_build.records:
            if record["product"] != adapter.product_id:
                raise AssertionError(
                    f"{adapter.product_id} adapter returned {record['product']} record"
                )
            validate_record(record)
        products.append(product_build)
    return products
```

This imports `pipeline.curated`, which does not exist yet. That is acceptable until Task 2.

- [ ] **Step 4: Add the GoldenGate adapter entry point**

In `pipeline/build.py`, add these functions above `main()`:

```python
def today_iso():
    return datetime.date.today().isoformat()


def build_goldengate_product(fetch=None, today=None):
    from pipeline.product_registry import ProductBuild

    records = build_records(
        fetch or http_fetch,
        sources_mod.RELEASE_NOTES_BASE,
        today=today or today_iso(),
    )
    return ProductBuild(sources_mod.PRODUCT_ID, sources_mod.PRODUCT_LABEL, records, {})
```

- [ ] **Step 5: Run tests and commit**

```bash
.venv/bin/python -m pytest tests/python/test_product_registry.py::test_registry_check_rejects_unregistered_data_product tests/python/test_product_registry.py::test_build_all_products_runs_each_registered_adapter -q
git add tests/python/test_product_registry.py pipeline/product_registry.py pipeline/build.py
git commit -m "test: define product refresh registry contract"
```

Expected: the two targeted tests pass. The full new file may still fail on `registered_products_include_all_site_products` until Task 2 adds curated adapters.

## Task 2: Curated Product Source Adapter

**Files:**
- Create: `tests/python/test_curated_products.py`
- Create: `pipeline/curated.py`
- Create: `pipeline/curated_sources/oracle-database.json`
- Create: `pipeline/curated_sources/oracle-weblogic-server.json`

- [ ] **Step 1: Write failing curated adapter tests**

Create `tests/python/test_curated_products.py`:

```python
import json

import pytest

from pipeline.curated import (
    build_curated_product,
    build_oracle_database_product,
    build_oracle_weblogic_product,
    oracle_owned_host,
)


def _source_definition():
    return {
        "product": {"id": "oracle-test", "label": "Oracle Test"},
        "versions": [
            {
                "index": {"support_track": "Long Term Support Release"},
                "record": {
                    "product": "oracle-test",
                    "version": "1",
                    "release_label": "Oracle Test 1",
                    "record_type": "release",
                    "released": "2026-01-01",
                    "sections": {
                        "certification": [],
                        "whats_new": [
                            {
                                "title": "Feature",
                                "description": "From Oracle source",
                                "source_url": "https://docs.oracle.com/test",
                            }
                        ],
                        "behavior_changes": [],
                        "deprecated": [],
                        "desupported": [],
                    },
                },
            }
        ],
    }


def test_oracle_owned_host_accepts_oracle_domains_only():
    assert oracle_owned_host("https://oracle.com/a")
    assert oracle_owned_host("https://docs.oracle.com/a")
    assert not oracle_owned_host("https://example.com/a")


def test_build_curated_product_stamps_last_updated_and_verifies_urls():
    fetched = []

    def fetch(url):
        fetched.append(url)
        return "ok"

    product = build_curated_product(_source_definition(), fetch=fetch, today="2026-05-31")

    assert product.product_id == "oracle-test"
    assert product.label == "Oracle Test"
    assert product.records[0]["last_updated"] == "2026-05-31"
    assert product.records[0]["sections"]["whats_new"][0]["title"] == "Feature"
    assert product.index_metadata["1"]["support_track"] == "Long Term Support Release"
    assert fetched == ["https://docs.oracle.com/test"]


def test_build_curated_product_rejects_non_oracle_source_url():
    source = _source_definition()
    source["versions"][0]["record"]["sections"]["whats_new"][0]["source_url"] = "https://example.com/test"

    with pytest.raises(AssertionError, match="non-Oracle"):
        build_curated_product(source, fetch=lambda url: "ok", today="2026-05-31")


def test_database_and_weblogic_source_definitions_build_current_versions():
    database = build_oracle_database_product(fetch=lambda url: "ok", today="2026-05-31")
    weblogic = build_oracle_weblogic_product(fetch=lambda url: "ok", today="2026-05-31")

    assert database.product_id == "oracle-database"
    assert [record["version"] for record in database.records] == ["26ai", "21c", "19c", "12c"]
    assert weblogic.product_id == "oracle-weblogic-server"
    assert [record["version"] for record in weblogic.records] == ["15c", "14c", "12c", "11g"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/python/test_curated_products.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.curated'`.

- [ ] **Step 3: Create curated source JSON files from existing checked-in data**

Create `pipeline/curated_sources/oracle-database.json` and `pipeline/curated_sources/oracle-weblogic-server.json` by running this one-time export from the repository root:

```bash
.venv/bin/python - <<'PY'
import json
import pathlib

root = pathlib.Path(".")
index = json.loads((root / "data" / "index.json").read_text(encoding="utf-8"))


def product_index(product_id):
    for product in index["products"]:
        if product["id"] == product_id:
            return product
    raise AssertionError(f"missing product in data/index.json: {product_id}")


def support_metadata(product_id):
    product = product_index(product_id)
    metadata = {}
    for version in product["versions"]:
        entry = {}
        if "support_track" in version:
            entry["support_track"] = version["support_track"]
        metadata[version["version"]] = entry
    return metadata


def write_source(product_id, label, versions, output_name):
    metadata = support_metadata(product_id)
    entries = []
    for version in versions:
        record_path = root / "data" / product_id / f"{version}.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record.pop("last_updated", None)
        entries.append({"index": metadata.get(version, {}), "record": record})
    output_path = root / "pipeline" / "curated_sources" / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {"product": {"id": product_id, "label": label}, "versions": entries},
            indent=2,
        ),
        encoding="utf-8",
    )


write_source("oracle-database", "Oracle Database", ["26ai", "21c", "19c", "12c"], "oracle-database.json")
write_source(
    "oracle-weblogic-server",
    "Oracle WebLogic Server",
    ["15c", "14c", "12c", "11g"],
    "oracle-weblogic-server.json",
)
PY
```

Inspect the generated files:

```bash
.venv/bin/python -m json.tool pipeline/curated_sources/oracle-database.json > /tmp/oracle-database-curated.json
.venv/bin/python -m json.tool pipeline/curated_sources/oracle-weblogic-server.json > /tmp/oracle-weblogic-curated.json
! rg -n '"last_updated"' pipeline/curated_sources
```

Expected: both `json.tool` commands succeed and `rg` returns no matches. The generated files preserve every section item and every Oracle-owned `source_url`; they preserve existing `support_track` values from `data/index.json` in each `index` object where present and use `{}` for versions without support-track metadata.

- [ ] **Step 4: Implement curated adapter**

Create `pipeline/curated.py`:

```python
import copy
import json
import pathlib
from urllib.parse import urlparse

from pipeline.product_registry import ProductBuild
from pipeline.validate import validate_record

CURATED_SOURCE_DIR = pathlib.Path(__file__).resolve().parent / "curated_sources"


def oracle_owned_host(url):
    host = urlparse(url).hostname or ""
    return host == "oracle.com" or host.endswith(".oracle.com")


def _record_source_urls(record):
    urls = set()
    for items in record["sections"].values():
        for item in items:
            source_url = item.get("source_url")
            if source_url:
                urls.add(source_url)
    return sorted(urls)


def _verify_source_urls(record, fetch):
    for source_url in _record_source_urls(record):
        if not oracle_owned_host(source_url):
            raise AssertionError(f"non-Oracle source URL in {record['product']} {record['version']}: {source_url}")
        fetch(source_url)


def load_source_definition(filename):
    path = CURATED_SOURCE_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


def build_curated_product(source_definition, fetch, today):
    if fetch is None:
        from pipeline.build import http_fetch
        fetch = http_fetch
    records = []
    index_metadata = {}
    product = source_definition["product"]
    for version_entry in source_definition["versions"]:
        record = copy.deepcopy(version_entry["record"])
        record["last_updated"] = today
        _verify_source_urls(record, fetch)
        validate_record(record)
        records.append(record)
        index_metadata[record["version"]] = dict(version_entry.get("index", {}))
    return ProductBuild(product["id"], product["label"], records, index_metadata)


def build_oracle_database_product(fetch=None, today=None):
    from pipeline.build import today_iso
    return build_curated_product(
        load_source_definition("oracle-database.json"),
        fetch=fetch,
        today=today or today_iso(),
    )


def build_oracle_weblogic_product(fetch=None, today=None):
    from pipeline.build import today_iso
    return build_curated_product(
        load_source_definition("oracle-weblogic-server.json"),
        fetch=fetch,
        today=today or today_iso(),
    )
```

- [ ] **Step 5: Run tests and commit**

```bash
.venv/bin/python -m pytest tests/python/test_curated_products.py tests/python/test_product_registry.py -q
git add tests/python/test_curated_products.py pipeline/curated.py pipeline/curated_sources
git commit -m "feat: add curated product refresh adapters"
```

Expected: tests pass, including the registry completeness test that now finds all three product adapters.

## Task 3: All-Product Build And Combined Index

**Files:**
- Modify: `pipeline/product_registry.py`
- Modify: `pipeline/build.py`
- Modify: `tests/python/test_product_registry.py`
- Create: `tests/python/test_all_product_build.py`

- [ ] **Step 1: Write failing all-product build tests**

Create `tests/python/test_all_product_build.py`:

```python
import json

from pipeline.build import write_all_product_outputs
from pipeline.product_registry import ProductBuild


def _record(product, version, released):
    return {
        "product": product,
        "version": version,
        "release_label": f"{product} {version}",
        "record_type": "release",
        "released": released,
        "last_updated": "2026-05-31",
        "sections": {
            "certification": [],
            "whats_new": [],
            "behavior_changes": [],
            "deprecated": [],
            "desupported": [],
        },
    }


def test_write_all_product_outputs_writes_combined_index(tmp_path):
    products = [
        ProductBuild(
            "one",
            "One",
            [_record("one", "2", "2026-01-01"), _record("one", "1", "2025-01-01")],
            {"2": {"support_track": "LTS"}, "1": {}},
        ),
        ProductBuild("two", "Two", [_record("two", "a", "2024-01-01")], {}),
    ]

    write_all_product_outputs(products, tmp_path)

    assert (tmp_path / "one" / "2.json").exists()
    assert (tmp_path / "two" / "a.json").exists()

    index = json.loads((tmp_path / "index.json").read_text())
    assert [product["id"] for product in index["products"]] == ["one", "two"]
    one_versions = index["products"][0]["versions"]
    assert [version["version"] for version in one_versions] == ["2", "1"]
    assert one_versions[0]["order"] == 2
    assert one_versions[1]["order"] == 1
    assert one_versions[0]["support_track"] == "LTS"
    assert one_versions[0]["file"] == "one/2.json"
```

Add this test to `tests/python/test_product_registry.py`:

```python
def _registered_fetch(url):
    release_page = """
    <html><body>
      <h3 class="sect3">Release 23.26.2.0.0: May 2026</h3>
      <p class="subhead2">Generated test item</p>
      <p>Generated test description.</p>
    </body></html>
    """
    if url.endswith("toc.js"):
        return json.dumps({
            "toc": [{
                "topics": [
                    {"title": "New Features", "href": "new-features.html"},
                    {"title": "Default Behavior Changes", "href": "default-behaviour.html"},
                    {"title": "Deprecated and Desupported", "href": "deprecated-features.html"},
                ]
            }]
        })
    host = urlparse(url).hostname or ""
    if host == "oracle.com" or host.endswith(".oracle.com"):
        return release_page
    raise AssertionError(f"unexpected URL: {url}")


def test_registered_products_build_against_fake_fetch():
    products = build_all_products(fetch=_registered_fetch, today="2026-05-31")

    assert {product.product_id for product in products} == {
        "oracle-goldengate",
        "oracle-database",
        "oracle-weblogic-server",
    }
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/python/test_all_product_build.py tests/python/test_product_registry.py -q
```

Expected: FAIL because `write_all_product_outputs` does not exist.

- [ ] **Step 3: Add the all-product writer**

In `pipeline/build.py`, add:

```python
def _index_entry(product_id, order, record, metadata):
    entry = {
        "version": record["version"],
        "label": record["version"],
        "order": order,
        "record_type": record["record_type"],
        "released": record["released"],
        "file": f"{product_id}/{record['version']}.json",
    }
    entry.update(metadata)
    return entry


def write_all_product_outputs(products, data_dir):
    data_dir = pathlib.Path(data_dir)
    index_products = []
    for product in products:
        product_dir = data_dir / product.product_id
        product_dir.mkdir(parents=True, exist_ok=True)
        records = sorted(product.records, key=lambda r: r["released"], reverse=True)
        n = len(records)
        versions_index = []
        metadata_by_version = product.index_metadata or {}
        for pos, record in enumerate(records):
            fname = f"{record['version']}.json"
            (product_dir / fname).write_text(json.dumps(record, indent=2), encoding="utf-8")
            versions_index.append(
                _index_entry(product.product_id, n - pos, record, metadata_by_version.get(record["version"], {}))
            )
        index_products.append({
            "id": product.product_id,
            "label": product.label,
            "versions": versions_index,
        })
    (data_dir / "index.json").write_text(json.dumps({"products": index_products}, indent=2), encoding="utf-8")
```

Change `main()`:

```python
def main():
    from pipeline.product_registry import build_all_products

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    products = build_all_products(fetch=http_fetch, today=today_iso())
    write_all_product_outputs(products, repo_root / "data")
```

Keep existing `build_records()`, `write_release_outputs()`, `build_record()`, and `write_outputs()` for compatibility with current tests.

- [ ] **Step 4: Run tests and commit**

```bash
.venv/bin/python -m pytest tests/python/test_all_product_build.py tests/python/test_product_registry.py tests/python/test_curated_products.py tests/python/test_release_build.py tests/python/test_build.py -q
git add pipeline/product_registry.py pipeline/build.py tests/python/test_all_product_build.py tests/python/test_product_registry.py
git commit -m "feat: build registered products"
```

Expected: tests pass.

## Task 4: Workflow And Documentation

**Files:**
- Modify: `.github/workflows/refresh-data.yml`
- Modify: `README.md`
- Modify: `docs/HANDOVER.md`
- Create: `tests/python/test_refresh_workflow.py`

- [ ] **Step 1: Write workflow/docs tests**

Create `tests/python/test_refresh_workflow.py`:

```python
from pathlib import Path


def test_refresh_workflow_uses_all_product_copy(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "refresh-data.yml").read_text()

    assert "name: Refresh Oracle Release Delta data" in workflow
    assert "data: refresh Oracle Release Delta data" in workflow
    assert "Data refresh: Oracle Release Delta" in workflow
    assert "GoldenGate comparison" not in workflow
    assert "python -m pipeline.build" in workflow


def test_docs_describe_all_product_periodic_refresh(repo_root):
    readme = (repo_root / "README.md").read_text()
    handover = (repo_root / "docs" / "HANDOVER.md").read_text()

    assert "all registered products" in readme
    assert "Database and WebLogic" in readme
    assert "all registered products" in handover
    assert "not yet crawler-backed" not in readme
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/python/test_refresh_workflow.py -q
```

Expected: FAIL because workflow and docs still say GoldenGate-specific refresh.

- [ ] **Step 3: Update workflow copy**

Edit `.github/workflows/refresh-data.yml`:

```yaml
name: Refresh Oracle Release Delta data
```

Change PR step:

```yaml
      - name: Open pull request with refreshed data
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "data: refresh Oracle Release Delta data"
          branch: data/refresh
          title: "Data refresh: Oracle Release Delta"
          body: |
            Automated refresh of Oracle Release Delta data from Oracle-owned sources.
            Review the diff before merging; parser drift or source drift will show up here.
          labels: data-refresh
```

Keep the schedule, manual trigger, permissions, tests, and `python -m pipeline.build` step.

- [ ] **Step 4: Update README and handover**

In `README.md`, change the Pipeline/Product/Updating data sections to say:

```markdown
- **Pipeline** (`pipeline/`): a product-registry data refresh run weekly by GitHub Actions.
  GoldenGate is crawler-backed. Oracle Database and Oracle WebLogic Server are
  source-backed curated adapters: their release records are regenerated from
  maintained Oracle-owned source definitions, source URLs are checked during
  refresh, records are schema-validated, and the workflow opens a pull request
  with the refreshed `data/` JSON for human review.
```

In `README.md` `Updating data`, replace the GoldenGate-only paragraph with:

```markdown
The `Refresh Oracle Release Delta data` workflow runs weekly (and on demand via
"Run workflow"). It rebuilds all registered products and opens a PR; review the
diff and merge. A product must have a refresh adapter before it can be included
in `data/index.json`.
```

In `docs/HANDOVER.md`, update the current-state bullets:

```markdown
- Python pipeline (`pipeline/`): product-registry refresh. GoldenGate is crawler-backed
  from Oracle release notes; Oracle Database and Oracle WebLogic Server are
  source-backed curated adapters regenerated from maintained Oracle-owned source
  definitions.
- GitHub Action `.github/workflows/refresh-data.yml`: weekly (Mon 06:00 UTC) +
  manual; runs pytest, `python -m pipeline.build`, refreshes all registered
  products, and opens a review PR.
- Oracle Database and Oracle WebLogic Server are not auto-discovered yet; adding
  a new release requires updating their curated source definitions.
```

- [ ] **Step 5: Run tests and commit**

```bash
.venv/bin/python -m pytest tests/python/test_refresh_workflow.py -q
git add .github/workflows/refresh-data.yml README.md docs/HANDOVER.md tests/python/test_refresh_workflow.py
git commit -m "docs: describe all-product data refresh"
```

Expected: tests pass.

## Task 5: Regenerate Data And Final Verification

**Files:**
- Modify generated data under `data/`
- Verify all pipeline and frontend tests

- [ ] **Step 1: Run the all-product build**

```bash
.venv/bin/python -m pipeline.build
```

Expected:

- `data/index.json` includes `oracle-goldengate`, `oracle-database`, and `oracle-weblogic-server`.
- Database/WebLogic records have refreshed `last_updated` values.
- No non-Oracle source URL is accepted.

- [ ] **Step 2: Validate generated data**

```bash
.venv/bin/python - <<'PY'
import json
import pathlib
from pipeline.validate import validate_record

for path in pathlib.Path("data").glob("*/*.json"):
    validate_record(json.loads(path.read_text()))
print("validated data records")
PY
```

Expected: `validated data records`.

- [ ] **Step 3: Run full test suites**

```bash
npm test
.venv/bin/python -m pytest tests/python/ -q
```

Expected: all JS tests pass and all Python tests pass.

- [ ] **Step 4: Check generated product coverage**

```bash
.venv/bin/python - <<'PY'
import json
index = json.load(open("data/index.json"))
print([product["id"] for product in index["products"]])
PY
```

Expected:

```text
['oracle-goldengate', 'oracle-database', 'oracle-weblogic-server']
```

- [ ] **Step 5: Check whitespace and changed files**

```bash
git diff --check
git status --short
```

Expected: `git diff --check` has no output. `git status --short` shows only planned pipeline, workflow, docs, tests, curated source definitions, and generated data changes.

- [ ] **Step 6: Commit regenerated data and final integration**

```bash
git add pipeline tests/python .github/workflows/refresh-data.yml README.md docs/HANDOVER.md data
git commit -m "feat: refresh all registered products"
```

Expected: commit succeeds.
