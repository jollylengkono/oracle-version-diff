import json
from urllib.parse import urlparse

import pytest

from pipeline import build as build_module
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


def test_registered_product_ids_honors_explicit_empty_adapters():
    assert registered_product_ids([]) == set()


def test_build_all_products_honors_explicit_empty_adapters():
    assert build_all_products([], fetch=lambda url: "ok", today="2026-05-31") == []


def test_registry_check_honors_explicit_empty_registered_ids():
    index = {"products": [{"id": "oracle-goldengate"}]}

    with pytest.raises(AssertionError, match="oracle-goldengate"):
        ensure_data_products_registered(index, set())


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


def test_build_goldengate_product_preserves_explicit_falsy_fetch_and_today(monkeypatch):
    class FalsyFetch:
        def __call__(self, url):
            raise AssertionError(f"unexpected fetch call for {url}")

        def __bool__(self):
            return False

    falsy_fetch = FalsyFetch()
    calls = []

    def build_records(fetch, base_url, today=None):
        calls.append((fetch, base_url, today))
        return []

    monkeypatch.setattr(build_module, "build_records", build_records)

    product = build_module.build_goldengate_product(fetch=falsy_fetch, today="")

    assert product.records == []
    assert calls == [(falsy_fetch, build_module.sources_mod.RELEASE_NOTES_BASE, "")]


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
