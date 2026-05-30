from conftest import read_fixture
from pipeline.build import resolve_section_urls, build_records

BASE = "https://docs.oracle.com/en/database/goldengate/core/26/release-notes/"


def fake_fetch_factory():
    toc = read_fixture("real/toc.js")
    pages = {
        "new-features.html": read_fixture("real/new-features.html"),
        "default-behaviour-updates-23ai.html": read_fixture("real/default-behaviour.html"),
        "deprecated-features.html": read_fixture("real/deprecated-features.html"),
        "21c-new-features.html": read_fixture("release_notes_sample.html"),
        "21c-default-behavior-changes.html": read_fixture("release_notes_sample.html"),
        "21c-deprecated-features.html": read_fixture("release_notes_sample.html"),
    }

    def fetch(url):
        if url.endswith("toc.js"):
            return toc
        if "21.3/release-notes/release-21." in url or "21.3/release-notes/oggcore-new-features" in url:
            return pages["21c-new-features.html"]
        if "21.3/release-notes/default-behavior-changes.html" in url:
            return pages["21c-default-behavior-changes.html"]
        if "21.3/release-notes/deprecated-features.html" in url:
            return pages["21c-deprecated-features.html"]
        for name, html in pages.items():
            if name in url:
                return html
        raise AssertionError(f"unexpected url {url}")

    return fetch


def test_resolve_section_urls_from_toc():
    urls = resolve_section_urls(read_fixture("real/toc.js"), BASE)
    assert "new-features.html" in urls["whats_new"]
    assert "default-behaviour" in urls["behavior_changes"].lower()
    assert "deprecated-features.html" in urls["deprecated"]


def test_build_records_merges_sections_per_release():
    recs = build_records(fake_fetch_factory(), BASE, today="2026-05-30")
    assert len(recs) >= 5

    top = recs[0]
    assert top["product"] == "oracle-goldengate"
    assert top["version"].startswith("23.")
    assert top["last_updated"] == "2026-05-30"
    assert top["release_label"].startswith("Release")

    record_with_new_features = next(r for r in recs if r["sections"]["whats_new"])
    wn_titles = [i["title"] for i in record_with_new_features["sections"]["whats_new"]]
    assert any("YugabyteDB" in t for t in wn_titles)

    # at least one release carries deprecated content from the deprecated page
    assert any(r["sections"]["deprecated"] for r in recs)
    # records validate against the schema (build_records validates internally)


def test_build_records_sorts_by_released_descending_and_keeps_patch_releases_distinct():
    recs = build_records(fake_fetch_factory(), BASE, today="2026-05-30")
    released = [r["released"] for r in recs]
    assert released == sorted(released, reverse=True)

    versions = [r["version"] for r in recs]
    assert versions.index("23.7.1.25.02") < versions.index("23.7.0.25.01")


def test_build_records_includes_curated_legacy_baselines():
    recs = build_records(fake_fetch_factory(), BASE, today="2026-05-30")
    versions = [r["version"] for r in recs]

    assert versions[-2:] == ["21c", "19c"]
    assert next(r for r in recs if r["version"] == "19c")["record_type"] == "baseline"
    assert next(r for r in recs if r["version"] == "23.26.2.0.0")["record_type"] == "release"


def test_build_records_includes_21c_baseline_items_for_dynamic_compare():
    recs = build_records(fake_fetch_factory(), BASE, today="2026-05-30")
    baseline = next(r for r in recs if r["version"] == "21c")

    assert baseline["sections"]["whats_new"]
    assert baseline["sections"]["whats_new"][0]["source_url"].startswith("https://docs.oracle.com/")


def test_build_records_populates_21c_behavior_and_deprecated_sections():
    recs = build_records(fake_fetch_factory(), BASE, today="2026-05-30")
    baseline = next(r for r in recs if r["version"] == "21c")

    assert baseline["sections"]["behavior_changes"]
    assert baseline["sections"]["deprecated"]
    assert baseline["sections"]["behavior_changes"][0]["source_url"].endswith(
        "/21.3/release-notes/default-behavior-changes.html"
    )
    assert baseline["sections"]["deprecated"][0]["source_url"].endswith(
        "/21.3/release-notes/deprecated-features.html"
    )
