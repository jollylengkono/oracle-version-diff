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
