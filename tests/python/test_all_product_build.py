import json

import pytest

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


def test_write_all_product_outputs_preserves_label_metadata(tmp_path):
    products = [
        ProductBuild(
            "one",
            "One",
            [_record("one", "2", "2026-01-01")],
            {"2": {"label": "Version Two", "support_track": "LTS"}},
        )
    ]

    write_all_product_outputs(products, tmp_path)

    index = json.loads((tmp_path / "index.json").read_text())
    version = index["products"][0]["versions"][0]
    assert version["label"] == "Version Two"
    assert version["support_track"] == "LTS"
    assert version["file"] == "one/2.json"


@pytest.mark.parametrize("metadata", [{"file": "bad.json"}, {"unknown": "x"}])
def test_write_all_product_outputs_rejects_unsafe_metadata_keys(tmp_path, metadata):
    products = [
        ProductBuild(
            "one",
            "One",
            [_record("one", "2", "2026-01-01")],
            {"2": metadata},
        )
    ]

    offending_key = next(iter(metadata))
    with pytest.raises(AssertionError, match=offending_key):
        write_all_product_outputs(products, tmp_path)
