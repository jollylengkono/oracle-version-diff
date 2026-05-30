from conftest import read_fixture
from pipeline.parse import parse_release_sections, release_version

SRC = "https://docs.oracle.com/x"


def test_release_version_extracts_parenthetical_and_plain():
    assert release_version("Release 26ai (23.26.1.0.0): January 2026") == "23.26.1.0.0"
    assert release_version("Release 23.10: January 2025") == "23.10"


def test_parse_release_sections_groups_items_by_release():
    rels = parse_release_sections(read_fixture("release_notes_sample.html"), source_url=SRC)
    assert [r["version"] for r in rels] == ["23.26.1.0.0", "23.10"]

    first = rels[0]
    assert first["label"].startswith("Release 26ai")
    assert [i["title"] for i in first["items"]] == [
        "Support for YugabyteDB",
        "Embedded AI Service Providers",
    ]
    assert first["items"][0]["source_url"] == SRC
    assert "YugabyteDB" in first["items"][0]["description"]

    # second release mixes a subhead2 item and a dlterm (deprecated-style) item
    t2 = [i["title"] for i in rels[1]["items"]]
    assert "Parallel Replicat improvements" in t2
    assert "Sybase ASE has been deprecated" in t2


def test_parse_release_sections_on_real_new_features_page():
    src = "https://docs.oracle.com/en/database/goldengate/core/26/release-notes/new-features.html"
    rels = parse_release_sections(read_fixture("real/new-features.html"), source_url=src)
    assert len(rels) >= 5
    all_titles = [i["title"] for r in rels for i in r["items"]]
    assert any("YugabyteDB" in t for t in all_titles)


def test_parse_release_sections_on_real_deprecated_page():
    src = "https://docs.oracle.com/en/database/goldengate/core/26/release-notes/deprecated-features.html"
    rels = parse_release_sections(read_fixture("real/deprecated-features.html"), source_url=src)
    assert len(rels) >= 1
    all_titles = [i["title"] for r in rels for i in r["items"]]
    assert any("Sybase" in t for t in all_titles)
