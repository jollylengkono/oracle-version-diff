from conftest import read_fixture
from pipeline.build import resolve_section_urls, build_records

BASE = "https://docs.oracle.com/en/database/goldengate/core/26/release-notes/"


def fake_fetch_factory():
    toc = read_fixture("real/toc.js")
    pages = {
        "new-features.html": read_fixture("real/new-features.html"),
        "default-behaviour-updates-23ai.html": read_fixture("real/default-behaviour.html"),
        "deprecated-features.html": read_fixture("real/deprecated-features.html"),
    }

    def fetch(url):
        if url.endswith("toc.js"):
            return toc
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

    wn_titles = [i["title"] for i in top["sections"]["whats_new"]]
    assert any("YugabyteDB" in t for t in wn_titles)

    # at least one release carries deprecated content from the deprecated page
    assert any(r["sections"]["deprecated"] for r in recs)
    # records validate against the schema (build_records validates internally)
