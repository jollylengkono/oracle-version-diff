import json

import pytest

from pipeline.ai_refresh import (
    AIRefreshError,
    candidate_source_urls,
    merge_candidate_versions,
    run_ai_refresh,
    validate_candidate_payload,
)


def _source_definition():
    return {
        "product": {"id": "oracle-database", "label": "Oracle Database"},
        "versions": [
            {
                "index": {"label": "Oracle AI Database 26ai", "support_track": "Long Term Support Release"},
                "record": {
                    "product": "oracle-database",
                    "version": "26ai",
                    "release_label": "Oracle AI Database 26ai",
                    "record_type": "release",
                    "released": "2026-01-01",
                    "sections": {
                        "certification": [],
                        "whats_new": [],
                        "behavior_changes": [],
                        "deprecated": [],
                        "desupported": [],
                    },
                },
            }
        ],
    }


def _candidate_payload(version="27ai", source_url="https://docs.oracle.com/database/27ai"):
    return {
        "product": "oracle-database",
        "versions": [
            {
                "index": {"label": f"Oracle Database {version}", "support_track": None},
                "record": {
                    "product": "oracle-database",
                    "version": version,
                    "release_label": f"Oracle Database {version}",
                    "record_type": "release",
                    "released": "2027-01-01",
                    "sections": {
                        "certification": [
                            {
                                "category": "JDK",
                                "value": "Java 21",
                                "source_url": "https://docs.oracle.com/database/certification",
                            }
                        ],
                        "whats_new": [
                            {
                                "title": "New feature",
                                "description": "A sourced feature.",
                                "source_url": source_url,
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


def test_candidate_source_urls_collects_section_urls():
    urls = candidate_source_urls(_candidate_payload()["versions"][0]["record"])

    assert urls == [
        "https://docs.oracle.com/database/27ai",
        "https://docs.oracle.com/database/certification",
    ]


def test_validate_candidate_payload_rejects_wrong_product():
    payload = _candidate_payload()
    payload["product"] = "oracle-weblogic-server"

    with pytest.raises(AIRefreshError, match="product"):
        validate_candidate_payload(payload, "oracle-database", today="2026-05-31")


def test_validate_candidate_payload_rejects_non_oracle_source_url():
    payload = _candidate_payload(source_url="https://example.com/not-oracle")

    with pytest.raises(AIRefreshError, match="non-Oracle"):
        validate_candidate_payload(payload, "oracle-database", today="2026-05-31")


def test_merge_candidate_versions_adds_new_versions_newest_first():
    merged = merge_candidate_versions(_source_definition(), _candidate_payload()["versions"], today="2026-05-31")

    assert [entry["record"]["version"] for entry in merged["versions"]] == ["27ai", "26ai"]
    assert "last_updated" not in merged["versions"][0]["record"]
    assert "support_track" not in merged["versions"][0]["index"]
    assert merged["versions"][1]["index"]["support_track"] == "Long Term Support Release"


def test_merge_candidate_versions_replaces_existing_version_preserving_existing_index_metadata():
    payload = _candidate_payload(version="26ai")
    merged = merge_candidate_versions(_source_definition(), payload["versions"], today="2026-05-31")

    assert [entry["record"]["version"] for entry in merged["versions"]] == ["26ai"]
    assert merged["versions"][0]["index"] == {
        "label": "Oracle AI Database 26ai",
        "support_track": "Long Term Support Release",
    }
    assert merged["versions"][0]["record"]["sections"]["whats_new"][0]["title"] == "New feature"


def test_run_ai_refresh_requires_openai_key_before_file_writes(tmp_path):
    source_path = tmp_path / "oracle-database.json"
    source_path.write_text(json.dumps(_source_definition()), encoding="utf-8")

    with pytest.raises(AIRefreshError, match="OPENAI_API_KEY"):
        run_ai_refresh(
            products=["oracle-database"],
            source_paths={"oracle-database": source_path},
            targets={"oracle-database": {"label": "Oracle Database", "seed_urls": ["https://docs.oracle.com/database"]}},
            env={},
            discover=lambda seed_urls: [],
            extract=lambda **kwargs: _candidate_payload(),
            today="2026-05-31",
        )

    assert json.loads(source_path.read_text(encoding="utf-8")) == _source_definition()


def test_run_ai_refresh_updates_curated_sources_not_data(tmp_path):
    source_path = tmp_path / "oracle-database.json"
    source_path.write_text(json.dumps(_source_definition()), encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    run_ai_refresh(
        products=["oracle-database"],
        source_paths={"oracle-database": source_path},
        targets={"oracle-database": {"label": "Oracle Database", "seed_urls": ["https://docs.oracle.com/database"]}},
        env={"OPENAI_API_KEY": "sk-test"},
        discover=lambda seed_urls: [],
        extract=lambda **kwargs: _candidate_payload(),
        today="2026-05-31",
    )

    updated = json.loads(source_path.read_text(encoding="utf-8"))
    assert [entry["record"]["version"] for entry in updated["versions"]] == ["27ai", "26ai"]
    assert list(data_dir.iterdir()) == []
