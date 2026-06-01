from conftest import read_fixture
from pipeline.build import resolve_section_urls, build_records

BASE = "https://docs.oracle.com/en/database/goldengate/core/26/release-notes/"

LEGACY_19C_NEW_FEATURES = """
<article>
  <h2 class="sect2">New Features</h2>
  <h3 class="sect3">Release 19c (19.1.0) - May 2019 Initial Release</h3>
  <dl>
    <dt class="dlterm">Target-Initiated Paths</dt>
    <dd><p>Target-initiated paths for microservices enable the Receiver Server to initiate a path.</p></dd>
  </dl>
</article>
"""

LEGACY_19C_BEHAVIOR = """
<article>
  <h2 class="sect2">Default Behavior Changes</h2>
  <h3 class="sect3">Release 19c (19.1.0) - May 2019 Initial Release</h3>
  <dl>
    <dt class="dlterm">Extract Default Trail File Version</dt>
    <dd><p>The primary Extract writes trail file in the same format as the existing trail file format.</p></dd>
  </dl>
</article>
"""

LEGACY_19C_DEPRECATED = """
<article>
  <h2 class="sect2">Deprecated and Desupported Features and Parameters</h2>
  <h3 class="sect3">Release 19c (19.1.0) - September 2019</h3>
  <dl>
    <dt class="dlterm">Classic Extract for SQL Server</dt>
    <dd><p>Classic Extract is desupported for SQL Server.</p></dd>
  </dl>
</article>
"""

LEGACY_12C_WHATS_NEW = """
<article>
  <h2 class="sect2">What’s New in this Release</h2>
  <h3 class="sect3">New Features</h3>
  <h4 class="sect4">Release 12.3.0.1.181228 - February 2019</h4>
  <dl>
    <dt class="dlterm">Microsoft Azure SQL Database Support</dt>
    <dd><p>Oracle GoldenGate now supports delivery to Microsoft Azure SQL Database targets.</p></dd>
    <dt class="dlterm">SQL Server</dt>
    <dd>
      <dl>
        <dt class="dlterm">SQL Server 2017 Support</dt>
        <dd><p>Oracle GoldenGate now supports SQL Server 2017 Enterprise edition.</p></dd>
        <dt class="dlterm"></dt>
        <dd><p>This blank nested term should not become a data item.</p></dd>
      </dl>
    </dd>
  </dl>
  <h3 class="sect3">Default Behavior Changes</h3>
  <h4 class="sect4">Release 12.3.0.1.0 - August 2017 Initial Release</h4>
  <dl>
    <dt class="dlterm">System Change Number</dt>
    <dd><p>The value size is expanded from 6 bytes to 8 bytes.</p></dd>
  </dl>
  <h3 class="sect3">Deprecated Features</h3>
  <h4 class="sect4">Release 12.3.0.1.0 - August 2017 Initial Release</h4>
  <dl>
    <dt class="dlterm">Oracle GoldenGate Director</dt>
    <dd><p>Oracle GoldenGate Director is not supported with Oracle GoldenGate 12.3.0.1 release.</p></dd>
  </dl>
</article>
"""


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
        if "19.1/release-notes/new-features.html" in url:
            return LEGACY_19C_NEW_FEATURES
        if "19.1/release-notes/default-behavior-changes.html" in url:
            return LEGACY_19C_BEHAVIOR
        if "19.1/release-notes/deprecated-features.html" in url:
            return LEGACY_19C_DEPRECATED
        if "12.3.0.1/oggrn/whats-new-this-release.html" in url:
            return LEGACY_12C_WHATS_NEW
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


def test_build_records_omits_release_records_without_section_items():
    toc = """
    define({"toc":[{"topics":[
      {"title":"New Features","href":"new-features.html"},
      {"title":"Default Behavior Changes","href":"default-behavior-changes.html"},
      {"title":"Deprecated and Desupported","href":"deprecated-features.html"}
    ]}]});
    """
    empty_release_page = """
    <article>
      <h2 class="sect2">New Features</h2>
      <h3 class="sect3">Release 99.1: January 2099</h3>
      <p>No extracted release-delta items are present.</p>
    </article>
    """

    def fetch(url):
        if url.endswith("toc.js"):
            return toc
        if "21.3/release-notes/release-21." in url or "21.3/release-notes/oggcore-new-features" in url:
            return LEGACY_19C_NEW_FEATURES
        if "21.3/release-notes/default-behavior-changes.html" in url:
            return LEGACY_19C_BEHAVIOR
        if "21.3/release-notes/deprecated-features.html" in url:
            return LEGACY_19C_DEPRECATED
        if "19.1/release-notes/new-features.html" in url:
            return LEGACY_19C_NEW_FEATURES
        if "19.1/release-notes/default-behavior-changes.html" in url:
            return LEGACY_19C_BEHAVIOR
        if "19.1/release-notes/deprecated-features.html" in url:
            return LEGACY_19C_DEPRECATED
        if "12.3.0.1/oggrn/whats-new-this-release.html" in url:
            return LEGACY_12C_WHATS_NEW
        return empty_release_page

    recs = build_records(fetch, BASE, today="2026-05-30")

    assert "99.1" not in [r["version"] for r in recs]


def test_build_records_sorts_by_released_descending_and_keeps_patch_releases_distinct():
    recs = build_records(fake_fetch_factory(), BASE, today="2026-05-30")
    released = [r["released"] for r in recs]
    assert released == sorted(released, reverse=True)

    versions = [r["version"] for r in recs]
    assert versions.index("23.7.1.25.02") < versions.index("23.7.0.25.01")


def test_build_records_includes_curated_legacy_baselines():
    recs = build_records(fake_fetch_factory(), BASE, today="2026-05-30")
    versions = [r["version"] for r in recs]

    assert versions[-3:] == ["21c", "19c", "12c"]
    assert next(r for r in recs if r["version"] == "12c")["record_type"] == "baseline"
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


def test_build_records_populates_19c_from_oracle_release_note_sources():
    recs = build_records(fake_fetch_factory(), BASE, today="2026-05-30")
    baseline = next(r for r in recs if r["version"] == "19c")

    assert baseline["sections"]["whats_new"][0]["title"] == "Target-Initiated Paths"
    assert baseline["sections"]["behavior_changes"][0]["title"] == "Extract Default Trail File Version"
    assert baseline["sections"]["deprecated"][0]["title"] == "Classic Extract for SQL Server"
    assert baseline["sections"]["whats_new"][0]["source_url"].endswith(
        "/19.1/release-notes/new-features.html"
    )
    assert all(item["title"] for item in baseline["sections"]["whats_new"])


def test_build_records_populates_12c_grouped_release_note_sections():
    recs = build_records(fake_fetch_factory(), BASE, today="2026-05-30")
    baseline = next(r for r in recs if r["version"] == "12c")

    assert baseline["sections"]["whats_new"][0]["title"] == "Microsoft Azure SQL Database Support"
    assert baseline["sections"]["behavior_changes"][0]["title"] == "System Change Number"
    assert baseline["sections"]["deprecated"][0]["title"] == "Oracle GoldenGate Director"
    assert baseline["sections"]["deprecated"][0]["source_url"].endswith(
        "/12.3.0.1/oggrn/whats-new-this-release.html"
    )
    assert "SQL Server" not in [item["title"] for item in baseline["sections"]["whats_new"]]
    assert all(item["title"] for item in baseline["sections"]["whats_new"])
